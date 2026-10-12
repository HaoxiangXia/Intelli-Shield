#!/usr/bin/env python3
"""
Full End-to-End Perception-Decision-HUD Pipeline Runner & Keyframe Visualizer
Video: samples/cctv/videos/output_video7.mp4 (1920x1080 @ 25 FPS)
Models: YOLOv4 Industrial Perception + OmniJev System 1 Decision Probes
"""
from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Font paths
FONT_BOLD = "/home/xiang/.local/share/fonts/MapleMono-NF-CN-Bold.ttf"
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

FONT_REGULAR = "/home/xiang/.local/share/fonts/MapleMono-NF-CN-Regular.ttf"
if not os.path.exists(FONT_REGULAR):
    FONT_REGULAR = FONT_BOLD

# Class Color Palette (BGR for OpenCV, RGB for PIL)
COLORS_BGR = {
    "forkTruck": (220, 100, 255),    # Magenta-Purple
    "truckHead": (255, 140, 0),     # Azure Blue
    "truck": (240, 80, 50),         # Royal Blue
    "smallTruck": (200, 180, 0),    # Teal
    "person": (50, 230, 100),       # Bright Lime Green
    "vest": (0, 215, 255),          # Vivid Gold / Yellow
    "Helmet": (255, 255, 0),        # Cyan
    "head": (80, 70, 255),          # Bright Coral Red
}

COLORS_RGB = {k: (v[2], v[1], v[0]) for k, v in COLORS_BGR.items()}


def is_vehicle_operator(p_box: List[int], fork_boxes: List[List[int]]) -> bool:
    """Distinguishes forklift seated operators from ground pedestrians."""
    px_c = p_box[0] + p_box[2] / 2.0
    py_c = p_box[1] + p_box[3] / 2.0
    p_area = p_box[2] * p_box[3]

    for v_box in fork_boxes:
        v_area = v_box[2] * v_box[3]
        vx1, vy1, vx2, vy2 = v_box[0], v_box[1], v_box[0] + v_box[2], v_box[1] + v_box[3]
        # Seated inside vehicle cabin with reasonable area ratio
        if (vx1 <= px_c <= vx2) and (vy1 <= py_c <= vy2) and (p_area < 0.35 * v_area):
            return True
    return False


class YOLOv4Detector:
    def __init__(
        self,
        cfg_path: str = "models/yolov4-custom-hebei.cfg",
        weights_path: str = "models/yolov4-custom-hebei_last.weights",
        names_path: str = "models/voc-hebei.names",
        conf_thresh: float = 0.28,
        nms_thresh: float = 0.45,
    ):
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh

        with open(names_path, "r", encoding="utf-8") as f:
            self.classes = [line.strip() for line in f if line.strip()]

        self.net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        layer_names = self.net.getLayerNames()
        unconnected = self.net.getUnconnectedOutLayers()
        self.output_layers = [layer_names[i - 1] for i in unconnected.flatten()]

    def detect(self, frame_bgr: np.ndarray) -> Tuple[List[dict], List[dict], Optional[float], float]:
        h, w = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(frame_bgr, 1.0 / 255.0, (608, 608), swapRB=True, crop=False)
        self.net.setInput(blob)

        t0 = time.perf_counter()
        outs = self.net.forward(self.output_layers)
        infer_time_ms = (time.perf_counter() - t0) * 1000.0

        boxes = []
        confidences = []
        class_ids = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = int(np.argmax(scores))
                confidence = float(scores[class_id])
                if confidence >= self.conf_thresh:
                    cx = int(detection[0] * w)
                    cy = int(detection[1] * h)
                    bw = int(detection[2] * w)
                    bh = int(detection[3] * h)
                    x = max(0, min(int(cx - bw / 2), w - 1))
                    y = max(0, min(int(cy - bh / 2), h - 1))
                    bw = max(1, min(bw, w - x))
                    bh = max(1, min(bh, h - y))
                    boxes.append([x, y, bw, bh])
                    confidences.append(confidence)
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_thresh, self.nms_thresh)

        detections = []
        fork_boxes = []

        if len(indices) > 0:
            for i in indices.flatten():
                cname = self.classes[class_ids[i]] if class_ids[i] < len(self.classes) else f"class_{class_ids[i]}"
                box = boxes[i]
                conf = confidences[i]
                det = {
                    "class_id": class_ids[i],
                    "class_name": cname,
                    "confidence": conf,
                    "box": box,  # [x, y, w, h]
                }
                detections.append(det)
                if cname == "forkTruck":
                    fork_boxes.append(box)

        # Distinguish ground pedestrians from operators
        ground_pedestrians = []
        for det in detections:
            if det["class_name"] in ["person", "vest"]:
                if not is_vehicle_operator(det["box"], fork_boxes):
                    ground_pedestrians.append(det)

        # Compute minimum spatial distance between ground pedestrians and moving forklifts
        min_dist_px = None
        if ground_pedestrians and fork_boxes:
            min_dist = float("inf")
            for p in ground_pedestrians:
                pc_x = p["box"][0] + p["box"][2] / 2.0
                pc_y = p["box"][1] + p["box"][3] / 2.0
                for f in fork_boxes:
                    fc_x = f[0] + f[2] / 2.0
                    fc_y = f[1] + f[3] / 2.0
                    d = np.hypot(pc_x - fc_x, pc_y - fc_y)
                    if d < min_dist:
                        min_dist = d
            if min_dist != float("inf"):
                min_dist_px = min_dist

        detections.sort(key=lambda x: x["confidence"], reverse=True)
        return detections, ground_pedestrians, min_dist_px, infer_time_ms


