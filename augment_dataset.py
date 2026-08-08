"""Add traceable, publicly labelled images to reAlIty's dataset.

This utility downloads only the requested images from the public,
MIT-licensed ``Parveshiiii/AI-vs-Real`` dataset on Hugging Face.  It intentionally
does not scrape arbitrary web pages.  Every saved file is recorded with its
source dataset and licence in ``dataset/acquisition_manifest.jsonl``.

The numbers in DATASET_TARGETS below are TOTAL counts you want sitting in
each folder, not additions on top of some assumed starting point. Every run
counts the actual image files currently in each dataset folder - your own
manual photos, hard-case derivatives from the other scripts, earlier runs of
this script, everything - and only downloads the shortfall needed to reach
the target. If a folder is already at or above its target, it is left
completely untouched.

The script is safe to re-run: it records every source row in a manifest and
never re-downloads a row already used anywhere (by this script or by the
independent-validation hard-case builders).

Run from the project folder:
    python augment_dataset.py
"""

from __future__ import annotations

import json
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image, UnidentifiedImageError


DATASET_ID = "Parveshiiii/AI-vs-Real"
DATASET_LICENSE = "mit"
ROWS_API = "https://datasets-server.huggingface.co/rows"
PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "dataset"
SPLIT_DIRS = {
    "train": {"ai": DATASET_DIR / "train" / "ai", "hum": DATASET_DIR / "train" / "hum"},
    "val": {"ai": DATASET_DIR / "val" / "ai", "hum": DATASET_DIR / "val" / "hum"},
}
MANIFEST_PATH = DATASET_DIR / "acquisition_manifest.jsonl"
SOURCES_PATH = DATASET_DIR / "DATASET_SOURCES.md"

# Manifests from the OTHER scripts that also draw source rows from
# Parveshiiii/AI-vs-Real. Rows already spent there are skipped here too, so
# the same source photo never ends up both as a plain addition and as the
# base image for one of the independent-validation hard-case edits.
OTHER_SOURCE_MANIFESTS = [
    DATASET_DIR / "independent_val_ai_hard_cases_manifest.jsonl",
    DATASET_DIR / "independent_val_human_hard_cases_manifest.jsonl",
]

# Final totals you want sitting in each dataset folder, counting every image
# already there for any reason.
DATASET_TARGETS = {
    "train": {"ai": 1800, "hum": 1800},
    "val": {"ai": 350, "hum": 350},
}
LABEL_TO_FOLDER = {0: "ai", 1: "hum"}
ALLOWED_LICENSES = {
    "apache-2.0",
    "bsd-3-clause",
    "cc-by-4.0",
    "cc0-1.0",
    "mit",
    "public-domain",
    "pdm",
}
RANDOM_SEED = 20260731
PAGE_SIZE = 100
MAX_BLOCKS = 140  # Parveshiiii/AI-vs-Real has ~14k rows total (140 pages of 100)
# The public source itself is MIT-licensed. Its API does not expose a separate
# origin field per image, so random samples are drawn across its whole corpus.
MAX_PER_SOURCE = {"ai": 10_000, "hum": 10_000}
WORKERS = 10
REQUEST_TIMEOUT = 45
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _normalise_license(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "-")


def _request_json(session: requests.Session, params: dict[str, Any]) -> dict[str, Any]:
    for attempt in range(4):
        try:
            response = session.get(ROWS_API, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as error:
            if attempt == 3:
                raise RuntimeError(f"Could not query the public dataset: {error}") from error
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def _current_counts() -> dict[str, dict[str, int]]:
    """Count every image file actually sitting in each dataset folder right now."""
    counts: dict[str, dict[str, int]] = {}
    for split, labels in SPLIT_DIRS.items():
        counts[split] = {}
        for label, folder in labels.items():
            if not folder.exists():
                counts[split][label] = 0
                continue
            counts[split][label] = sum(
                1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            )
    return counts


def _used_source_rows() -> set[int]:
    """Source-row ids already spent by this script or by the hard-case builders."""
    row_ids: set[int] = set()
    for path in [MANIFEST_PATH, *OTHER_SOURCE_MANIFESTS]:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as manifest:
            for line in manifest:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record.get("source_row"), int):
                    row_ids.add(record["source_row"])
    return row_ids


