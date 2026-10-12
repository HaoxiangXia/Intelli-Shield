#!/usr/bin/env python3
"""
YOLOv4 Inference Script for Darknet Weights & Config.
Performs object detection using OpenCV DNN module.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Tuple

import cv2
import numpy as np


# Distinct color palette for classes
CLASS_COLORS = [
    (0, 255, 128),    # 0: person (Green)
    (255, 165, 0),    # 1: cell phone (Orange)
    (0, 215, 255),    # 2: vest (Gold/Yellow)
    (255, 255, 0),    # 3: Helmet (Cyan)
    (203, 192, 255),  # 4: SafetyBelt (Pink)
    (255, 0, 255),    # 5: ball (Magenta)
    (0, 100, 255),    # 6: forkTruck (Bright Orange-Red)
    (255, 50, 50),    # 7: truck (Blue)
    (180, 105, 255),  # 8: truckHead (Purple)
    (50, 205, 50),    # 9: smallTruck (Lime)
    (128, 128, 128),  # 10: blackHelmet (Gray)
    (0, 140, 255),    # 11: workwear (Dark Orange)
    (255, 191, 0),    # 12: face (Deep Sky Blue)
    (147, 20, 255),   # 13: head (Pink-Red)
]


def load_classes(names_path: str) -> List[str]:
    with open(names_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_model(cfg_path: str, weights_path: str):
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Weights file not found: {weights_path}")

    net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    layer_names = net.getLayerNames()
    unconnected = net.getUnconnectedOutLayers()
    if len(unconnected.shape) == 2:
        output_layers = [layer_names[i[0] - 1] for i in unconnected]
    else:
        output_layers = [layer_names[i - 1] for i in unconnected]

    return net, output_layers


def infer_image(
    net,
    output_layers: List[str],
    classes: List[str],
    image_path: str,
    conf_thresh: float = 0.30,
    nms_thresh: float = 0.45,
    input_size: Tuple[int, int] = (608, 608),
) -> Tuple[np.ndarray, List[dict], float]:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image from {image_path}")

    height, width = img.shape[:2]
    blob = cv2.dnn.blobFromImage(
        img, 1.0 / 255.0, input_size, swapRB=True, crop=False
    )
    net.setInput(blob)

    start_time = time.time()
    outs = net.forward(output_layers)
    infer_time_ms = (time.time() - start_time) * 1000.0

    boxes = []
    confidences = []
    class_ids = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])
            if confidence >= conf_thresh:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # Clamp to image boundaries
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))
                w = max(1, min(w, width - x))
                h = max(1, min(h, height - y))

                boxes.append([x, y, w, h])
                confidences.append(confidence)
                class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_thresh, nms_thresh)

    results = []
    if len(indices) > 0:
        for idx in indices.flatten():
            results.append({
                "class_id": class_ids[idx],
                "class_name": classes[class_ids[idx]] if class_ids[idx] < len(classes) else f"class_{class_ids[idx]}",
                "confidence": confidences[idx],
                "box": boxes[idx],  # [x, y, w, h]
            })

    # Sort results by confidence descending
    results.sort(key=lambda item: item["confidence"], reverse=True)
    return img, results, infer_time_ms


def draw_detections(img: np.ndarray, detections: List[dict]) -> np.ndarray:
    annotated = img.copy()
    h_img, w_img = annotated.shape[:2]

    # Calculate scale factor for font and box lines based on image resolution
    scale = max(0.5, min(w_img, h_img) / 1000.0)
    thickness = max(2, int(2 * scale))
    font_scale = max(0.45, 0.5 * scale)

    for det in detections:
        x, y, w, h = det["box"]
        cid = det["class_id"]
        cname = det["class_name"]
        conf = det["confidence"]
        color = CLASS_COLORS[cid % len(CLASS_COLORS)]

        # Draw bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)

        # Label formatting
        label = f"{cname} {conf:.1%}"
        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
        )

        # Label background pill
        label_y1 = max(0, y - text_h - baseline - 4)
        label_y2 = y
        label_x2 = min(w_img, x + text_w + 6)
        cv2.rectangle(
            annotated,
            (x, label_y1),
            (label_x2, label_y2),
            color,
            -1
        )

        # Text in contrasting color (black or dark)
        cv2.putText(
            annotated,
            label,
            (x + 3, label_y2 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 0, 0),
            thickness=max(1, int(1 * scale)),
            lineType=cv2.LINE_AA,
        )

    # Add HUD header info
    hud_text = f"YOLOv4 Inference | Detections: {len(detections)}"
    cv2.putText(
        annotated,
        hud_text,
        (20, int(35 * scale)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale * 1.2,
        (0, 255, 255),
        thickness=max(2, int(2 * scale)),
        lineType=cv2.LINE_AA,
    )

    return annotated


def main():
    parser = argparse.ArgumentParser(description="Run YOLOv4 inference on images")
    parser.add_argument(
        "--image",
        type=str,
        default="samples/cctv/raw_images/220121shenyang1509.png",
        help="Path to input image",
    )
    parser.add_argument(
        "--cfg",
        type=str,
        default="models/yolov4-custom-hebei.cfg",
        help="Path to .cfg file",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="models/yolov4-custom-hebei_last.weights",
        help="Path to .weights file",
    )
    parser.add_argument(
        "--names",
        type=str,
        default="models/voc-hebei.names",
        help="Path to .names file",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.30,
        help="Confidence threshold",
    )
    parser.add_argument(
        "--nms",
        type=float,
        default=0.45,
        help="NMS threshold",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="samples/cctv/keyframes/yolov4_result.png",
        help="Path to output annotated image",
    )

    args = parser.parse_args()

    print(f"[*] Loading classes from {args.names}...")
    classes = load_classes(args.names)
    print(f"[+] Loaded {len(classes)} classes: {classes}")

    print(f"[*] Loading YOLOv4 network from {args.cfg} & {args.weights}...")
    net, output_layers = load_model(args.cfg, args.weights)
    print(f"[+] Output layers: {output_layers}")

    print(f"[*] Running inference on {args.image} (conf={args.conf}, nms={args.nms})...")
    img, detections, infer_time = infer_image(
        net, output_layers, classes, args.image, conf_thresh=args.conf, nms_thresh=args.nms
    )

    print(f"\n==================== YOLOv4 Inference Report ====================")
    print(f"Image Resolution : {img.shape[1]} x {img.shape[0]}")
    print(f"Inference Time   : {infer_time:.2f} ms")
    print(f"Total Detections : {len(detections)}")
    print(f"-----------------------------------------------------------------")
    for i, det in enumerate(detections, 1):
        x, y, w, h = det['box']
        print(
            f"  {i:2d}. [{det['class_name']:<12}] "
            f"Confidence: {det['confidence']:6.1%} | "
            f"BBox: [x={x:4d}, y={y:4d}, w={w:4d}, h={h:4d}]"
        )
    print(f"=================================================================\n")

    annotated = draw_detections(img, detections)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    cv2.imwrite(args.output, annotated)
    print(f"[+] Saved annotated visualization to: {args.output}")


if __name__ == "__main__":
    main()
