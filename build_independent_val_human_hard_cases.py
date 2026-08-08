"""Add independently sourced, edited human photos to dataset/val/hum.

This creates 185 *new* validation files from previously unused, MIT-licensed
human-labelled photos in Parveshiiii/AI-vs-Real.  The source rows already used
for the training split are excluded.  Each source image receives one visual
edit, then only the edited result is saved in the validation folder.
"""

from __future__ import annotations

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

from create_validation_human_hard_cases import RENDERERS, VARIANTS


PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "dataset"
DESTINATION_DIR = DATASET_DIR / "val" / "hum"
ACQUISITION_MANIFEST = DATASET_DIR / "acquisition_manifest.jsonl"
MANIFEST_PATH = DATASET_DIR / "independent_val_human_hard_cases_manifest.jsonl"
DATASET_ID = "Parveshiiii/AI-vs-Real"
ROWS_API = "https://datasets-server.huggingface.co/rows"
TARGET_COUNT = 185
RANDOM_SEED = 20260801
PAGE_SIZE = 100
REQUEST_TIMEOUT = 20
WORKERS = 8


def existing_source_rows() -> set[int]:
    rows: set[int] = set()
    for path in (ACQUISITION_MANIFEST, MANIFEST_PATH):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record.get("source_row"), int):
                rows.add(record["source_row"])
    return rows


def request_json(session: requests.Session, params: dict) -> dict:
    for attempt in range(3):
        try:
            response = session.get(ROWS_API, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            if attempt == 2:
                raise RuntimeError(f"The public source could not be queried: {error}") from error
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def collect_candidates(excluded: set[int], needed: int) -> list[dict]:
    session = requests.Session()
    session.headers["User-Agent"] = "reAlIty-validation-data-builder/1.0"
    first = request_json(session, {"dataset": DATASET_ID, "config": "default", "split": "train", "offset": 0, "length": 1})
    total_rows = int(first["num_rows_total"])
    max_block = max(1, (total_rows - 1) // PAGE_SIZE)
    blocks = list(range(max_block + 1))
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(blocks)
    selected: list[dict] = []
    seen = set(excluded)

    # Stop as soon as there is a reserve for failed image downloads.  This is
    # much gentler on the public preview service than scanning the whole corpus.
    for block in blocks:
        page = request_json(session, {
            "dataset": DATASET_ID,
            "config": "default",
            "split": "train",
            "offset": block * PAGE_SIZE,
            "length": PAGE_SIZE,
        })
        for item in page.get("rows", []):
            row_id = int(item["row_idx"])
            row = item["row"]
            image_url = (row.get("image") or {}).get("src")
            if row_id in seen or row.get("binary_label") != 1 or not image_url:
                continue
            seen.add(row_id)
            selected.append({"source_row": row_id, "image_url": image_url})
        if len(selected) >= needed + 45:
            break

    if len(selected) < needed:
        raise RuntimeError(f"Only found {len(selected)} unused human-labelled source rows; need {needed}.")
    rng.shuffle(selected)
    return selected


def download(candidate: dict) -> tuple[dict, Image.Image | None]:
    try:
        response = requests.get(candidate["image_url"], timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            return candidate, image.convert("RGB").copy()
    except (requests.RequestException, UnidentifiedImageError, OSError, ValueError):
        return candidate, None


def main() -> None:
    existing_records = []
    if MANIFEST_PATH.exists():
        existing_records = [json.loads(line) for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines() if line]
    remaining = TARGET_COUNT - len(existing_records)
    if remaining <= 0:
        print("All 185 independent validation hard cases are already present; no files were changed.")
        return

    candidates = collect_candidates(existing_source_rows(), remaining)
    rng = random.Random(RANDOM_SEED + len(existing_records))
    variants = [VARIANTS[index % len(VARIANTS)] for index in range(remaining)]
    rng.shuffle(variants)
    saved = 0
    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for start in range(0, len(candidates), 24):
            if saved >= remaining:
                break
            batch = candidates[start:start + 24]
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = [executor.submit(download, candidate) for candidate in batch]
                for future in as_completed(futures):
                    candidate, image = future.result()
                    if image is None or saved >= remaining:
                        continue
                    # Use a second distinct source image only for collage layouts.
                    second_candidate = rng.choice(candidates)
                    _, second = download(second_candidate)
                    if second is None:
                        second = image.copy()
                    variant = variants[saved]
                    output = RENDERERS[variant](image, second, rng)
                    number = len(existing_records) + saved + 1
                    filename = f"independent_val_hum_{number:03d}_{variant}.jpg"
                    path = DESTINATION_DIR / filename
                    temporary = DESTINATION_DIR / f".{filename}.tmp.jpg"
                    output.save(temporary, format="JPEG", quality=92, optimize=True)
                    temporary.replace(path)
                    manifest.write(json.dumps({
                        "created_by": "build_independent_val_human_hard_cases.py",
                        "dataset": DATASET_ID,
                        "source_license": "mit",
                        "source_row": candidate["source_row"],
                        "label": "hum",
                        "split": "val",
                        "file": f"val/hum/{filename}",
                        "variant": variant,
                    }) + "\n")
                    manifest.flush()
                    saved += 1
                    if saved % 25 == 0 or saved == remaining:
                        print(f"Saved {saved}/{remaining} independent human validation hard cases")

    if saved != remaining:
        raise RuntimeError(f"Saved {saved}/{remaining}. Re-run the script to resume safely.")
    print("Done. Every added image has a new source row and recorded provenance.")


if __name__ == "__main__":
    main()
