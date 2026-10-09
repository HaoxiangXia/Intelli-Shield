"""Perception layer using YOLO for detecting pedestrians and industrial vehicles."""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
import numpy as np

from .models import BoundingBox, PerceptionResult

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class YOLODetector:
    """YOLO26 nano perception engine for CCTV streams."""

    # Standard COCO class mappings
    # class 0: person, class 7: truck (often used for forklifts in default COCO)
    PERSON_CLASS_IDS = {0}
    FORKLIFT_CLASS_IDS = {7, 8}  # truck, custom industrial vehicles

    def __init__(
        self,
        model_path: str = "yolo26n.pt",
        conf_threshold: float = 0.35,
        device: str = "cpu",
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.device = device
        self.model = None

        if YOLO is not None:
            self.model = YOLO(model_path)

    def detect(self, frame_bgr: np.ndarray, frame_id: int, timestamp: float) -> PerceptionResult:
        result = PerceptionResult(frame_id=frame_id, timestamp=timestamp)

        if self.model is None:
            return result

        preds = self.model.predict(
            source=frame_bgr,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )

        if not preds or len(preds) == 0:
            return result

        boxes = preds[0].boxes
        if boxes is None:
            return result

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].tolist()

            bbox = BoundingBox(
                x1=xyxy[0],
                y1=xyxy[1],
                x2=xyxy[2],
                y2=xyxy[3],
                confidence=conf,
                class_name="person" if cls_id in self.PERSON_CLASS_IDS else "forklift",
            )

            if cls_id in self.PERSON_CLASS_IDS:
                result.pedestrians.append(bbox)
            elif cls_id in self.FORKLIFT_CLASS_IDS or cls_id == 7:
                result.forklifts.append(bbox)

        result.min_distance_px = self._calc_min_distance(result.pedestrians, result.forklifts)
        return result

    @staticmethod
    def _calc_min_distance(
        peds: List[BoundingBox], forks: List[BoundingBox]
    ) -> Optional[float]:
        if not peds or not forks:
            return None

        min_d = float("inf")
        for p in peds:
            pc_x = (p.x1 + p.x2) / 2.0
            pc_y = (p.y1 + p.y2) / 2.0
            for f in forks:
                fc_x = (f.x1 + f.x2) / 2.0
                fc_y = (f.y1 + f.y2) / 2.0
                dist = math.hypot(pc_x - fc_x, pc_y - fc_y)
                if dist < min_d:
                    min_d = dist
        return min_d if min_d != float("inf") else None
