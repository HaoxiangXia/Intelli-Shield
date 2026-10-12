"""Perception layer using advisor-trained YOLOv4 Darknet model via OpenCV DNN."""

from __future__ import annotations
import math
import os
from typing import List, Optional, Tuple
import cv2
import numpy as np

from .models import BoundingBox, PerceptionResult

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class YOLODetector:
    """Perception engine supporting advisor-trained YOLOv4 (Darknet) and optional PyTorch weights."""

    # Default advisor-trained classes mapping
    # 0: person, 6: forkTruck, 7: truck, 8: truckHead, 9: smallTruck
    PERSON_CLASS_NAMES = {"person"}
    FORKLIFT_CLASS_NAMES = {"forktruck", "truck", "truckhead", "smalltruck"}

    def __init__(
        self,
        cfg_path: str = "models/yolov4-custom-hebei.cfg",
        weights_path: str = "models/yolov4-custom-hebei_last.weights",
        names_path: str = "models/voc-hebei.names",
        conf_threshold: float = 0.25,
        nms_threshold: float = 0.40,
        input_size: Tuple[int, int] = (608, 608),
        device: str = "cpu",
    ):
        self.cfg_path = cfg_path
        self.weights_path = weights_path
        self.names_path = names_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.input_size = input_size
        self.device = device

        self.net = None
        self.output_layers = []
        self.classes: List[str] = []
        self.ultralytics_model = None

        self._init_detector()

    def _init_detector(self):
        # 1. Darknet YOLOv4 initialization (Default advisor model)
        if os.path.exists(self.cfg_path) and os.path.exists(self.weights_path):
            if os.path.exists(self.names_path):
                with open(self.names_path, "r", encoding="utf-8") as f:
                    self.classes = [line.strip() for line in f if line.strip()]
            else:
                self.classes = ["person", "phone", "vest", "helmet", "belt", "ball", "forkTruck", "truck", "truckHead"]

            self.net = cv2.dnn.readNetFromDarknet(self.cfg_path, self.weights_path)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

            layer_names = self.net.getLayerNames()
            unconnected = self.net.getUnconnectedOutLayers()
            if len(unconnected.shape) == 2:
                self.output_layers = [layer_names[i[0] - 1] for i in unconnected]
            else:
                self.output_layers = [layer_names[i - 1] for i in unconnected]
            print(f"[YOLODetector] Loaded advisor YOLOv4 Darknet: {self.cfg_path} ({len(self.classes)} classes)")
            return

        # 2. Ultralytics PyTorch fallback (if weights_path ends with .pt)
        if YOLO is not None and self.weights_path.endswith(".pt") and os.path.exists(self.weights_path):
            self.ultralytics_model = YOLO(self.weights_path)
            print(f"[YOLODetector] Loaded Ultralytics PyTorch weights: {self.weights_path}")
            return

        print(f"[YOLODetector] Warning: Could not find model files at {self.cfg_path} or {self.weights_path}")

    def detect(self, frame_bgr: np.ndarray, frame_id: int, timestamp: float) -> PerceptionResult:
        result = PerceptionResult(frame_id=frame_id, timestamp=timestamp)

        # Path A: Darknet YOLOv4 OpenCV DNN (Advisor Model)
        if self.net is not None:
            height, width = frame_bgr.shape[:2]
            blob = cv2.dnn.blobFromImage(
                frame_bgr, 1.0 / 255.0, self.input_size, swapRB=True, crop=False
            )
            self.net.setInput(blob)
            outs = self.net.forward(self.output_layers)

            boxes = []
            confidences = []
            class_ids = []

            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = int(np.argmax(scores))
                    confidence = float(scores[class_id])
                    if confidence >= self.conf_threshold:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        x = max(0, min(x, width - 1))
                        y = max(0, min(y, height - 1))
                        w = max(1, min(w, width - x))
                        h = max(1, min(h, height - y))

                        boxes.append([x, y, w, h])
                        confidences.append(confidence)
                        class_ids.append(class_id)

            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)
            if len(indices) > 0:
                for idx in indices.flatten():
                    cid = class_ids[idx]
                    raw_cls_name = self.classes[cid] if cid < len(self.classes) else f"class_{cid}"

                    bbox = BoundingBox(
                        x1=float(boxes[idx][0]),
                        y1=float(boxes[idx][1]),
                        x2=float(boxes[idx][0] + boxes[idx][2]),
                        y2=float(boxes[idx][1] + boxes[idx][3]),
                        confidence=float(confidences[idx]),
                        class_name=raw_cls_name,
                    )

                    # Preserve all detected classes in detections for full video display
                    result.detections.append(bbox)

                    if raw_cls_name == "person":
                        result.pedestrians.append(bbox)
                    elif raw_cls_name == "forkTruck":
                        result.forklifts.append(bbox)
            result.min_distance_px = self._calc_min_distance(result.pedestrians, result.forklifts)
            return result

        # Path B: Ultralytics PyTorch fallback
        if self.ultralytics_model is not None:
            preds = self.ultralytics_model.predict(
                source=frame_bgr,
                conf=self.conf_threshold,
                device=self.device,
                verbose=False,
            )
            if preds and len(preds) > 0 and preds[0].boxes is not None:
                for box in preds[0].boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].tolist()

                    bbox = BoundingBox(
                        x1=xyxy[0],
                        y1=xyxy[1],
                        x2=xyxy[2],
                        y2=xyxy[3],
                        confidence=conf,
                        class_name="person" if cls_id == 0 else "forklift",
                    )
                    if cls_id == 0:
                        result.pedestrians.append(bbox)
                    elif cls_id in {7, 8}:
                        result.forklifts.append(bbox)

            result.min_distance_px = self._calc_min_distance(result.pedestrians, result.forklifts)
            return result

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
