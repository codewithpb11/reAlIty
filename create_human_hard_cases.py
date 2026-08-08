"""Create labelled *human* hard cases for reAlIty's image training set.

The base detector can mistake a real photograph for AI when it has captions,
dates, arrows, a highlighted area, redaction, or a collage layout.  This tool
creates a small, balanced set of those edits from the traceable human photos
already in ``dataset/train/hum``.  Originals are never changed.

It deliberately does not write into validation: validation should contain
independent, naturally occurring examples rather than synthetic copies of
training-style edits.

Run from the project folder:
    python create_human_hard_cases.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "dataset" / "train" / "hum"
MANIFEST_PATH = PROJECT_DIR / "dataset" / "derived_human_cases_manifest.jsonl"
TARGET_COUNT = 120
RANDOM_SEED = 20260801
CAPTIONS = ("WEEKEND", "DAY 12", "BEFORE", "PHOTO DUMP", "MEMORIES", "ARCHIVE")
VARIANTS = ("caption", "timestamp", "annotation", "redaction", "collage", "note")


def _load_manifest() -> tuple[int, set[str]]:
    count, sources = 0, set()
    if not MANIFEST_PATH.exists():
        return count, sources
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("created_by") == "create_human_hard_cases.py":
            count += 1
            if isinstance(item.get("source"), str):
                sources.add(item["source"])
    return count, sources


def _open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB").copy()


def _fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _caption(image: Image.Image, rng: random.Random) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    band = max(42, result.height // 10)
    y0 = result.height - band if rng.random() < 0.7 else 0
    draw.rectangle((0, y0, result.width, y0 + band), fill=(12, 12, 12))
    text = rng.choice(CAPTIONS)
    draw.text((max(12, result.width // 28), y0 + band // 3), text, fill=(245, 245, 245))
    return result


def _timestamp(image: Image.Image, rng: random.Random) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    label = rng.choice(("2024.08.17  18:42", "12/03/2025  09:16", "REC  00:14:28"))
    pad = max(10, result.width // 50)
    box_width = max(135, len(label) * 7) + pad * 2
    box_height = max(30, result.height // 16)
    x0 = result.width - box_width - pad
    y0 = result.height - box_height - pad
    draw.rounded_rectangle((x0, y0, x0 + box_width, y0 + box_height), radius=7, fill=(0, 0, 0))
    draw.text((x0 + pad, y0 + box_height // 3), label, fill=(235, 235, 235))
    return result


def _annotation(image: Image.Image, rng: random.Random) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    colour = rng.choice(((235, 48, 48), (255, 214, 36), (25, 170, 255)))
    cx, cy = rng.randint(result.width // 4, result.width * 3 // 4), rng.randint(result.height // 4, result.height * 3 // 4)
    radius = max(30, min(result.size) // 7)
    width = max(4, min(result.size) // 90)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=colour, width=width)
    start = (max(0, cx - radius * 2), max(0, cy - radius * 2))
    end = (cx - radius // 2, cy - radius // 2)
    draw.line((start, end), fill=colour, width=width)
    draw.polygon((end, (end[0] - width * 3, end[1]), (end[0], end[1] - width * 3)), fill=colour)
    return result


def _redaction(image: Image.Image, rng: random.Random) -> Image.Image:
    result = image.copy()
    width = rng.randint(max(80, result.width // 5), max(100, result.width // 2))
    height = rng.randint(max(28, result.height // 14), max(45, result.height // 8))
    x0 = rng.randint(0, max(0, result.width - width))
    y0 = rng.randint(0, max(0, result.height - height))
    blurred = result.crop((x0, y0, x0 + width, y0 + height)).filter(ImageFilter.GaussianBlur(radius=12))
    result.paste(blurred, (x0, y0))
    draw = ImageDraw.Draw(result)
    draw.rectangle((x0, y0, x0 + width, y0 + height), outline=(25, 25, 25), width=max(3, result.width // 180))
    return result


def _collage(image: Image.Image, second: Image.Image) -> Image.Image:
    size = (960, 960)
    canvas = Image.new("RGB", size, "#f6f6f6")
    tile = (452, 878)
    canvas.paste(_fit(image, tile), (28, 41))
    canvas.paste(_fit(second, tile), (480, 41))
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 13), "PHOTO NOTES", fill=(30, 30, 30))
    draw.text((30, 925), "two moments, one day", fill=(60, 60, 60))
    return canvas


def _note(image: Image.Image, rng: random.Random) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    side = max(80, min(result.size) // 5)
    x0 = result.width - side - 18
    y0 = 18
    colour = rng.choice(((255, 237, 126), (174, 224, 255), (255, 187, 187)))
    draw.rectangle((x0, y0, x0 + side, y0 + side), fill=colour)
    draw.text((x0 + 10, y0 + side // 3), rng.choice(("save", "wow", "note")), fill=(35, 35, 35))
    return result


def _make_variant(image: Image.Image, variant: str, second: Image.Image, rng: random.Random) -> Image.Image:
    if variant == "caption":
        return _caption(image, rng)
    if variant == "timestamp":
        return _timestamp(image, rng)
    if variant == "annotation":
        return _annotation(image, rng)
    if variant == "redaction":
        return _redaction(image, rng)
    if variant == "collage":
        return _collage(image, second)
    return _note(image, rng)


def main() -> None:
    already_created, used_sources = _load_manifest()
    remaining = max(0, TARGET_COUNT - already_created)
    if not remaining:
        print(f"{TARGET_COUNT} human hard cases are already present; no files were changed.")
        return

    # corpus_hum files have a documented MIT source, unlike personal files that
    # may have been placed in this folder by hand.
    candidates = sorted(SOURCE_DIR.glob("corpus_hum_*.jpg"))
    candidates = [path for path in candidates if path.name not in used_sources]
    if len(candidates) < remaining:
        raise RuntimeError(f"Need {remaining} unused source photos but found {len(candidates)}.")

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(candidates)
    chosen = candidates[:remaining]
    variants = [VARIANTS[index % len(VARIANTS)] for index in range(remaining)]
    rng.shuffle(variants)

    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for index, (source, variant) in enumerate(zip(chosen, variants), start=already_created + 1):
            image = _open_rgb(source)
            second = _open_rgb(rng.choice(candidates))
            result = _make_variant(image, variant, second, rng)
            filename = f"hardcase_hum_{index:03d}_{variant}.jpg"
            output = SOURCE_DIR / filename
            temporary = SOURCE_DIR / f".{filename}.tmp.jpg"
            result.save(temporary, format="JPEG", quality=95, optimize=True)
            temporary.replace(output)
            manifest.write(json.dumps({
                "created_by": "create_human_hard_cases.py",
                "label": "hum",
                "split": "train",
                "file": f"train/hum/{filename}",
                "source": source.name,
                "variant": variant,
                "source_license": "mit (derived from Parveshiiii/AI-vs-Real)",
            }) + "\n")
            if index % 20 == 0 or index == TARGET_COUNT:
                print(f"Created {index}/{TARGET_COUNT} human hard cases")

    print("Done. Originals and validation files were left unchanged.")


if __name__ == "__main__":
    main()
