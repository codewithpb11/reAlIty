"""
detector.py
Core AI-detection logic for reAlIty. Loads the model once (lazily, on first
use) and exposes simple functions the GUI can call for images and videos.

Also includes a heuristic (non-OCR) check for heavy text/graphic overlays
(captions, arrows, circles, redaction marks) - the classifier model wasn't
trained to tell "edited real photo with graphics on it" apart from "AI
image," so instead of silently trusting a possibly-skewed score, we flag
when this content is present so the app can be upfront about it.
"""

import statistics

import cv2
import numpy as np
from PIL import Image
import torch
from transformers import AutoImageProcessor, SiglipForImageClassification

from media_utils import load_image
from video_utils import extract_frames

MODEL_ID = "pb11-x/reality-detector-model"

_processor = None
_model = None


def _load_model():
    global _processor, _model
    if _model is None:
        _processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        _model = SiglipForImageClassification.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )
        _model.eval()
        torch.set_num_threads(1)
    return _processor, _model


def _check_overlay_bgr(frame_bgr, sat_thresh=160, val_thresh=130,
                        min_vivid_fraction=0.003, edge_density_thresh=0.15):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    s, v = hsv[:, :, 1], hsv[:, :, 2]
    vivid_mask = ((s > sat_thresh) & (v > val_thresh)).astype(np.uint8)

    vivid_fraction = float(np.count_nonzero(vivid_mask)) / vivid_mask.size
    if vivid_fraction < min_vivid_fraction:
        return False, round(vivid_fraction * 100, 2)

    dilated = cv2.dilate(vivid_mask, np.ones((5, 5), np.uint8), iterations=1)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    edges_in_region = cv2.bitwise_and(edges, edges, mask=dilated)

    region_area = np.count_nonzero(dilated)
    edge_density = (
        float(np.count_nonzero(edges_in_region)) / region_area if region_area else 0.0
    )

    return edge_density > edge_density_thresh, round(vivid_fraction * 100, 2)


def detect_image_from_pil(image: Image.Image) -> dict:
    processor, model = _load_model()
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        probs = torch.softmax(model(**inputs).logits, dim=1)[0]
    labels = model.config.id2label
    return {labels[i]: round(probs[i].item() * 100, 2) for i in range(len(labels))}


def detect_image(image_path: str) -> dict:
    image = load_image(image_path)
    result = detect_image_from_pil(image)

    frame_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    overlay_detected, overlay_pct = _check_overlay_bgr(frame_bgr)
    result["overlay_detected"] = overlay_detected
    result["overlay_pct"] = overlay_pct
    return result


def detect_video(video_path: str, num_frames: int = 10, progress_callback=None) -> dict:
    frames = extract_frames(video_path, num_frames)
    if not frames:
        return {"error": "Could not read this video file."}

    all_scores = []
    overlay_flags = []
    overlay_pcts = []

    for i, frame in enumerate(frames):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        all_scores.append(detect_image_from_pil(image))

        flagged, pct = _check_overlay_bgr(frame)
        overlay_flags.append(flagged)
        overlay_pcts.append(pct)

        if progress_callback:
            progress_callback(i + 1, len(frames))

    labels = all_scores[0].keys()
    result = {
        label: round(statistics.median([s[label] for s in all_scores]), 2)
        for label in labels
    }

    result["overlay_detected"] = (sum(overlay_flags) / len(overlay_flags)) >= 0.3
    result["overlay_pct"] = round(sum(overlay_pcts) / len(overlay_pcts), 2)
    return result
