"""
check_dataset_counts.py

Quick sanity check: counts how many images are actually sitting in each
dataset folder right now. Useful after all the adding/removing you've done,
to see exactly where things stand before zipping and training.

Run from the project folder:
    python check_dataset_counts.py
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "dataset"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def count_images(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS)


def main() -> None:
    print(f"{'Folder':<20} {'Count':>8}")
    print("-" * 30)
    total = 0
    for split in ("train", "val"):
        for label in ("ai", "hum"):
            folder = DATASET_DIR / split / label
            count = count_images(folder)
            total += count
            print(f"{split}/{label:<15} {count:>8}")
    print("-" * 30)
    print(f"{'TOTAL':<20} {total:>8}")


if __name__ == "__main__":
    main()
