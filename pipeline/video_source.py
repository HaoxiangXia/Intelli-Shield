"""Video feed intake and pacing controller for high-mounted CCTV feeds."""

from __future__ import annotations
import os
import time
from typing import Generator, Optional, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


class VideoSource:
    """Reads local CCTV MP4/AVI or RTSP stream, with loop and FPS control."""

    def __init__(
        self,
        video_path: str,
        target_fps: float = 10.0,
        loop: bool = True,
    ):
        self.video_path = video_path
        self.target_fps = target_fps
        self.loop = loop
        self.frame_interval = 1.0 / max(target_fps, 0.1)

    def frames(self) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        if cv2 is None:
            raise RuntimeError(
                "OpenCV (cv2) is required to read video sources. Run 'uv sync' or 'uv pip install \"opencv-python>=4.8,<5.0\"'"
            )

        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found at: {self.video_path}")

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video at: {self.video_path}")

        frame_id = 0
        last_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    if self.loop:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break

                frame_id += 1
                now = time.time()
                elapsed = now - last_time
                if elapsed < self.frame_interval:
                    time.sleep(self.frame_interval - elapsed)
                last_time = time.time()

                yield frame_id, now, frame
        finally:
            cap.release()
