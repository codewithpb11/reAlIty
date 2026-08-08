"""Media-format helpers shared by the GUI and detector."""

from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError

# Register optional Pillow decoders when the matching packages are installed.
# These imports have no effect on machines that do not need those formats.
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass


def load_image(path: str) -> Image.Image:
    """Open a readable image and return a detached RGB copy."""
    with Image.open(path) as image:
        return image.convert("RGB").copy()


def _is_readable_image(path: str) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def _is_readable_video(path: str) -> bool:
    """Check a file by decoding its first frame, not by its filename."""
    capture = cv2.VideoCapture(path)
    try:
        if not capture.isOpened():
            return False
        success, _ = capture.read()
        return success
    finally:
        capture.release()


def detect_media_type(path: str) -> str:
    """Return ``image`` or ``video`` for a locally readable non-PDF file.

    The file chooser deliberately permits every file extension. Actual support
    depends on Pillow for images and OpenCV/FFmpeg codecs for videos, so users
    receive a helpful error instead of a misleading extension-only decision.
    """
    if Path(path).suffix.lower() == ".pdf":
        raise ValueError("PDF documents are not supported. Please select an image or video.")

    if _is_readable_image(path):
        return "image"
    if _is_readable_video(path):
        return "video"

    raise ValueError(
        "This file could not be decoded as an image or video on this computer. "
        "It may use an unsupported or missing codec."
    )
