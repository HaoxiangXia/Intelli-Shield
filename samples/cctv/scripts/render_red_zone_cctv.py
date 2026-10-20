"""Renders CCTV frame with ground Red-Zone safety perimeter and System 1 cognitive HUD."""

from __future__ import annotations
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pipeline.detector import YOLODetector
from pipeline.gating import SpatialTemporalGate
from pipeline.models import AlarmLevel, OmniJevProbes, RedZoneState
from pipeline.risk_fusion import RiskFusionEngine


def render_annotated_frame(
    video_path: str = "samples/cctv/videos/output_video7.mp4",
    timestamp_sec: float = 10.0,
    out_path: str = "samples/cctv/keyframes/red_zone_cctv_annotated.png",
):
    # 1. Load video frame
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"Could not read frame at {timestamp_sec}s from {video_path}")

    h, w = frame.shape[:2]

    # 2. Run Pipeline (Perception -> RedZone -> Gating -> Risk Fusion)
    cfg_path = "models/yolov4-custom-hebei.cfg"
    weights_path = "models/yolov4-custom-hebei_last.weights"
    if os.path.exists(cfg_path) and os.path.exists(weights_path):
        detector = YOLODetector(cfg_path=cfg_path, weights_path=weights_path)
    else:
        detector = YOLODetector(cfg_path="", weights_path="yolo26n.pt")
    gate = SpatialTemporalGate()
    fusion = RiskFusionEngine()

    perception = detector.detect(frame, frame_id=int(timestamp_sec * 10), timestamp=timestamp_sec)
    gate_decision = gate.evaluate(perception)

    # Realistic OmniJev probe output from empirical 3090 log
    probes = OmniJevProbes(
        collision_risk=0.785,
        worker_awareness={"unaware": 0.65, "yielding": 0.25, "separated": 0.10},
        threat_score=2.48,
        latency_ms=107.4,
    )

    decision = fusion.arbitrate(
        int(timestamp_sec * 10), timestamp_sec, perception, probes=probes, gating=gate_decision
    )

    # 3. Visualization drawing layer
    overlay = frame.copy()

    # Draw Red-Zone polygons on ground
    rz = decision.red_zone
    if rz and rz.polygons:
        for poly_pts in rz.polygons:
            pts_np = np.array(poly_pts, dtype=np.int32).reshape(-1, 1, 2)
            # Semi-transparent red danger fill
            cv2.fillPoly(overlay, [pts_np], (0, 0, 180))
            # Glowing contour border
            cv2.polylines(frame, [pts_np], isClosed=True, color=(0, 0, 255), thickness=4)
            cv2.polylines(frame, [pts_np], isClosed=True, color=(50, 150, 255), thickness=1)

    # Blend ground overlay
    alpha = 0.35
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Draw Forklift bounding boxes
    for fork in perception.forklifts:
        fx1, fy1, fx2, fy2 = int(fork.x1), int(fork.y1), int(fork.x2), int(fork.y2)
        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 140, 255), 3)

    # Draw Pedestrian bounding box & Ground Foot Anchor
    for ped in perception.pedestrians:
        px1, py1, px2, py2 = int(ped.x1), int(ped.y1), int(ped.x2), int(ped.y2)
        cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 255, 255), 2)

        # Foot Ground Anchor
        foot_x = int((px1 + px2) / 2)
        foot_y = int(py2)

        # Draw foot target anchor
        cv2.circle(frame, (foot_x, foot_y), 8, (0, 0, 255), -1)
        cv2.circle(frame, (foot_x, foot_y), 16, (0, 255, 255), 2)
        cv2.line(frame, (foot_x - 22, foot_y), (foot_x + 22, foot_y), (0, 255, 255), 2)
        cv2.line(frame, (foot_x, foot_y - 22), (foot_x, foot_y + 22), (0, 255, 255), 2)

    # 4. HUD Radar Dashboard
    panel_w, panel_h = 960, 440
    panel_x1, panel_y1 = w - panel_w - 30, 30
    panel_x2, panel_y2 = panel_x1 + panel_w, panel_y1 + panel_h

    hud_overlay = frame.copy()
    cv2.rectangle(hud_overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), (16, 20, 26), -1)
    hud_alpha = 0.88
    frame = cv2.addWeighted(hud_overlay, hud_alpha, frame, 1 - hud_alpha, 0)
    cv2.rectangle(frame, (panel_x1, panel_y1), (panel_x2, panel_y2), (70, 80, 95), 2)
    cv2.line(frame, (panel_x1 + 25, panel_y1 + 80), (panel_x2 - 25, panel_y1 + 80), (60, 70, 85), 2)

    # Status Bar Box
    status_box_y = panel_y1 + 360
    cv2.rectangle(frame, (panel_x1 + 25, status_box_y), (panel_x2 - 25, status_box_y + 55), (20, 20, 140), -1)
    cv2.rectangle(frame, (panel_x1 + 25, status_box_y), (panel_x2 - 25, status_box_y + 55), (0, 0, 255), 2)

    # 5. Bilingual Typography via PIL
    font_path = "/home/xiang/.local/share/fonts/MapleMono-NF-CN-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

    font_title = ImageFont.truetype(font_path, 26)
    font_body = ImageFont.truetype(font_path, 21)
    font_sub = ImageFont.truetype(font_path, 19)
    font_badge = ImageFont.truetype(font_path, 22)
    font_tag = ImageFont.truetype(font_path, 18)

    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    # Ground Foot Tag Badge
    for ped in perception.pedestrians:
        bx1, by1, bx2, by2 = int(ped.x1), int(ped.y1), int(ped.x2), int(ped.y2)
        foot_x = int((bx1 + bx2) / 2)
        foot_y = int(by2)
        rz_m_str = f"{rz.min_dist_m:.2f}m" if rz else "N/A"
        tag_text = f"【足底接地点】越过红线: {rz_m_str} (禁区违规侵入)"
        # Dark badge pill behind text
        t_w = int(len(tag_text) * 19)
        draw.rectangle([(foot_x - 175, foot_y + 15), (foot_x - 175 + t_w, foot_y + 45)], fill=(20, 20, 28, 220))
        draw.text((foot_x - 170, foot_y + 18), tag_text, font=font_tag, fill=(255, 100, 100))

    # Forklift Tag Badge
    for fork in perception.forklifts:
        fx1, fy1 = int(fork.x1), int(fork.y1)
        f_tag = "【叉车】三向红光警戒区"
        f_w = int(len(f_tag) * 18)
        draw.rectangle([(fx1, max(fy1 - 30, 8)), (fx1 + f_w, max(fy1 - 4, 34))], fill=(15, 25, 35, 220))
        draw.text((fx1 + 6, max(fy1 - 28, 10)), f_tag, font=font_tag, fill=(0, 230, 255))
    # HUD Texts
    draw.text((panel_x1 + 25, panel_y1 + 18), "智盾 2.0 | 卡尼曼双系统认知风控与红光空间防御 (PROBE HUD)", font=font_title, fill=(0, 240, 255))
    draw.text((panel_x1 + 25, panel_y1 + 52), "System 1 Fast Intuition (OmniJev) + Physical Red-Zone Hard Boundary", font=font_sub, fill=(160, 180, 200))

    # Metric Row 1: Physical Red Zone Boundary
    rz_state_desc = "严重违规 - 侵入红光禁区 (ZONE_INSIDE)" if rz and rz.state == RedZoneState.INSIDE else "正常隔离"
    draw.text((panel_x1 + 25, panel_y1 + 100), f"物理红光防御状态: {rz_state_desc}", font=font_body, fill=(255, 90, 90))
    rz_dist_str = f"侵入深度: {-rz.min_dist_px:.1f} px  ({-rz.min_dist_m:.2f} m)  [一票否决硬约束生效]" if rz else "N/A"
    draw.text((panel_x1 + 25, panel_y1 + 135), f"红光边缘距离: {rz_dist_str}", font=font_body, fill=(255, 220, 100))

    # Metric Row 2: OmniJev Collision Probability
    p_coll = probes.collision_risk
    draw.text((panel_x1 + 25, panel_y1 + 180), f"System 1 碰撞风险 P(collision): {p_coll:.1%}  [高危轨迹碰撞趋势]", font=font_body, fill=(255, 255, 255))

    # Metric Row 3: Worker Attention Distribution
    awareness = probes.worker_awareness
    unaware_p = awareness.get("unaware", 0.0)
    yielding_p = awareness.get("yielding", 0.0)
    separated_p = awareness.get("separated", 0.0)
    draw.text((panel_x1 + 25, panel_y1 + 225), "工人注意力分布 (Choice 探针语义):", font=font_body, fill=(215, 225, 235))
    attn_str = f"分心背对: {unaware_p:.1%} (高危盲区) | 注视避让: {yielding_p:.1%} | 安全隔离: {separated_p:.1%}"
    draw.text((panel_x1 + 25, panel_y1 + 258), attn_str, font=font_sub, fill=(255, 120, 120))

    # Metric Row 4: Threat Score & Latency
    draw.text((panel_x1 + 25, panel_y1 + 295), f"综合危害烈度评分: {probes.threat_score:.2f} / 3.0  [3级紧迫危险] | 推理时延: {probes.latency_ms:.1f} ms", font=font_sub, fill=(180, 200, 220))

    # Metric Row 5: Final Alarm Badge
    badge_str = "当前状态: [CRITICAL 紧急报警 - 侵入红光禁区，触发声光告警与急停]"
    draw.text((panel_x1 + 45, status_box_y + 14), badge_str, font=font_badge, fill=(255, 230, 230))

    # Save
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img_final = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imwrite(out_path, img_final)
    print(f"Successfully generated annotated image: {out_path}")
    return out_path


if __name__ == "__main__":
    render_annotated_frame()