def _collect_candidates(needed: dict[str, int], used_rows: set[int]) -> dict[str, list[dict[str, Any]]]:
    """Collect a large, random, licence-compatible candidate pool."""
    session = requests.Session()
    session.headers["User-Agent"] = "reAlIty-training-data-builder/1.0"
    first_page = _request_json(
        session,
        {"dataset": DATASET_ID, "config": "default", "split": "train", "offset": 0, "length": 1},
    )
    total_rows = int(first_page["num_rows_total"])
    block_count = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE
    rng = random.Random(RANDOM_SEED)
    blocks = rng.sample(range(block_count), k=min(MAX_BLOCKS, block_count))

    candidates: dict[str, list[dict[str, Any]]] = {"ai": [], "hum": []}
    seen_rows = set(used_rows)

    for number, block in enumerate(blocks, start=1):
        try:
            page = _request_json(
                session,
                {
                    "dataset": DATASET_ID,
                    "config": "default",
                    "split": "train",
                    "offset": block * PAGE_SIZE,
                    "length": PAGE_SIZE,
                },
            )
        except RuntimeError as error:
            print(f"Skipped an unavailable public-data batch: {error}")
            continue
        for item in page.get("rows", []):
            row_id = int(item["row_idx"])
            if row_id in seen_rows:
                continue
            row = item["row"]
            folder = LABEL_TO_FOLDER.get(row.get("binary_label"))
            licence = DATASET_LICENSE
            image_data = row.get("image") or {}
            image_url = image_data.get("src")
            if folder is None or licence not in ALLOWED_LICENSES or not image_url:
                continue
            seen_rows.add(row_id)
            candidates[folder].append(
                {
                    "source_row": row_id,
                    "source_dataset": DATASET_ID,
                    "source_license": licence,
                    "image_url": image_url,
                }
            )
        if number % 20 == 0:
            print(f"Collected candidates from {number}/{len(blocks)} public-data batches...")

    for label in candidates:
        rng.shuffle(candidates[label])
    return candidates


