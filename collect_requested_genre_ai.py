"""Download 3,000 caption-matched FLUX images into ``dataset/train/ai``.

The upstream corpus is Apache-2.0 and contains rich per-image captions.  This
collector range-reads only caption columns to make subject selections, then
fetches image row groups only for the selected records.  A JSONL manifest keeps
the source id, source shard, caption, and requested genre for every image.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Iterator

import fsspec
import pyarrow.parquet as pq
from PIL import Image, UnidentifiedImageError


DATASET_ID = "LucasFang/FLUX-Reason-6M"
DATASET_LICENSE = "apache-2.0"
SOURCE_BASE = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/main"
ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"
DESTINATION = DATASET_DIR / "train" / "ai"
MANIFEST = DATASET_DIR / "requested_genre_ai_manifest.jsonl"
SOURCE_NOTES = DATASET_DIR / "REQUESTED_GENRE_AI_SOURCES.md"
RANDOM_SEED = 20260801
# ``caption_original`` carries the subject prompt and ``caption_style`` lets us
# reject obvious synthetic/illustrative treatments.  Avoiding the much larger
# generated-detail fields makes remote selection practical.
CAPTION_COLUMNS = ("id", "caption_original", "caption_style")

TARGETS = {
    "devices": 272, "vehicles": 272, "money": 272,
    "business": 273, "doctors": 273, "surgery": 273,
    "theft": 273, "gaming": 273, "playstations": 273,
    "animated_ai": 273, "dancing_people": 273,
}
TERMS = {
    "devices": (r"\b(smartphone|mobile phone|laptop|computer|tablet|camera|headphones|earbuds|drone|robot|television|monitor|keyboard|smartwatch|appliance)\b",),
    "vehicles": (r"\b(car|automobile|truck|bus|motorcycle|bicycle|scooter|train|subway|airplane|aeroplane|helicopter|boat|ship|vehicle)\b",),
    "money": (r"\b(money|cash|currency|banknote|dollar|euro|rupee|coins?|wallet|atm|banking)\b",),
    "business": (r"\b(business|office|meeting|conference|entrepreneur|executive|coworker|workplace|corporate|presentation|boardroom|startup)\b",),
    "doctors": (r"\b(doctor|physician|nurse|medic|healthcare worker|hospital staff|medical professional|clinician)\b",),
    "surgery": (r"\b(surgery|surgical|surgeon|operating room|operating theatre|operation|scrubs|anesthesia)\b",),
    "theft": (r"\b(thief|theft|stealing|stolen|robbery|robber|burglary|burglar|pickpocket|shoplifting|heist|break-in)\b",),
    "gaming": (r"\b(gaming|gamer|video game|esports|e-sports|arcade|game controller|streamer)\b",),
    "playstations": (r"\b(playstation|play station|ps5|ps4|console gaming|gaming console|game console|gamepad)\b",),
    "animated_ai": (r"\b(animated|animation|anime|cartoon|animated film|3d animation|stop motion|illustrated character)\b",),
    "dancing_people": (r"\b(dancing|dancer|dance floor|ballet|ballroom|breakdance|hip-hop dance|choreography)\b",),
}
NATURAL = re.compile(r"\b(photo(?:graph|graphic)?|photorealistic|realistic|camera|candid|documentary|natural light|35mm|filmic|cinematic|editorial|street photograph)\b", re.I)
STYLIZED = re.compile(r"\b(anime|cartoon|illustration|painting|watercolor|drawing|sketch|comic|manga|3d render|cgi|digital art|logo|poster|typography|infographic|icon|pixel art|vector)\b", re.I)
AI_DISCLOSURE = re.compile(r"\b(ai[ -]generated|artificial intelligence|made by ai|generative ai)\b", re.I)
GROUPS = (("Aesthetics-Part01", "fluxdb-aesthetics-part01", 415), ("Aesthetics-Part02", "fluxdb-aesthetics-part02", 454), ("Imaginative", "fluxdb-imaginative", 168))


def caption(row: dict[str, Any]) -> str:
    return " ".join(str(row.get(column) or "") for column in CAPTION_COLUMNS[1:])


def routes(max_shards: int) -> Iterator[tuple[str, str]]:
    values = [(f"{group}/{prefix}-{index:05d}-of-{total:05d}.parquet", f"{SOURCE_BASE}/{group}/{prefix}-{index:05d}-of-{total:05d}.parquet") for group, prefix, total in GROUPS for index in range(total)]
    random.Random(RANDOM_SEED).shuffle(values)
    yield from values[:max_shards]


def open_parquet(url: str):
    handle = fsspec.open(url, "rb", block_size=8 * 1024 * 1024, cache_type="readahead").open()
    return handle, pq.ParquetFile(handle)


def existing() -> tuple[Counter[str], set[str]]:
    counts: Counter[str] = Counter()
    ids: set[str] = set()
    if not MANIFEST.exists():
        return counts, ids
    for line in MANIFEST.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("acquired_by") == "collect_requested_genre_ai.py" and record.get("genre") in TARGETS:
            counts[record["genre"]] += 1
            if isinstance(record.get("source_id"), str):
                ids.add(record["source_id"])
    return counts, ids


def matched_genres(row: dict[str, Any]) -> list[str]:
    text = caption(row)
    if not text or AI_DISCLOSURE.search(text):
        return []
    result = []
    for genre, expressions in TERMS.items():
        if not any(re.search(expression, text, re.I) for expression in expressions):
            continue
        if genre == "animated_ai" or (NATURAL.search(text) and not STYLIZED.search(text)):
            result.append(genre)
    return result


def select(max_shards: int, needed: dict[str, int], used_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    selected = {genre: [] for genre in TARGETS}
    seen = set(used_ids)
    for shard_number, (shard, url) in enumerate(routes(max_shards), 1):
        try:
            handle, parquet = open_parquet(url)
            try:
                # Read the caption columns in one Arrow operation.  Iterating row
                # groups individually causes an HTTP range round-trip for each of
                # the 50 groups in a shard, which is needlessly slow on the Hub.
                group_starts: list[tuple[int, int]] = []
                cursor = 0
                for group_index in range(parquet.num_row_groups):
                    group_starts.append((cursor, group_index))
                    cursor += parquet.metadata.row_group(group_index).num_rows
                table = parquet.read(columns=CAPTION_COLUMNS)
                group_cursor = 0
                for absolute_index, row in enumerate(table.to_pylist()):
                    while group_cursor + 1 < len(group_starts) and absolute_index >= group_starts[group_cursor + 1][0]:
                        group_cursor += 1
                    group_start, group_index = group_starts[group_cursor]
                    index = absolute_index - group_start
                    source_id = str(row["id"])
                    if source_id in seen:
                        continue
                    options = [genre for genre in matched_genres(row) if len(selected[genre]) < needed[genre]]
                    if not options:
                        continue
                    genre = max(options, key=lambda name: needed[name] - len(selected[name]))
                    selected[genre].append({"genre": genre, "source_id": source_id, "shard": shard, "url": url, "row_group": group_index, "row_offset": index, "caption": caption(row)})
                    seen.add(source_id)
            finally:
                handle.close()
        except Exception as error:
            print(f"Skipped metadata shard {shard}: {error}", flush=True)
            continue
        if shard_number % 1 == 0 or all(len(selected[name]) >= needed[name] for name in TARGETS):
            counts = {name: len(rows) for name, rows in selected.items()}
            print(f"Scanned {shard_number}/{max_shards} shards; candidates {sum(counts.values())}/{sum(needed.values())}: {counts}", flush=True)
        if all(len(selected[name]) >= needed[name] for name in TARGETS):
            return selected
    missing = {name: needed[name] - len(rows) for name, rows in selected.items() if len(rows) < needed[name]}
    raise RuntimeError(f"Insufficient caption-matched candidates: {missing}")


def write_notes() -> None:
    SOURCE_NOTES.write_text("# Requested AI-genre additions\n\nThe images recorded in `requested_genre_ai_manifest.jsonl` are from [LucasFang/FLUX-Reason-6M](https://huggingface.co/datasets/LucasFang/FLUX-Reason-6M), a captioned AI-image corpus under Apache-2.0. Keep upstream Apache-2.0 attribution and any applicable upstream NOTICE when redistributing these raw images.\n", encoding="utf-8")


def save(selected: dict[str, list[dict[str, Any]]], needed: dict[str, int]) -> None:
    destinations: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for rows in selected.values():
        for candidate in rows:
            destinations[(candidate["url"], candidate["row_group"])].append(candidate)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    saved: Counter[str] = Counter()
    with MANIFEST.open("a", encoding="utf-8") as manifest:
        for (url, group_index), candidates in destinations.items():
            if all(saved[name] >= needed[name] for name in TARGETS):
                break
            offsets = {candidate["row_offset"]: candidate for candidate in candidates}
            try:
                handle, parquet = open_parquet(url)
                try:
                    rows = parquet.read_row_group(group_index, columns=("id", "image")).to_pylist()
                finally:
                    handle.close()
            except Exception as error:
                print(f"Skipped image row group: {error}", flush=True)
                continue
            for offset, candidate in offsets.items():
                genre = candidate["genre"]
                if saved[genre] >= needed[genre]:
                    continue
                image_value = rows[offset].get("image") or {}
                raw = image_value.get("bytes") if isinstance(image_value, dict) else None
                if not raw:
                    continue
                try:
                    with Image.open(BytesIO(raw)) as image:
                        if min(image.size) < 384:
                            continue
                        filename = f"flux_requested_{genre}_{candidate['source_id']}.jpg"
                        output = DESTINATION / filename
                        if output.exists():
                            continue
                        temporary = DESTINATION / f".{filename}.tmp.jpg"
                        image.convert("RGB").save(temporary, "JPEG", quality=94, optimize=True)
                        temporary.replace(output)
                except (UnidentifiedImageError, OSError, ValueError):
                    continue
                manifest.write(json.dumps({"acquired_by": "collect_requested_genre_ai.py", "dataset": DATASET_ID, "source_license": DATASET_LICENSE, "source_id": candidate["source_id"], "source_shard": candidate["shard"], "split": "train", "label": "ai", "genre": genre, "file": str(output.relative_to(DATASET_DIR)).replace("\\\\", "/"), "caption": candidate["caption"]}, ensure_ascii=False) + "\n")
                manifest.flush()
                saved[genre] += 1
                if saved[genre] % 25 == 0 or saved[genre] == needed[genre]:
                    print(f"Saved {genre}: {saved[genre]}/{needed[genre]}", flush=True)
    missing = {name: needed[name] - saved[name] for name in TARGETS if saved[name] < needed[name]}
    if missing:
        raise RuntimeError(f"Image extraction incomplete: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-shards", type=int, default=300)
    args = parser.parse_args()
    if sum(TARGETS.values()) != 3000:
        raise AssertionError("target must total 3,000")
    counts, ids = existing()
    needed = {name: TARGETS[name] - counts[name] for name in TARGETS}
    if not any(needed.values()):
        print("The requested 3,000 images are already present.", flush=True)
        return
    write_notes()
    save(select(args.max_shards, needed, ids), needed)
    print("Completed the 3,000 requested additions.", flush=True)


if __name__ == "__main__":
    main()