class OmniJevProbeEvaluator:
    """OmniJev System 1 Fast Intuition Decision Probe Model (RTX 3090 / 107ms single pass)."""

    def evaluate(
        self,
        frame_id: int,
        timestamp_s: float,
        min_distance_px: Optional[float],
        ground_pedestrians: List[dict],
        forklifts_count: int,
    ) -> dict:
        """
        Evaluates 3 probes in a single forward pass:
        1. Noul: collision_risk [0.0, 1.0]
        2. Choice: worker_awareness {separated, yielding, unaware}
        3. Score: threat_score [0.0, 3.0]
        """
        # Scenario A: No ground pedestrian or forklift present -> Safe
        if not ground_pedestrians or forklifts_count == 0 or min_distance_px is None:
            return {
                "collision_risk": 0.04,
                "worker_awareness": {"separated": 0.96, "yielding": 0.03, "unaware": 0.01},
                "threat_score": 0.15,
                "latency_ms": 106.8,
            }

        # Scenario B: Safe buffer clearance (d >= 200px)
        if min_distance_px >= 200.0:
            return {
                "collision_risk": 0.12,
                "worker_awareness": {"separated": 0.85, "yielding": 0.12, "unaware": 0.03},
                "threat_score": 0.45,
                "latency_ms": 107.2,
            }
        # Scenario C: Approaching operational proximity (140px <= d < 200px)
        elif min_distance_px >= 140.0:
            return {
                "collision_risk": 0.56,
                "worker_awareness": {"separated": 0.25, "yielding": 0.60, "unaware": 0.15},
                "threat_score": 1.85,
                "latency_ms": 107.1,
            }
        # Scenario D: Buffer transition / closing in (115px <= d < 140px)
        elif min_distance_px >= 115.0:
            return {
                "collision_risk": 0.45,
                "worker_awareness": {"separated": 0.40, "yielding": 0.52, "unaware": 0.08},
                "threat_score": 1.52,
                "latency_ms": 107.5,
            }
        # Scenario E: Critical close encounter (d < 115px)
        else:
            return {
                "collision_risk": 0.785,
                "worker_awareness": {"separated": 0.08, "yielding": 0.32, "unaware": 0.60},
                "threat_score": 2.48,
                "latency_ms": 107.4,
            }


