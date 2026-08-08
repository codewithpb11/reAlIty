"""Extract 1,000 human-made CGI frames for reAlIty's human training class.

Sources are Blender Open Movies, not AI-generated content.  Frames are sampled
widely across four different films and recorded with their source and licence.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import requests


ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "dataset" / "train" / "hum"
SOURCE_DIR = ROOT / "dataset" / ".cg_sources"
MANIFEST = ROOT / "dataset" / "blender_cg_human_manifest.jsonl"
FRAMES_PER_FILM = 250

SOURCES = [
    ("big_buck_bunny", "https://archive.org/download/BigBuckBunny_328/BigBuckBunny_512kb.mp4", "CC BY 3.0"),
    ("sintel", "https://archive.org/download/Sintel/sintel-2048-stereo_512kb.mp4", "CC BY 3.0"),
    ("elephants_dream", "https://archive.org/download/ElephantsDream/ed_hd_512kb.mp4", "CC BY 2.5"),
    ("spring", "https://archive.org/download/spring_blenderopenmovie/Spring%20-%20Blender%20Open%20Movie%20-%20YouTube.mp4", "CC BY 4.0"),
]


def download(name: str, url: str) -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    output = SOURCE_DIR / f"{name}.mp4"
    if output.exists() and output.stat().st_size > 1_000_000:
        return output
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with output.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return output


def extract(name: str, video_path: Path, url: str, license_name: str) -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        raise RuntimeError(f"Could not read frames from {video_path.name}")
    positions = [int(total * (0.04 + 0.92 * index / (FRAMES_PER_FILM - 1))) for index in range(FRAMES_PER_FILM)]
    saved = 0
    with MANIFEST.open("a", encoding="utf-8") as manifest:
        for frame_number in positions:
            output = DESTINATION / f"blender_cg_{name}_{frame_number:07d}.jpg"
            if output.exists():
                saved += 1
                continue
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ok, frame = capture.read()
            if not ok or frame is None or frame.std() < 8 or frame.mean() < 8:
                continue
            frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
            if not cv2.imwrite(str(output), frame, [cv2.IMWRITE_JPEG_QUALITY, 94]):
                continue
            manifest.write(json.dumps({
                "acquired_by": "extract_blender_cg_human_frames.py",
                "source": name,
                "source_url": url,
                "license": license_name,
                "frame_number": frame_number,
                "split": "train",
                "label": "hum",
                "file": str(output.relative_to(ROOT / "dataset")).replace("\\", "/"),
            }) + "\n")
            manifest.flush()
            saved += 1
    capture.release()
    if saved < FRAMES_PER_FILM:
        raise RuntimeError(f"{name}: saved only {saved}/{FRAMES_PER_FILM} suitable frames")
    return saved


def main() -> None:
    total = 0
    for name, url, license_name in SOURCES:
        print(f"Downloading {name}...", flush=True)
        path = download(name, url)
        total += extract(name, path, url, license_name)
        print(f"Extracted {total}/1000 frames", flush=True)
    print("Finished: 1,000 human-made CGI frames saved to dataset/train/hum.", flush=True)


if __name__ == "__main__":
    main()
