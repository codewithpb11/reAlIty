"""
Comprehensive dataset diversity analysis for reAlIty.
Parses all manifests and counts images by source, variant, split, and class.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

DATASET_DIR = Path("dataset")

def analyze():
    # Count actual files on disk
    def count_files(folder):
        exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
        if not folder.exists():
            return 0
        return sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in exts)

    print("=" * 70)
    print("ON-DISK IMAGE COUNTS")
    print("=" * 70)
    for split in ("train", "val"):
        for label in ("ai", "hum"):
            c = count_files(DATASET_DIR / split / label)
            print(f"  {split}/{label}: {c}")

    # Parse all manifests
    manifests = {
        "acquisition": DATASET_DIR / "acquisition_manifest.jsonl",
        "blender_cg": DATASET_DIR / "blender_cg_human_manifest.jsonl",
        "derived_human": DATASET_DIR / "derived_human_cases_manifest.jsonl",
        "flux": DATASET_DIR / "realistic_flux_ai_manifest.jsonl",
        "val_human_hard": DATASET_DIR / "validation_human_hard_cases_manifest.jsonl",
        "indep_val_ai": DATASET_DIR / "independent_val_ai_hard_cases_manifest.jsonl",
        "indep_val_human": DATASET_DIR / "independent_val_human_hard_cases_manifest.jsonl",
        "coco_human": DATASET_DIR / "coco_human_manifest.jsonl",
        "requested_genre": DATASET_DIR / "requested_genre_ai_manifest.jsonl",
    }

    all_records = []
    for name, path in manifests.items():
        if not path.exists():
            print(f"\n  [SKIP] {name}: {path} not found")
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rec["_manifest"] = name
                    all_records.append(rec)
                except json.JSONDecodeError:
                    pass

    # Count by source dataset
    print("\n" + "=" * 70)
    print("SOURCE DATASET BREAKDOWN (from manifests)")
    print("=" * 70)
    by_source = Counter()
    for r in all_records:
        src = r.get("source_dataset") or r.get("dataset") or r.get("source", "unknown")
        by_source[src] += 1
    for src, cnt in by_source.most_common():
        print(f"  {src}: {cnt}")

    # Count by acquired_by / script
    print("\n" + "=" * 70)
    print("ACQUISITION SCRIPT BREAKDOWN")
    print("=" * 70)
    by_script = Counter()
    for r in all_records:
        script = r.get("acquired_by") or r.get("created_by") or r.get("_manifest", "unknown")
        by_script[script] += 1
    for script, cnt in by_script.most_common():
        print(f"  {script}: {cnt}")

    # Count by split
    print("\n" + "=" * 70)
    print("SPLIT BREAKDOWN")
    print("=" * 70)
    by_split = defaultdict(lambda: defaultdict(int))
    for r in all_records:
        split = r.get("split", "unknown")
        label = r.get("label", "unknown")
        by_split[split][label] += 1
    for split in sorted(by_split):
        print(f"  {split}:")
        for label in sorted(by_split[split]):
            print(f"    {label}: {by_split[split][label]}")

    # Count variants (hard cases)
    print("\n" + "=" * 70)
    print("VARIANT BREAKDOWN (hard cases)")
    print("=" * 70)
    by_variant = Counter()
    for r in all_records:
        if "variant" in r:
            by_variant[r["variant"]] += 1
    for var, cnt in by_variant.most_common():
        print(f"  {var}: {cnt}")

    # Count by bucket (COCO)
    print("\n" + "=" * 70)
    print("COCO BUCKET BREAKDOWN")
    print("=" * 70)
    coco_buckets = Counter()
    for r in all_records:
        if "bucket" in r and "coco" in str(r.get("acquired_by", "")).lower():
            coco_buckets[r["bucket"]] += 1
    for bucket, cnt in coco_buckets.most_common():
        print(f"  {bucket}: {cnt}")

    # Count FLUX genre/style
    print("\n" + "=" * 70)
    print("FLUX GENRE/STYLE BREAKDOWN")
    print("=" * 70)
    flux_buckets = Counter()
    for r in all_records:
        if "genre" in r and "style" in r:
            flux_buckets[f"{r['genre']}/{r['style']}"] += 1
    for bucket, cnt in flux_buckets.most_common():
        print(f"  {bucket}: {cnt}")

    # Count Blender CG sources
    print("\n" + "=" * 70)
    print("BLENDER CG SOURCES")
    print("=" * 70)
    blender_sources = Counter()
    for r in all_records:
        if "blender" in str(r.get("acquired_by", "")).lower():
            blender_sources[r.get("source", "unknown")] += 1
    for src, cnt in blender_sources.most_common():
        print(f"  {src}: {cnt}")

    # Video files check
    print("\n" + "=" * 70)
    print("VIDEO FILES ON DISK")
    print("=" * 70)
    for split in ("train", "val"):
        for label in ("ai", "hum"):
            folder = DATASET_DIR / split / label
            if not folder.exists():
                continue
            vids = [f for f in folder.iterdir() if f.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".webm"}]
            print(f"  {split}/{label}: {len(vids)} videos")

    # Check for unmanifested files (files with no manifest entry)
    print("\n" + "=" * 70)
    print("UNMANIFESTED FILES (likely manual additions)")
    print("=" * 70)
    all_manifested = set()
    for r in all_records:
        f = r.get("file", "")
        if f:
            all_manifested.add(f.replace("\\", "/"))

    for split in ("train", "val"):
        for label in ("ai", "hum"):
            folder = DATASET_DIR / split / label
            if not folder.exists():
                continue
            unmanifested = []
            for f in folder.iterdir():
                rel = f"{split}/{label}/{f.name}"
                if rel not in all_manifested and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".avif"}:
                    unmanifested.append(f.name)
            if unmanifested:
                print(f"  {split}/{label}: {len(unmanifested)} unmanifested files")
                for name in unmanifested[:5]:
                    print(f"    - {name}")
                if len(unmanifested) > 5:
                    print(f"    ... and {len(unmanifested) - 5} more")

    # Overall summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_manifested = len(all_records)
    print(f"Total manifest records: {total_manifested}")

if __name__ == "__main__":
    analyze()