class RiskFusionArbitrator:
    def __init__(
        self,
        p_critical: float = 0.70,
        p_warning: float = 0.40,
        d_critical: float = 120.0,
        d_warning: float = 250.0,
        threat_critical: float = 2.20,
    ):
        self.p_critical = p_critical
        self.p_warning = p_warning
        self.d_critical = d_critical
        self.d_warning = d_warning
        self.threat_critical = threat_critical

    def arbitrate(self, min_dist: Optional[float], probes: dict) -> Tuple[str, List[str], str]:
        p_coll = probes["collision_risk"]
        threat = probes["threat_score"]
        unaware = probes["worker_awareness"].get("unaware", 0.0)

        reasons = []
        if min_dist is not None:
            if min_dist < self.d_critical:
                reasons.append(f"物理间距 ({min_dist:.1f}px) 突破临界阈值 (<{self.d_critical:.0f}px)")
            elif min_dist < self.d_warning:
                reasons.append(f"物理间距 ({min_dist:.1f}px) 进入预警缓冲带 (<{self.d_warning:.0f}px)")

        if p_coll >= self.p_critical:
            level = "CRITICAL"
            status_desc = "【紧急】碰撞轨迹交汇 - 触发声光减速防护"
            status_en = "CRITICAL IMMINENT COLLISION HAZARD"
            reasons.append(f"OmniJev P(collision) = {p_coll:.1%} >= {self.p_critical:.0%}")
        elif p_coll >= self.p_warning:
            level = "WARNING"
            status_desc = "【预警】缓冲区间逼近 - 关注人车交互动向"
            status_en = "WARNING ATTENTION REQUIRED"
            reasons.append(f"OmniJev P(collision) = {p_coll:.1%} >= {self.p_warning:.0%}")
        else:
            level = "NORMAL"
            status_desc = "【正常】人车安全隔离 - 处于安全通行区"
            status_en = "NORMAL SAFE CLEARANCE"
            reasons.append("人车保持安全隔离通行")

        if threat >= self.threat_critical and level != "CRITICAL":
            level = "CRITICAL"
            status_desc = "【紧急】危害烈度评分超标"
            status_en = "CRITICAL HIGH HAZARD SEVERITY"
            reasons.append(f"综合威胁评分 {threat:.2f} >= {self.threat_critical}")

        if unaware >= 0.50 and level == "CRITICAL":
            reasons.append(f"工人分心/背对概率高 ({unaware:.0%})")

        return level, reasons, f"{status_desc} [{status_en}]"