def _select_diverse(candidates: list[dict[str, Any]], amount: int, per_source_cap: int) -> list[dict[str, Any]]:
    """Round-robin sources, avoiding one source dominating the additions."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["source_dataset"]].append(candidate)

    source_names = list(grouped)
    random.Random(RANDOM_SEED + amount).shuffle(source_names)
    selected: list[dict[str, Any]] = []
    selected_per_source: dict[str, int] = defaultdict(int)

    while len(selected) < amount:
        added_this_round = False
        for source_name in source_names:
            if len(selected) >= amount:
                break
            if selected_per_source[source_name] >= per_source_cap or not grouped[source_name]:
                continue
            selected.append(grouped[source_name].pop())
            selected_per_source[source_name] += 1
            added_this_round = True
        if not added_this_round:
            break
    return selected


def _download_image(candidate: dict[str, Any]) -> tuple[dict[str, Any], Image.Image | None, str | None]:
    """Download and decode an image in a worker; saving remains single-threaded."""
    try:
        response = requests.get(candidate["image_url"], timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            return candidate, image.convert("RGB").copy(), None
    except (requests.RequestException, UnidentifiedImageError, OSError, ValueError) as error:
        return candidate, None, str(error)


def _write_sources_file() -> None:
    if SOURCES_PATH.exists() and DATASET_ID in SOURCES_PATH.read_text(encoding="utf-8"):
        return
    SOURCES_PATH.write_text(
        "# Added labelled-image source\n\n"
        "This folder contains additional training and validation images downloaded by "
        "`augment_dataset.py` from `Parveshiiii/AI-vs-Real` on Hugging Face. "
        "The dataset card declares an MIT licence and maps label `0` to AI-generated "
        "and label `1` to real/human-captured.\n\n"
        "`acquisition_manifest.jsonl` records the split, source dataset, MIT licence, and "
        "source row for every added file. Keep this attribution and licence notice if "
        "you distribute the raw training images.\n",
        encoding="utf-8",
    )


def _save_additions(split: str, label: str, pool: list[dict[str, Any]], needed: int) -> int:
    destination = SPLIT_DIRS[split][label]
    destination.mkdir(parents=True, exist_ok=True)
    added = 0
    failures = 0

    # The surplus candidates cover occasional HTTP or image-decoding failures.
    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for start in range(0, len(pool), 32):
            if added >= needed:
                break
            batch = pool[start : start + 32]
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = [executor.submit(_download_image, candidate) for candidate in batch]
                for future in as_completed(futures):
                    candidate, image, error = future.result()
                    if image is None:
                        failures += 1
                        continue
                    if added >= needed:
                        continue

                    filename = f"corpus_{split}_{label}_{candidate['source_row']:08d}.jpg"
                    output_path = destination / filename
                    temporary_path = destination / f".{filename}.tmp.jpg"
                    if output_path.exists():
                        continue
                    image.save(temporary_path, format="JPEG", quality=95, optimize=True)
                    temporary_path.replace(output_path)

                    record = {
                        "acquired_by": "augment_dataset.py",
                        "dataset": DATASET_ID,
                        "split": split,
                        "label": label,
                        "file": str(output_path.relative_to(DATASET_DIR)).replace("\\", "/"),
                        "source_row": candidate["source_row"],
                        "source_dataset": candidate["source_dataset"],
                        "source_license": candidate["source_license"],
                    }
                    manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
                    manifest.flush()
                    added += 1
                    if added % 25 == 0 or added == needed:
                        print(f"{label}: saved {added}/{needed}")

    if failures:
        print(f"{label}: skipped {failures} unreadable or unavailable public records")
    return added


def main() -> None:
    _write_sources_file()
    current = _current_counts()
    used_rows = _used_source_rows()

    for split, labels in DATASET_TARGETS.items():
        for label, target in labels.items():
            have = current[split][label]
            if have > target:
                print(f"Note: {split}/{label} already has {have} images, above the {target} target - leaving it as is.")

    needed = {
        split: {
            label: max(0, target - current[split][label])
            for label, target in labels.items()
        }
        for split, labels in DATASET_TARGETS.items()
    }
    needed_by_label = {
        label: sum(needed[split][label] for split in needed)
        for label in ("ai", "hum")
    }
    if not any(needed_by_label.values()):
        print("Every folder is already at or above its target; no files were changed.")
        return

    print(
        "Topping up to target: "
        f"{needed['train']['ai']} more train AI, {needed['train']['hum']} more train human, "
        f"{needed['val']['ai']} more validation AI, and {needed['val']['hum']} more validation human images."
    )
    candidates = _collect_candidates(needed_by_label, used_rows)

    pools: dict[str, list[dict[str, Any]]] = {}
    for label in ("ai", "hum"):
        # Keep a generous reserve so failed downloads do not change the requested total.
        pool_size = needed_by_label[label] + max(120, needed_by_label[label] // 4)
        pool = _select_diverse(candidates[label], pool_size, MAX_PER_SOURCE[label])
        if len(pool) < needed_by_label[label]:
            raise RuntimeError(
                f"Only found {len(pool)} compatible {label} candidates, but {needed_by_label[label]} are needed. "
                "No training images were added."
            )
        pools[label] = pool

    for split in ("train", "val"):
        for label in ("ai", "hum"):
            amount = needed[split][label]
            if not amount:
                continue
            # Keep a private reserve for this split. If a public image has
            # disappeared or cannot be decoded, _save_additions can continue
            # with the next candidate instead of leaving the target short.
            selection_size = min(len(pools[label]), amount + max(30, amount // 4))
            selected, pools[label] = pools[label][:selection_size], pools[label][selection_size:]
            saved = _save_additions(split, label, selected, amount)
            if saved != amount:
                raise RuntimeError(
                    f"Saved {saved}/{amount} {split} {label} images. Re-run the script to resume."
                )

    print("Finished. Every folder is now at its target, with provenance recorded in the dataset folder.")


if __name__ == "__main__":
    main()
