"""Add 180 independently sourced, edited AI images to dataset/val/ai.

The source dataset's documented binary label 0 means AI-generated. Every
source row used here is excluded if it was recorded anywhere in the existing
training or validation acquisition manifests.
"""

from __future__ import annotations

import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from create_validation_human_hard_cases import RENDERERS, VARIANTS
from build_independent_val_human_hard_cases import (
    DATASET_ID,
    DATASET_DIR,
    PAGE_SIZE,
    REQUEST_TIMEOUT,
    ROWS_API,
    WORKERS,
    download,
    existing_source_rows,
    request_json,
)


DESTINATION_DIR = DATASET_DIR / "val" / "ai"
MANIFEST_PATH = DATASET_DIR / "independent_val_ai_hard_cases_manifest.jsonl"
TARGET_COUNT = 180
RANDOM_SEED = 20260802


def read_existing() -> tuple[list[dict], set[int]]:
    if not MANIFEST_PATH.exists():
        return [], set()
    records = [json.loads(line) for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines() if line]
    return records, {record["source_row"] for record in records if isinstance(record.get("source_row"), int)}


def collect_ai_candidates(excluded: set[int], needed: int) -> list[dict]:
    import requests

    session = requests.Session()
    session.headers["User-Agent"] = "reAlIty-validation-data-builder/1.0"
    first = request_json(session, {"dataset": DATASET_ID, "config": "default", "split": "train", "offset": 0, "length": 1})
    total_rows = int(first["num_rows_total"])
    blocks = list(range(max(1, (total_rows - 1) // PAGE_SIZE) + 1))
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(blocks)
    seen, selected = set(excluded), []

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
            url = (row.get("image") or {}).get("src")
            if row_id in seen or row.get("binary_label") != 0 or not url:
                continue
            seen.add(row_id)
            selected.append({"source_row": row_id, "image_url": url})
        if len(selected) >= needed + 45:
            break
    if len(selected) < needed:
        raise RuntimeError(f"Only found {len(selected)} unused AI-labelled source rows; need {needed}.")
    rng.shuffle(selected)
    return selected


def main() -> None:
    existing_records, current_rows = read_existing()
    remaining = TARGET_COUNT - len(existing_records)
    if remaining <= 0:
        print("All 180 independent AI validation hard cases are already present; no files were changed.")
        return

    candidates = collect_ai_candidates(existing_source_rows() | current_rows, remaining)
    rng = random.Random(RANDOM_SEED + len(existing_records))
    variants = [VARIANTS[index % len(VARIANTS)] for index in range(remaining)]
    rng.shuffle(variants)
    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0

    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for start in range(0, len(candidates), 24):
            if saved >= remaining:
                break
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = [executor.submit(download, candidate) for candidate in candidates[start:start + 24]]
                for future in as_completed(futures):
                    candidate, image = future.result()
                    if image is None or saved >= remaining:
                        continue
                    _, second = download(rng.choice(candidates))
                    if second is None:
                        second = image.copy()
                    variant = variants[saved]
                    output = RENDERERS[variant](image, second, rng)
                    number = len(existing_records) + saved + 1
                    filename = f"independent_val_ai_{number:03d}_{variant}.jpg"
                    path = DESTINATION_DIR / filename
                    temporary = DESTINATION_DIR / f".{filename}.tmp.jpg"
                    output.save(temporary, format="JPEG", quality=92, optimize=True)
                    temporary.replace(path)
                    manifest.write(json.dumps({
                        "created_by": "build_independent_val_ai_hard_cases.py",
                        "dataset": DATASET_ID,
                        "source_license": "mit",
                        "source_row": candidate["source_row"],
                        "label": "ai",
                        "split": "val",
                        "file": f"val/ai/{filename}",
                        "variant": variant,
                    }) + "\n")
                    manifest.flush()
                    saved += 1
                    if saved % 25 == 0 or saved == remaining:
                        print(f"Saved {saved}/{remaining} independent AI validation hard cases")

    if saved != remaining:
        raise RuntimeError(f"Saved {saved}/{remaining}. Re-run the script to resume safely.")
    print("Done. Every added file has a unique AI-labelled source row and recorded provenance.")


if __name__ == "__main__":
    main()
