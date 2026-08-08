"""
video_utils.py
Handles extracting evenly-spaced frames from a video file so they
can be individually classified by the detector.
"""

import cv2


def extract_frames(video_path: str, num_frames: int = 10):
    """
    Extracts up to `num_frames` evenly spaced frames from a video.

    Returns a list of frames as BGR numpy arrays (OpenCV's native format).
    Returns an empty list if the video can't be opened or read.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return []

    # Don't ask for more frames than the video actually has
    num_frames = min(num_frames, total_frames)
    frame_ids = [int(i * total_frames / num_frames) for i in range(num_frames)]

    frames = []
    for frame_id in frame_ids:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        success, frame = cap.read()
        if success:
            frames.append(frame)

    cap.release()
    return frames
