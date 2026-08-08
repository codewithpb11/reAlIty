"""check_flux_sources_removed.py

Confirms whether any images downloaded from LucasFang/FLUX-Reason-6M (via
collect_requested_genre_ai.py or collect_realistic_flux_ai.py) are still
sitting in the dataset folders. Checks the actual files on disk against
what's recorded in each script's manifest - doesn't rely on memory of
what was deleted.

Run from the project folder:
    python check_flux_sources_removed.py
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "dataset"

FLUX_MANIFESTS = [
    DATASET_DIR / "requested_genre_ai_manifest.jsonl",
    DATASET_DIR / "realistic_flux_ai_manifest.jsonl",
]


def main() -> None:
    remaining = []
    checked = 0
    for manifest_path in FLUX_MANIFESTS:
        if not manifest_path.exists():
            print(f"{manifest_path.name}: not found, skipping.")
            continue
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            checked += 1
            file_path = DATASET_DIR / record["file"]
            if file_path.exists():
                remaining.append(str(file_path.relative_to(DATASET_DIR)))

    print(f"Checked {checked} recorded FLUX-derived entries across {len(FLUX_MANIFESTS)} manifest(s).")
    if remaining:
        print(f"\n{len(remaining)} FLUX.1-dev-derived images are STILL present, e.g.:")
        for path in remaining[:10]:
            print(f"  {path}")
        if len(remaining) > 10:
            print(f"  ... and {len(remaining) - 10} more.")
        print("\nThese carry the FLUX.1-dev licensing question flagged earlier -")
        print("worth deleting before a commercial (Gumroad) release.")
    else:
        print("\nNone found. No FLUX-derived images remain in the dataset folders.")


if __name__ == "__main__":
    main()
