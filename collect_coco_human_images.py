"""Add 6,500 real photographs to dataset/train/hum from captioned COCO 2017.

Images are selected from a public real-photo corpus using its human-written
captions, recorded with the original row and COCO licence id, and saved only
to the training human folder.  It is resumable: files already listed in the
manifest are never downloaded again.

Run a no-write availability check first:
    python collect_coco_human_images.py --dry-run --max-pages 80

Then run the collection:
    python collect_coco_human_images.py --max-pages 180
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image, UnidentifiedImageError

DATASET_ID = "phiyodr/coco2017"
ROWS_API = "https://datasets-server.huggingface.co/rows"
ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "dataset" / "train" / "hum"
MANIFEST = ROOT / "dataset" / "coco_human_manifest.jsonl"
TARGET = 6500
PAGE_SIZE = 100
REQUEST_DELAY_SECONDS = 1.25  # avoids the public viewer's rate limit
SEED = 20260801

# Broad, real-world caption buckets. The totals equal 6,500.
BUCKETS: dict[str, tuple[int, tuple[str, ...]]] = {
    "people_everyday_work": (1200, (r"\b(man|woman|people|person|child|family|worker|street|office|kitchen)\b",)),
    "food_eating": (500, (r"\b(food|meal|pizza|cake|sandwich|plate|restaurant|eating|kitchen)\b",)),
    "water_travel_outdoors": (700, (r"\b(ocean|water|beach|boat|surf|swimming|travel|mountain|lake|river)\b",)),
    "transport": (700, (r"\b(car|truck|bus|train|airplane|bicycle|motorcycle|traffic|vehicle)\b",)),
    "devices_media": (500, (r"\b(phone|computer|laptop|television|tv|camera|remote|screen|keyboard)\b",)),
    "books_education": (300, (r"\b(book|school|student|classroom|college|reading|library|education)\b",)),
    "sports_hobbies_music": (700, (r"\b(sport|playing|tennis|baseball|soccer|ski|skate|surf|guitar|instrument|dance|martial)\b",)),
    "animals_nature": (700, (r"\b(dog|cat|bird|horse|animal|zebra|elephant|tree|forest|flower|grass)\b",)),
    "home_shopping_social": (700, (r"\b(home|room|bed|chair|table|store|shopping|market|party|wedding)\b",)),
    "general_real_photos": (500, (r".*",)),
}
REJECT = re.compile(r"\b(cartoon|drawing|painting|illustration|diagram|logo|poster|text)\b", re.IGNORECASE)


def existing_rows() -> set[int]:
    if not MANIFEST.exists():
        return set()
    used: set[int] = set()
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
            if item.get("dataset") == DATASET_ID and isinstance(item.get("source_row"), int):
                used.add(item["source_row"])
        except json.JSONDecodeError:
            pass
    return used


def request_rows(offset: int, length: int = PAGE_SIZE) -> dict[str, Any]:
    params = {"dataset": DATASET_ID, "config": "default", "split": "train", "offset": offset, "length": length}
    for attempt in range(8):
        response = requests.get(ROWS_API, params=params, timeout=60)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()
        delay = min(120, 12 * (attempt + 1))
        print(f"Rate-limited at offset {offset}; waiting {delay}s before retry {attempt + 1}/8", flush=True)
        time.sleep(delay)
    raise requests.HTTPError(f"Rate limit persisted for metadata offset {offset}")


def select_candidates(max_pages: int, used: set[int]) -> dict[str, list[dict[str, Any]]]:
    first = request_rows(0, 1)
    block_count = int(first["num_rows_total"]) // PAGE_SIZE
    rng = random.Random(SEED)
    page_numbers = rng.sample(range(block_count), min(max_pages, block_count))
    selected: dict[str, list[dict[str, Any]]] = defaultdict(list)
    capacities = {name: amount + max(25, amount // 8) for name, (amount, _) in BUCKETS.items()}

    for page_index, page_number in enumerate(page_numbers, start=1):
        try:
            page = request_rows(page_number * PAGE_SIZE)
        except requests.RequestException as error:
            print(f"Skipped metadata page {page_index}: {error}", flush=True)
            time.sleep(15)
            continue
        for item in page.get("rows", []):
            row_id = int(item["row_idx"])
            row = item["row"]
            if row_id in used:
                continue
            captions = " ".join(str(value) for value in row.get("captions", []))
            if not captions or REJECT.search(captions):
                continue
            choices = [
                name for name, (_, terms) in BUCKETS.items()
                if len(selected[name]) < capacities[name]
                and any(re.search(term, captions, re.IGNORECASE) for term in terms)
            ]
            if not choices:
                continue
            bucket = max(choices, key=lambda name: capacities[name] - len(selected[name]))
            selected[bucket].append({
                "source_row": row_id,
                "bucket": bucket,
                # Preserve COCO's public HTTP URL. In this environment its
                # HTTPS endpoint presents a certificate-host mismatch.
                "url": row["coco_url"],
                "license_id": row.get("license"),
                "captions": row.get("captions", []),
            })
            used.add(row_id)
        found = sum(len(items) for items in selected.values())
        print(f"Scanned {page_index}/{len(page_numbers)} metadata pages; selected {found} reserve candidates", flush=True)
        time.sleep(2.5)
        if all(len(selected[name]) >= capacities[name] for name in BUCKETS):
            break
    return selected


def fetch_image(candidate: dict[str, Any]) -> Image.Image | None:
    try:
        response = requests.get(candidate["url"], timeout=60)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            image = image.convert("RGB")
            return image.copy() if min(image.size) >= 320 else None
    except (requests.RequestException, UnidentifiedImageError, OSError, ValueError):
        return None


def save_images(selected: dict[str, list[dict[str, Any]]]) -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", encoding="utf-8") as manifest:
        for bucket, (target, _) in BUCKETS.items():
            saved = 0
            candidates = selected[bucket]
            with ThreadPoolExecutor(max_workers=8) as executor:
                for start in range(0, len(candidates), 32):
                    if saved >= target:
                        break
                    futures = {executor.submit(fetch_image, item): item for item in candidates[start : start + 32]}
                    for future in as_completed(futures):
                        if saved >= target:
                            continue
                        candidate = futures[future]
                        image = future.result()
                        if image is None:
                            continue
                        output = DESTINATION / f"coco_human_{bucket}_{candidate['source_row']:08d}.jpg"
                        if output.exists():
                            continue
                        image.save(output, format="JPEG", quality=94, optimize=True)
                        manifest.write(json.dumps({
                            "acquired_by": "collect_coco_human_images.py",
                            "dataset": DATASET_ID,
                            "source_row": candidate["source_row"],
                            "split": "train",
                            "label": "hum",
                            "bucket": bucket,
                            "license_id": candidate["license_id"],
                            "file": str(output.relative_to(ROOT / "dataset")).replace("\\", "/"),
                            "captions": candidate["captions"],
                        }, ensure_ascii=False) + "\n")
                        manifest.flush()
                        saved += 1
            if saved != target:
                raise RuntimeError(f"{bucket}: saved {saved}/{target}. Re-run to resume safely.")
            print(f"Saved {bucket}: {saved}/{target}")


def save_exact_total(selected: dict[str, list[dict[str, Any]]]) -> None:
    """Save exactly TARGET photos while retaining the caption-derived bucket."""
    candidates = [item for items in selected.values() for item in items]
    random.Random(SEED).shuffle(candidates)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    saved = 0
    with MANIFEST.open("a", encoding="utf-8") as manifest:
        with ThreadPoolExecutor(max_workers=8) as executor:
            for start in range(0, len(candidates), 32):
                if saved >= TARGET:
                    break
                futures = {executor.submit(fetch_image, item): item for item in candidates[start : start + 32]}
                for future in as_completed(futures):
                    if saved >= TARGET:
                        continue
                    candidate = futures[future]
                    image = future.result()
                    if image is None:
                        continue
                    output = DESTINATION / f"coco_human_{candidate['bucket']}_{candidate['source_row']:08d}.jpg"
                    if output.exists():
                        continue
                    image.save(output, format="JPEG", quality=94, optimize=True)
                    manifest.write(json.dumps({
                        "acquired_by": "collect_coco_human_images.py",
                        "dataset": DATASET_ID,
                        "source_row": candidate["source_row"],
                        "split": "train",
                        "label": "hum",
                        "bucket": candidate["bucket"],
                        "license_id": candidate["license_id"],
                        "file": str(output.relative_to(ROOT / "dataset")).replace("\\", "/"),
                        "captions": candidate["captions"],
                    }, ensure_ascii=False) + "\n")
                    manifest.flush()
                    saved += 1
                    if saved % 100 == 0:
                        print(f"Saved {saved}/{TARGET} real photos")
    if saved != TARGET:
        raise RuntimeError(f"Saved {saved}/{TARGET}. Re-run to resume safely.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    selected = select_candidates(args.max_pages, existing_rows())
    counts = {name: len(selected[name]) for name in BUCKETS}
    print(json.dumps(counts, indent=2))
    total_candidates = sum(counts.values())
    if total_candidates < TARGET:
        raise RuntimeError(f"Only found {total_candidates}/{TARGET} broad caption-matched candidates. Increase --max-pages; no files written.")
    if args.dry_run:
        print("Dry run passed; no files written.")
        return
    save_exact_total(selected)
    print("Finished: 6,500 real human images added to dataset/train/hum.")


if __name__ == "__main__":
    main()
