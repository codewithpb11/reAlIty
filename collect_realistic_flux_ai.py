"""Build a caption-filtered, photo-realistic AI-image extension for reAlIty.

The earlier random downloader cannot distinguish an illustration from a photo.
This collector instead uses the caption metadata exposed by the public
``Zitacron/real-vs-ai-corpus`` viewer.  It accepts only rows labelled AI whose
original source is ``LucasFang/FLUX-Reason-6M`` and whose captions support one
of the requested genre/style buckets.  Every selected source row is unique and
is recorded in a manifest, so train and validation never share an image.

Run a dry audit first:
    python collect_realistic_flux_ai.py --dry-run --max-pages 250

Then collect the requested additions:
    python collect_realistic_flux_ai.py --max-pages 900
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import random
import re
import time
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image, UnidentifiedImageError


DATASET_ID = "Zitacron/real-vs-ai-corpus"
SOURCE_DATASET = "LucasFang/FLUX-Reason-6M"
ROWS_API = "https://datasets-server.huggingface.co/rows"
PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "dataset"
MANIFEST_PATH = DATASET_DIR / "realistic_flux_ai_manifest.jsonl"
PAGE_SIZE = 100
RANDOM_SEED = 20260801
REQUEST_TIMEOUT = 45
PAGE_WORKERS = 6
IMAGE_WORKERS = 8

# 709 total additions: 619 train + 90 validation.  The 11 genres and 3 styles
# are intentionally balanced rather than allowing people portraits to dominate.
GENRES: dict[str, tuple[str, ...]] = {
    "people": (r"\b(person|people|woman|women|man|men|child|children|family|friends|crowd|student|worker|portrait)\b",),
    "animals": (r"\b(dog|cat|horse|elephant|lion|tiger|bear|fox|wolf|animal|wildlife|mammal)\b",),
    "parties": (r"\b(party|festival|celebration|wedding|birthday|gathering|concert|dance|reunion)\b",),
    "politics": (r"\b(politic|election|campaign|parliament|government|rally|senator|mayor|debate|protest)\b",),
    "celestial_beings": (r"\b(angel|celestial being|deity|mythical being|ethereal person)\b",),
    "planets": (r"\b(planet|earth from space|mars|jupiter|saturn|moon surface|exoplanet)\b",),
    "stars": (r"\b(starfield|stars|milky way|night sky|constellation|galaxy|nebula)\b",),
    "underwater": (r"\b(underwater|under water|ocean floor|coral reef|dolphin|whale|shark|octopus|jellyfish|sea turtle|fish)\b",),
    "objects": (r"\b(object|chair|table|camera|bicycle|car|book|watch|vase|building|kitchen|furniture|vehicle|instrument)\b",),
    "birds": (r"\b(bird|eagle|owl|parrot|sparrow|falcon|penguin|flamingo|swan)\b",),
    "nature": (r"\b(nature|forest|mountain|river|lake|waterfall|beach|landscape|meadow|tree|garden|desert)\b",),
}
STYLES: dict[str, tuple[str, ...]] = {
    "concept": (r"\b(concept art|conceptual photograph|conceptual photo|photorealistic concept)\b",),
    "cinematic": (r"\b(cinematic|film still|filmic|35mm|movie scene|dramatic lighting)\b",),
    "casual": (r"\b(candid|casual|documentary|everyday|snapshot|street photograph|natural light)\b",),
}
PHOTO_EVIDENCE = re.compile(
    r"\b(photo(?:graph|graphic)?|photorealistic|realistic|camera|candid|documentary|natural light|35mm|filmic|cinematic)\b",
    re.IGNORECASE,
)
REJECT_STYLE = re.compile(
    r"\b(anime|cartoon|illustration|painting|watercolor|drawing|sketch|comic|manga|3d render|cgi|digital art|logo|poster|typography|infographic|icon|pixel art)\b",
    re.IGNORECASE,
)


def _bucket_targets() -> dict[tuple[str, str], dict[str, int]]:
    """Return balanced per-genre/style targets that sum exactly to 619/90."""
    buckets = [(genre, style) for genre in GENRES for style in STYLES]
    targets: dict[tuple[str, str], dict[str, int]] = {}
    # 21 each gives 693.  The first 16 receive one extra = 709.
    # Validation is 3 images in 24 buckets and 2 in the other 9 = 90.
    for index, bucket in enumerate(buckets):
        total = 22 if index < 16 else 21
        validation = 3 if index < 24 else 2
        targets[bucket] = {"train": total - validation, "val": validation}
    assert sum(value["train"] for value in targets.values()) == 619
    assert sum(value["val"] for value in targets.values()) == 90
    return targets


def _caption(row: dict[str, Any]) -> str:
    fields = ("caption_composition", "caption_entity", "caption_style", "caption_detail", "caption_original")
    return " ".join(str(row.get(field) or "") for field in fields)


def _matching_buckets(row: dict[str, Any]) -> list[tuple[str, str]]:
    if row.get("label_text") != "ai" or row.get("source_dataset") != SOURCE_DATASET:
        return []
    text = _caption(row)
    if not text or REJECT_STYLE.search(text) or not PHOTO_EVIDENCE.search(text):
        return []
    matches: list[tuple[str, str]] = []
    for genre, genre_terms in GENRES.items():
        if not any(re.search(term, text, re.IGNORECASE) for term in genre_terms):
            continue
        for style, style_terms in STYLES.items():
            if any(re.search(term, text, re.IGNORECASE) for term in style_terms):
                matches.append((genre, style))
    return matches


def _fetch_page(offset: int) -> list[dict[str, Any]]:
    response = requests.get(
        ROWS_API,
        params={"dataset": DATASET_ID, "config": "default", "split": "train", "offset": offset, "length": PAGE_SIZE},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("rows", [])


def _existing_rows() -> set[int]:
    if not MANIFEST_PATH.exists():
        return set()
    rows: set[int] = set()
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            if record.get("dataset") == DATASET_ID and isinstance(record.get("source_row"), int):
                rows.add(record["source_row"])
        except json.JSONDecodeError:
            continue
    return rows


def _collect(max_pages: int, targets: dict[tuple[str, str], dict[str, int]], used_rows: set[int]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    first_page = _fetch_page(0)
    # The viewer always returns 100 rows; request one metadata page to retrieve total.
    metadata = requests.get(
        ROWS_API,
        params={"dataset": DATASET_ID, "config": "default", "split": "train", "offset": 0, "length": 1},
        timeout=REQUEST_TIMEOUT,
    ).json()
    total_rows = int(metadata["num_rows_total"])
    blocks = total_rows // PAGE_SIZE
    rng = random.Random(RANDOM_SEED)
    offsets = [0] + [block * PAGE_SIZE for block in rng.sample(range(1, blocks), min(max_pages - 1, blocks - 1))]
    selected: dict[tuple[str, str], list[dict[str, Any]]] = {bucket: [] for bucket in targets}
    needed = {bucket: sum(counts.values()) for bucket, counts in targets.items()}

    def choose_bucket(matches: list[tuple[str, str]]) -> tuple[str, str] | None:
        choices = [bucket for bucket in matches if len(selected[bucket]) < needed[bucket]]
        if not choices:
            return None
        return max(choices, key=lambda bucket: needed[bucket] - len(selected[bucket]))

    pages_seen = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=PAGE_WORKERS) as executor:
        for start in range(0, len(offsets), PAGE_WORKERS):
            batch_offsets = offsets[start : start + PAGE_WORKERS]
            futures = [executor.submit(_fetch_page, offset) for offset in batch_offsets]
            for future in concurrent.futures.as_completed(futures):
                pages_seen += 1
                try:
                    page = future.result()
                except (requests.RequestException, ValueError) as error:
                    print(f"Skipped unavailable metadata page: {error}")
                    continue
                for item in page:
                    row_id = int(item["row_idx"])
                    if row_id in used_rows:
                        continue
                    row = item["row"]
                    bucket = choose_bucket(_matching_buckets(row))
                    image = row.get("image") or {}
                    if bucket is None or not image.get("src"):
                        continue
                    selected[bucket].append(
                        {
                            "source_row": row_id,
                            "image_url": image["src"],
                            "source_license": row.get("source_license", "unknown"),
                            "caption": _caption(row),
                        }
                    )
                    used_rows.add(row_id)
            complete = sum(len(rows) for rows in selected.values())
            print(f"Scanned {pages_seen}/{len(offsets)} metadata pages; selected {complete}/709 candidates")
            if complete == 709:
                break
    return selected


def _download(candidate: dict[str, Any]) -> Image.Image | None:
    try:
        response = requests.get(candidate["image_url"], timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            image = image.convert("RGB")
            if min(image.size) < 384:
                return None
            return image.copy()
    except (requests.RequestException, UnidentifiedImageError, OSError, ValueError):
        return None


def _save(selected: dict[tuple[str, str], list[dict[str, Any]]], targets: dict[tuple[str, str], dict[str, int]]) -> None:
    failures: Counter[str] = Counter()
    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for bucket, candidates in selected.items():
            genre, style = bucket
            cursor = 0
            for split in ("train", "val"):
                amount = targets[bucket][split]
                destination = DATASET_DIR / split / "ai"
                destination.mkdir(parents=True, exist_ok=True)
                saved = 0
                # Candidates are already distinct; attempt a small reserve in the bucket.
                with concurrent.futures.ThreadPoolExecutor(max_workers=IMAGE_WORKERS) as executor:
                    while saved < amount and cursor < len(candidates):
                        batch = candidates[cursor : cursor + min(24, len(candidates) - cursor)]
                        cursor += len(batch)
                        futures = {executor.submit(_download, candidate): candidate for candidate in batch}
                        for future in concurrent.futures.as_completed(futures):
                            if saved >= amount:
                                continue
                            candidate = futures[future]
                            image = future.result()
                            if image is None:
                                failures[split] += 1
                                continue
                            filename = f"flux_{split}_{genre}_{style}_{candidate['source_row']:08d}.jpg"
                            output = destination / filename
                            if output.exists():
                                continue
                            image.save(output, format="JPEG", quality=94, optimize=True)
                            manifest.write(json.dumps({
                                "acquired_by": "collect_realistic_flux_ai.py",
                                "dataset": DATASET_ID,
                                "source_dataset": SOURCE_DATASET,
                                "source_license": candidate["source_license"],
                                "source_row": candidate["source_row"],
                                "split": split,
                                "label": "ai",
                                "genre": genre,
                                "style": style,
                                "file": str(output.relative_to(DATASET_DIR)).replace("\\\\", "/"),
                                "caption": candidate["caption"],
                            }, ensure_ascii=False) + "\n")
                            manifest.flush()
                            saved += 1
                if saved != amount:
                    raise RuntimeError(f"{bucket}/{split}: saved {saved}/{amount}; no partial bucket is silently accepted")
    if failures:
        print(f"Skipped unreadable downloads: {dict(failures)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.max_pages < 1:
        raise SystemExit("--max-pages must be at least 1")
    targets = _bucket_targets()
    selected = _collect(args.max_pages, targets, _existing_rows())
    counts = {f"{genre}/{style}": len(rows) for (genre, style), rows in selected.items()}
    print(json.dumps(counts, indent=2))
    complete = all(len(selected[bucket]) == sum(targets[bucket].values()) for bucket in targets)
    if not complete:
        raise RuntimeError("Not enough caption-filtered candidates. Increase --max-pages; no image files were written.")
    if args.dry_run:
        print("Dry run complete: no files written.")
        return
    _save(selected, targets)
    print("Saved 619 train and 90 validation AI images with source-row provenance.")


if __name__ == "__main__":
    main()
