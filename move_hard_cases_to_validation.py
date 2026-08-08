"""Move the generated human hard cases from training to validation exactly once."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
TRAIN_DIR = PROJECT_DIR / "dataset" / "train" / "hum"
VALIDATION_DIR = PROJECT_DIR / "dataset" / "val" / "hum"
MANIFEST_PATH = PROJECT_DIR / "dataset" / "derived_human_cases_manifest.jsonl"


def main() -> None:
    records = [json.loads(line) for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines() if line]
    selected = [
        record for record in records
        if record.get("created_by") == "create_human_hard_cases.py"
        and record.get("split") == "train"
        and record.get("label") == "hum"
    ]
    if not selected:
        print("No generated human hard cases remain in the training split.")
        return

    sources = [TRAIN_DIR / Path(record["file"]).name for record in selected]
    missing = [path.name for path in sources if not path.is_file()]
    destinations = [VALIDATION_DIR / path.name for path in sources]
    collisions = [path.name for path in destinations if path.exists()]
    if missing or collisions:
        raise RuntimeError(f"Refusing to move files. Missing: {missing}; destination collisions: {collisions}")

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    for source, destination in zip(sources, destinations):
        source.replace(destination)

    moved_names = {path.name for path in destinations}
    for record in records:
        if record.get("file", "").split("/")[-1] in moved_names and record.get("split") == "train":
            record["split"] = "val"
            record["file"] = f"val/hum/{Path(record['file']).name}"

    temporary_manifest = MANIFEST_PATH.with_suffix(".tmp")
    temporary_manifest.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(MANIFEST_PATH)
    print(f"Moved {len(selected)} generated hard cases from train/hum to val/hum.")


if __name__ == "__main__":
    main()
