"""Create 60 additional edited-but-human examples for dataset/val/hum.

Only the original human photos already held out in validation are used as
sources. No train image is read, so the resulting validation cases cannot
leak a training source into evaluation.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


PROJECT_DIR = Path(__file__).resolve().parent
VALIDATION_DIR = PROJECT_DIR / "dataset" / "val" / "hum"
MANIFEST_PATH = PROJECT_DIR / "dataset" / "validation_human_hard_cases_manifest.jsonl"
TARGET_COUNT = 60
RANDOM_SEED = 20260801
VARIANTS = ("story_ui", "meme_caption", "collage", "redaction", "markup", "repost")


def open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB").copy()


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def story_ui(image: Image.Image, _: Image.Image, rng: random.Random) -> Image.Image:
    canvas = fit(image, (720, 960))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((25, 28, 695, 39), radius=5, outline=(245, 245, 245), width=3)
    draw.ellipse((36, 53, 70, 87), fill=(240, 240, 240))
    draw.text((82, 62), rng.choice(("weekend", "camera roll", "today")), fill=(245, 245, 245))
    draw.text((38, 912), "Reply to this photo", fill=(245, 245, 245))
    draw.rounded_rectangle((25, 895, 695, 945), radius=18, outline=(245, 245, 245), width=2)
    return canvas


def meme_caption(image: Image.Image, _: Image.Image, rng: random.Random) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    band = max(50, canvas.height // 8)
    draw.rectangle((0, 0, canvas.width, band), fill=(9, 9, 9))
    draw.rectangle((0, canvas.height - band, canvas.width, canvas.height), fill=(9, 9, 9))
    draw.text((max(12, canvas.width // 26), band // 3), rng.choice(("WHEN THE CAMERA OPENS", "NO EDITS, JUST VIBES", "ONE MORE PHOTO")), fill=(255, 255, 255))
    draw.text((max(12, canvas.width // 26), canvas.height - band + band // 3), rng.choice(("…and it actually worked", "saved to favourites", "send this to the group")), fill=(255, 255, 255))
    return canvas


def collage(image: Image.Image, second: Image.Image, _: random.Random) -> Image.Image:
    canvas = Image.new("RGB", (960, 960), (238, 237, 232))
    canvas.paste(fit(image, (430, 760)), (34, 120))
    canvas.paste(fit(second, (430, 760)), (496, 120))
    draw = ImageDraw.Draw(canvas)
    draw.text((36, 48), "A LITTLE PHOTO DUMP", fill=(36, 36, 36))
    draw.text((36, 905), "unfiltered moments", fill=(70, 70, 70))
    return canvas


def redaction(image: Image.Image, _: Image.Image, rng: random.Random) -> Image.Image:
    canvas = image.copy()
    width = rng.randint(max(90, canvas.width // 4), max(130, canvas.width // 2))
    height = rng.randint(max(35, canvas.height // 14), max(55, canvas.height // 8))
    x0 = rng.randint(0, max(0, canvas.width - width))
    y0 = rng.randint(0, max(0, canvas.height - height))
    region = canvas.crop((x0, y0, x0 + width, y0 + height)).filter(ImageFilter.GaussianBlur(15))
    canvas.paste(region, (x0, y0))
    ImageDraw.Draw(canvas).rectangle((x0, y0, x0 + width, y0 + height), fill=(18, 18, 18))
    return canvas


def markup(image: Image.Image, _: Image.Image, rng: random.Random) -> Image.Image:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    colour = rng.choice(((241, 51, 66), (39, 166, 238), (255, 202, 35)))
    cx, cy = rng.randint(canvas.width // 4, canvas.width * 3 // 4), rng.randint(canvas.height // 4, canvas.height * 3 // 4)
    radius = max(35, min(canvas.size) // 6)
    stroke = max(4, min(canvas.size) // 100)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=colour, width=stroke)
    draw.line((30, 35, cx - radius // 2, cy - radius // 2), fill=colour, width=stroke)
    draw.text((36, 42), rng.choice(("look here", "this bit", "lol")), fill=colour)
    return canvas


def repost(image: Image.Image, _: Image.Image, rng: random.Random) -> Image.Image:
    # Resampling and a light colour adjustment imitate a repeatedly shared screenshot.
    small = image.resize((max(80, image.width // 2), max(80, image.height // 2)), Image.Resampling.BILINEAR)
    canvas = small.resize(image.size, Image.Resampling.BILINEAR)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.08)
    draw = ImageDraw.Draw(canvas)
    tag_w, tag_h = max(100, canvas.width // 4), max(35, canvas.height // 12)
    draw.rounded_rectangle((16, 16, 16 + tag_w, 16 + tag_h), radius=9, fill=(247, 247, 247))
    draw.text((28, 16 + tag_h // 3), rng.choice(("repost", "via @friend", "saved")), fill=(25, 25, 25))
    return canvas


RENDERERS = {
    "story_ui": story_ui,
    "meme_caption": meme_caption,
    "collage": collage,
    "redaction": redaction,
    "markup": markup,
    "repost": repost,
}


def main() -> None:
    existing = []
    if MANIFEST_PATH.exists():
        existing = [json.loads(line) for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines() if line]
    remaining = TARGET_COUNT - len(existing)
    if remaining <= 0:
        print("All 60 additional validation hard cases are already present; no files were changed.")
        return

    # The first 120 generated files have the hardcase prefix. All remaining
    # files are the original 20 validation photos held out by the user.
    originals = sorted(
        path for path in VALIDATION_DIR.iterdir()
        if path.is_file() and not path.name.startswith("hardcase_") and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    )
    if len(originals) < 20:
        raise RuntimeError(f"Expected at least 20 original validation photos; found {len(originals)}.")

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(originals)
    selected = [originals[index % len(originals)] for index in range(remaining)]
    variants = [VARIANTS[index % len(VARIANTS)] for index in range(remaining)]
    rng.shuffle(variants)

    with MANIFEST_PATH.open("a", encoding="utf-8") as manifest:
        for number, (source, variant) in enumerate(zip(selected, variants), start=len(existing) + 1):
            image = open_rgb(source)
            second = open_rgb(rng.choice(originals))
            output = RENDERERS[variant](image, second, rng)
            filename = f"val_hardcase_hum_{number:03d}_{variant}.jpg"
            destination = VALIDATION_DIR / filename
            temporary = VALIDATION_DIR / f".{filename}.tmp.jpg"
            output.save(temporary, format="JPEG", quality=92, optimize=True)
            temporary.replace(destination)
            manifest.write(json.dumps({
                "created_by": "create_validation_human_hard_cases.py",
                "label": "hum",
                "split": "val",
                "file": f"val/hum/{filename}",
                "source": source.name,
                "variant": variant,
                "note": "Derived only from an original human validation photo; no training image used.",
            }) + "\n")
            if number % 10 == 0 or number == TARGET_COUNT:
                print(f"Created {number}/{TARGET_COUNT} additional validation hard cases")


if __name__ == "__main__":
    main()
