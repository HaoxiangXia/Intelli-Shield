"""Synthetic high-mounted CCTV video generator for pipeline and probe validation."""

from __future__ import annotations
import math
import os
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def generate_cctv_video(output_path: str = "samples/cctv/videos/demo_forklift.mp4", duration_sec: int = 8, fps: int = 15):
    if cv2 is None:
        print("cv2 not available; skipping video synthesis.")
        return

    width, height = 960, 540
    total_frames = duration_sec * fps
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Pedestrian stationary at (600, 320)
    ped_x, ped_y = 600, 320

    # Forklift moving from left (150, 320) to right (680, 320)
    fork_start_x = 120
    fork_end_x = 650

    for f in range(total_frames):
        # Industrial warehouse floor (dark gray concrete)
        frame = np.full((height, width, 3), (60, 60, 65), dtype=np.uint8)

        # Draw warehouse yellow safety lanes
        cv2.line(frame, (50, 240), (900, 240), (0, 215, 255), 4)
        cv2.line(frame, (50, 420), (900, 420), (0, 215, 255), 4)

        # Overhead CCTV camera label
        cv2.putText(frame, "CAM-04 [WAREHOUSE-ZONE-B] OVERHEAD 30FPS", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(frame, f"TIMESTAMP: 2026-10-09 14:23:{f//fps:02d}.{int((f%fps)*(1000/fps)):03d}", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 160), 1)

        # Worker (Person) standing in safety margin
        # Head
        cv2.circle(frame, (ped_x, ped_y - 25), 10, (220, 180, 150), -1)
        # Body (blue safety uniform)
        cv2.rectangle(frame, (ped_x - 12, ped_y - 15), (ped_x + 12, ped_y + 20), (180, 100, 30), -1)
        # Legs
        cv2.line(frame, (ped_x - 6, ped_y + 20), (ped_x - 6, ped_y + 40), (50, 50, 50), 4)
        cv2.line(frame, (ped_x + 6, ped_y + 20), (ped_x + 6, ped_y + 40), (50, 50, 50), 4)
        cv2.putText(frame, "Worker", (ped_x - 20, ped_y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Forklift position interpolation
        progress = f / total_frames
        curr_fork_x = int(fork_start_x + (fork_end_x - fork_start_x) * progress)
        curr_fork_y = ped_y

        # Forklift Body (Orange/Yellow industrial vehicle)
        cv2.rectangle(frame, (curr_fork_x - 45, curr_fork_y - 25), (curr_fork_x + 40, curr_fork_y + 25), (20, 140, 240), -1)
        # Forklift cabin/mast
        cv2.rectangle(frame, (curr_fork_x - 10, curr_fork_y - 45), (curr_fork_x + 20, curr_fork_y - 25), (40, 40, 40), -1)
        # Forks extending forward
        cv2.line(frame, (curr_fork_x + 40, curr_fork_y + 10), (curr_fork_x + 75, curr_fork_y + 10), (100, 100, 100), 5)
        cv2.line(frame, (curr_fork_x + 40, curr_fork_y - 10), (curr_fork_x + 75, curr_fork_y - 10), (100, 100, 100), 5)
        cv2.putText(frame, "Forklift", (curr_fork_x - 25, curr_fork_y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        # Distance line
        dist = abs(ped_x - curr_fork_x)
        color = (0, 255, 0) if dist > 250 else ((0, 255, 255) if dist > 120 else (0, 0, 255))
        cv2.line(frame, (curr_fork_x + 40, curr_fork_y), (ped_x - 12, ped_y), color, 1, cv2.LINE_AA)

        writer.write(frame)

    writer.release()
    print(f"Generated synthetic CCTV video: {output_path} ({total_frames} frames, {width}x{height})")


if __name__ == "__main__":
    generate_cctv_video()
