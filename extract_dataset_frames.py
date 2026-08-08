"""
extract_dataset_frames.py

Pulls sample frames out of a folder of videos and drops them straight into
one of your dataset folders (e.g. dataset/train/ai or dataset/train/hum)
as individual .jpg files, ready for fine-tuning. Reuses the same
extract_frames() function from video_utils.py that your app already uses.

Usage:
    python extract_dataset_frames.py <source_video_folder> <destination_folder> [frames_per_video]

Examples:
    python extract_dataset_frames.py my_ai_videos   dataset/train/ai   6
    python extract_dataset_frames.py my_real_videos dataset/train/hum 6

IMPORTANT - avoiding data leakage:
Frames from the SAME video look very similar to each other. If some frames
of one video end up in train/ and others end up in val/, the model may
"cheat" by half-recognizing that exact video rather than truly learning to
generalize - which makes your val accuracy look better than it really is.

So: decide which whole VIDEOS go to train vs. val BEFORE running this
script, keep them in separate source folders, then run this script twice -
once per destination - rather than splitting individual extracted frames
afterward.

Also: keep frames-per-video modest (5-8 is plenty). You want frames from
MANY different videos, not many near-duplicate frames from a few videos.
"""

import sys
import os
import cv2

from video_utils import extract_frames

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov")


def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_dataset_frames.py <source_folder> <destination_folder> [frames_per_video]")
        sys.exit(1)

    source_folder = sys.argv[1]
    dest_folder = sys.argv[2]
    frames_per_video = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    if not os.path.isdir(source_folder):
        print(f"Source folder not found: {source_folder}")
        sys.exit(1)

    os.makedirs(dest_folder, exist_ok=True)

    videos = sorted(f for f in os.listdir(source_folder) if f.lower().endswith(VIDEO_EXTENSIONS))
    if not videos:
        print(f"No video files (.mp4/.avi/.mov) found in {source_folder}")
        return

    total_saved = 0
    for video_name in videos:
        video_path = os.path.join(source_folder, video_name)
        frames = extract_frames(video_path, num_frames=frames_per_video)

        if not frames:
            print(f"{video_name}: could not read this video, skipping")
            continue

        base_name = os.path.splitext(video_name)[0]
        for i, frame in enumerate(frames):
            out_path = os.path.join(dest_folder, f"{base_name}_frame{i}.jpg")
            cv2.imwrite(out_path, frame)
            total_saved += 1

        print(f"{video_name}: saved {len(frames)} frames")

    print(f"\nDone. Saved {total_saved} frames total into {dest_folder}")


if __name__ == "__main__":
    main()