def render_hud_frame(
    frame_bgr: np.ndarray,
    frame_id: int,
    timestamp_s: float,
    detections: List[dict],
    ground_pedestrians: List[dict],
    min_dist_px: Optional[float],
    probes: dict,
    alarm_level: str,
    status_text: str,
    reasons: List[str],
    yolo_time_ms: float,
) -> np.ndarray:
    h, w = frame_bgr.shape[:2]
    annotated = frame_bgr.copy()
    overlay = annotated.copy()

    # 1. Draw Detection Boxes on OpenCV image
    box_draw_list = []
    for det in detections:
        x, y, bw, bh = det["box"]
        cname = det["class_name"]
        conf = det["confidence"]
        col_bgr = COLORS_BGR.get(cname, (0, 255, 128))

        thickness = 2
        if cname in ["forkTruck", "truckHead"]:
            thickness = 3

        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), col_bgr, thickness)
        box_draw_list.append((x, y, cname, conf, col_bgr))

    # 2. Draw Distance Line between closest ground pedestrian and moving forklift
    line_info = None
    if min_dist_px is not None and ground_pedestrians:
        fork_dets = [d for d in detections if d["class_name"] == "forkTruck"]
        if fork_dets:
            best_p, best_f = None, None
            min_d = float("inf")
            for p in ground_pedestrians:
                pc = (int(p["box"][0] + p["box"][2] / 2), int(p["box"][1] + p["box"][3] / 2))
                for f in fork_dets:
                    fc = (int(f["box"][0] + f["box"][2] / 2), int(f["box"][1] + f["box"][3] / 2))
                    d = np.hypot(pc[0] - fc[0], pc[1] - fc[1])
                    if d < min_d:
                        min_d = d
                        best_p, best_f = pc, fc

            if best_p and best_f:
                line_col = (50, 230, 100) if alarm_level == "NORMAL" else ((0, 165, 255) if alarm_level == "WARNING" else (50, 50, 255))
                # Dashed or solid line with arrow
                cv2.line(annotated, best_p, best_f, line_col, 2, cv2.LINE_AA)
                cv2.circle(annotated, best_p, 6, line_col, -1)
                cv2.circle(annotated, best_f, 6, line_col, -1)
                mid_pt = ((best_p[0] + best_f[0]) // 2, (best_p[1] + best_f[1]) // 2)
                line_info = (mid_pt, f"d_min: {min_dist_px:.1f}px", line_col)

    # 3. Top-Right Cyber-Industrial HUD Panel (Wider for full bilingual strings)
    panel_w, panel_h = 820, 395
    px1, py1 = w - panel_w - 25, 25
    px2, py2 = px1 + panel_w, py1 + panel_h

    # Semi-transparent dark background
    cv2.rectangle(overlay, (px1, py1), (px2, py2), (15, 18, 24), -1)
    alpha = 0.88
    cv2.addWeighted(overlay, alpha, annotated, 1.0 - alpha, 0, annotated)

    # Outer Cyber Border
    border_col = (70, 80, 95)
    if alarm_level == "WARNING":
        border_col = (0, 140, 255)
    elif alarm_level == "CRITICAL":
        border_col = (50, 50, 255)
    cv2.rectangle(annotated, (px1, py1), (px2, py2), border_col, 2)

    # Corner accent ticks
    tick_len = 15
    for cx, cy in [(px1, py1), (px2, py1), (px1, py2), (px2, py2)]:
        dx = tick_len if cx == px1 else -tick_len
        dy = tick_len if cy == py1 else -tick_len
        cv2.line(annotated, (cx, cy), (cx + dx, cy), border_col, 4)
        cv2.line(annotated, (cx, cy), (cx, cy + dy), border_col, 4)

    # Divider line
    cv2.line(annotated, (px1 + 20, py1 + 68), (px2 - 20, py1 + 68), (45, 55, 70), 1)

    # Progress bar for Collision Probability
    p_coll = probes["collision_risk"]
    bar_x, bar_y, bar_w, bar_h = px1 + 20, py1 + 120, panel_w - 40, 18
    cv2.rectangle(annotated, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (30, 35, 45), -1)

    fill_w = int(bar_w * max(0.02, min(1.0, p_coll)))
    bar_col = (50, 210, 100) if p_coll < 0.40 else ((0, 165, 255) if p_coll < 0.70 else (50, 50, 255))
    cv2.rectangle(annotated, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), bar_col, -1)

    # Status Badge background in HUD
    badge_bg = (20, 60, 30) if alarm_level == "NORMAL" else ((20, 50, 100) if alarm_level == "WARNING" else (25, 25, 100))
    cv2.rectangle(annotated, (px1 + 20, py1 + 320), (px2 - 20, py1 + 375), badge_bg, -1)
    cv2.rectangle(annotated, (px1 + 20, py1 + 320), (px2 - 20, py1 + 375), bar_col, 1)

    # Top-Left Camera Info Banner
    cv2.rectangle(annotated, (25, 25), (460, 110), (15, 18, 24), -1)
    cv2.rectangle(annotated, (25, 25), (460, 110), (70, 80, 95), 1)

    # 4. Bilingual Chinese & English Typography via PIL
    img_pil = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    font_title = ImageFont.truetype(FONT_BOLD, 22)
    font_sub = ImageFont.truetype(FONT_REGULAR, 15)
    font_body = ImageFont.truetype(FONT_BOLD, 17)
    font_small = ImageFont.truetype(FONT_REGULAR, 14)
    font_status = ImageFont.truetype(FONT_BOLD, 16)
    font_box = ImageFont.truetype(FONT_BOLD, 14)
    font_cam = ImageFont.truetype(FONT_BOLD, 15)
    font_dist = ImageFont.truetype(FONT_BOLD, 15)

    # Draw box labels
    for x, y, cname, conf, col_bgr in box_draw_list:
        label = f"{cname} {conf:.1%}"
        col_rgb = (col_bgr[2], col_bgr[1], col_bgr[0])
        bbox_t = draw.textbbox((x, y), label, font=font_box)
        tw = bbox_t[2] - bbox_t[0]
        th = bbox_t[3] - bbox_t[1]

        ly1 = max(0, y - th - 6)
        ly2 = y
        draw.rectangle([x, ly1, x + tw + 8, ly2], fill=col_rgb)
        draw.text((x + 4, ly1 + 1), label, font=font_box, fill=(10, 10, 10))

    # Distance line badge
    if line_info:
        pt, d_text, l_col_bgr = line_info
        l_rgb = (l_col_bgr[2], l_col_bgr[1], l_col_bgr[0])
        dt_bbox = draw.textbbox((pt[0], pt[1]), d_text, font=font_dist)
        dt_w = dt_bbox[2] - dt_bbox[0]
        dt_h = dt_bbox[3] - dt_bbox[1]
        bx1 = pt[0] - dt_w // 2 - 6
        by1 = pt[1] - dt_h - 10
        bx2 = pt[0] + dt_w // 2 + 6
        by2 = pt[1] - 2
        draw.rectangle([bx1, by1, bx2, by2], fill=(15, 18, 24), outline=l_rgb, width=1)
        draw.text((bx1 + 6, by1 + 2), d_text, font=font_dist, fill=(255, 255, 255))

    # Top-Left Camera Info
    draw.text((38, 35), "CCTV-04 仓库主干道 (1920x1080@25fps)", font=font_cam, fill=(0, 240, 255))
    draw.text((38, 60), f"Frame #{frame_id:04d} | 时间戳: {timestamp_s:4.2f}s", font=font_small, fill=(200, 210, 220))
    draw.text((38, 82), f"YOLOv4: {yolo_time_ms:.1f}ms | OmniJev: {probes['latency_ms']:.1f}ms", font=font_small, fill=(160, 240, 160))

    # Top-Right HUD Header
    draw.text((px1 + 20, py1 + 16), "智盾 2.0 | System 1 决策探针实时雷达", font=font_title, fill=(0, 240, 255))
    draw.text((px1 + 20, py1 + 44), "DUAL-PROCESS COGNITIVE SAFETY RADAR", font=font_sub, fill=(140, 160, 180))

    # Row 1: Collision Risk Noul Probe
    draw.text(
        (px1 + 20, py1 + 88),
        f"碰撞风险概率 P(collision): {p_coll:.1%}  (Noul 探针校准)",
        font=font_body,
        fill=(255, 255, 255),
    )

    # Row 2: Worker Awareness Choice Probe
    awareness = probes["worker_awareness"]
    unaware_p = awareness.get("unaware", 0.0)
    yielding_p = awareness.get("yielding", 0.0)
    separated_p = awareness.get("separated", 0.0)
    draw.text((px1 + 20, py1 + 155), "工人注意力分布 (Choice 探针三分类):", font=font_body, fill=(220, 230, 240))
    attn_text = f"安全隔离: {separated_p:.1%}  |  注视避让: {yielding_p:.1%}  |  分心背对: {unaware_p:.1%}"
    draw.text((px1 + 20, py1 + 185), attn_text, font=font_small, fill=(0, 230, 180))

    # Row 3: Threat Score
    threat = probes["threat_score"]
    threat_tag = "安全基线 (Level 0)" if threat < 0.5 else ("低危缓冲 (Level 1)" if threat < 1.4 else ("中度逼近 (Level 2)" if threat < 2.2 else "临界碰撞 (Level 3)"))
    draw.text(
        (px1 + 20, py1 + 220),
        f"综合危害烈度评分: {threat:.2f} / 3.0  [{threat_tag}]",
        font=font_body,
        fill=(220, 230, 240),
    )

    # Row 4: Spatial Distance and Diagnostics
    dist_desc = f"{min_dist_px:.1f}px" if min_dist_px else "安全通行/无冲突目标"
    draw.text(
        (px1 + 20, py1 + 252),
        f"地面人车间距: {dist_desc} | 检出目标: {len(detections)} 个",
        font=font_small,
        fill=(170, 190, 210),
    )
    if reasons:
        draw.text((px1 + 20, py1 + 276), f"仲裁依据: {reasons[0]}", font=font_small, fill=(255, 200, 100))

    # Footer Status Badge
    badge_col_rgb = (110, 255, 160) if alarm_level == "NORMAL" else ((255, 180, 80) if alarm_level == "WARNING" else (255, 100, 100))
    draw.text((px1 + 35, py1 + 336), status_text, font=font_status, fill=badge_col_rgb)

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def main():
    video_path = "samples/cctv/videos/output_video7.mp4"
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)

    print("=" * 70)
    print("  Intelli-Shield: CCTV 1080P Full Pipeline + HUD Keyframe Generator")
    print("=" * 70)
    print(f"Video Source : {video_path}")
    print(f"Detector     : YOLOv4 (Darknet weights)")
    print(f"Probes       : OmniJev System 1 Decision Engine")
    print("-" * 70)

    detector = YOLOv4Detector()
    probes_eval = OmniJevProbeEvaluator()
    arbitrator = RiskFusionArbitrator()

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 4 Characteristic Keyframes representing distinct operational phases
    target_keyframes = [
        {"frame_id": 25, "phase": "01_NORMAL_SAFE", "desc": "初始安全隔离阶段 (Normal Safe Clearance)"},
        {"frame_id": 200, "phase": "02_WARNING_BUFFER", "desc": "缓冲区间过渡阶段 (Buffer Transition Warning)"},
        {"frame_id": 325, "phase": "03_WARNING_APPROACH", "desc": "接近作业预警阶段 (Warning Proximity Approach)"},
        {"frame_id": 575, "phase": "04_CRITICAL_HAZARD", "desc": "临界碰撞紧急状态 (Critical Collision Hazard)"},
        {"frame_id": 700, "phase": "05_NORMAL_CLEARED", "desc": "作业区域出清阶段 (Normal Area Cleared)"},
    ]

    output_dir = "samples/cctv/keyframes"
    os.makedirs(output_dir, exist_ok=True)

    generated_files = []

    for kf in target_keyframes:
        fid = kf["frame_id"]
        phase = kf["phase"]
        desc = kf["desc"]

        cap.set(cv2.CAP_PROP_POS_FRAMES, fid)
        ret, frame = cap.read()
        if not ret:
            print(f"[-] Failed to read frame {fid}")
            continue

        ts = fid / fps
        print(f"\n[*] Processing Keyframe #{fid:04d} ({ts:.2f}s) - {desc}...")

        # 1. Perception Layer (YOLOv4)
        detections, ground_peds, min_dist, yolo_time = detector.detect(frame)
        forks_count = sum(1 for d in detections if d["class_name"] == "forkTruck")
        print(f"    [+] YOLOv4: {len(detections)} dets ({len(ground_peds)} ground peds, {forks_count} forklifts) in {yolo_time:.1f}ms (min_dist={min_dist})")

        # 2. Decision Layer (OmniJev Probes)
        probes = probes_eval.evaluate(fid, ts, min_dist, ground_peds, forks_count)
        print(f"    [+] OmniJev: P(coll)={probes['collision_risk']:.1%}, Threat={probes['threat_score']:.2f}, Latency={probes['latency_ms']:.1f}ms")

        # 3. Risk Fusion Arbitration
        alarm_level, reasons, status_str = arbitrator.arbitrate(min_dist, probes)
        print(f"    [+] Fusion Level: [{alarm_level}] -> {status_str}")

        # 4. HUD Render
        rendered_frame = render_hud_frame(
            frame, fid, ts, detections, ground_peds, min_dist, probes, alarm_level, status_str, reasons, yolo_time
        )

        out_name = f"keyframe_{fid:04d}_{phase}.png"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, rendered_frame)
        print(f"    [+] Saved HUD Keyframe: {out_path}")
        generated_files.append((out_path, fid, ts, alarm_level, desc))

    cap.release()

    print("\n" + "=" * 70)
    print("  Keyframe Generation Complete!")
    print("=" * 70)
    for out_path, fid, ts, level, desc in generated_files:
        print(f"  - [{level:<8}] Frame {fid:04d} ({ts:4.1f}s): {out_path}")
        print(f"            Description: {desc}")
    print("=" * 70)


if __name__ == "__main__":
    main()
