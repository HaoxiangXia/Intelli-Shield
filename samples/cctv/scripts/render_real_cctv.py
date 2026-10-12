"""Renders real CCTV detections and OmniJev probe overlay on the camera image (Bilingual CN/EN)."""

import json
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

img_path = "samples/cctv/raw_images/220121shenyang1509.png"
perception_path = "samples/cctv/benchmarks/perception_real_cctv.json"
probe_path = "samples/cctv/benchmarks/probe_real_cctv.json"
out_path = "samples/cctv/keyframes/220121shenyang1509_annotated.png"

# Fonts
FONT_PATH = "/home/xiang/.local/share/fonts/MapleMono-NF-CN-Bold.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

font_title = ImageFont.truetype(FONT_PATH, 28)
font_sub = ImageFont.truetype(FONT_PATH, 20)
font_body = ImageFont.truetype(FONT_PATH, 23)
font_attn = ImageFont.truetype(FONT_PATH, 22)
font_status = ImageFont.truetype(FONT_PATH, 25)
font_box = ImageFont.truetype(FONT_PATH, 22)

# Load data
with open(perception_path, "r", encoding="utf-8") as f:
    percep_data = json.load(f)

with open(probe_path, "r", encoding="utf-8") as f:
    probe_data = json.load(f)

probes = probe_data.get("probes", {})
p_coll = probes.get("collision_risk", 0.0)
awareness = probes.get("worker_awareness", {})
threat = probes.get("threat_score", 0.0)

# Load image via OpenCV for drawing rectangles, then PIL for text
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(f"Failed to read image at {img_path}")

h, w = img.shape[:2]
overlay = img.copy()

# 1. Draw Bounding Boxes via OpenCV
box_labels = []

for det in percep_data.get("detections", []):
    cls_name = det["class_name"]
    conf = det["confidence"]
    x1, y1, x2, y2 = [int(v) for v in det["bbox"]]

    if cls_name == "person":
        color = (255, 200, 0)  # Sky-blue BGR
        label = f"工人 / Worker {conf:.2f}"
    else:
        color = (0, 215, 255)  # Industrial Yellow BGR
        label = f"货车 / Truck {conf:.2f}"

    cv2.rectangle(img, (x1, y1), (x2, y2), color, 4)
    box_labels.append((x1, y1, label, color))

# Forklift (Right side)
fork_box = (1950, 950, 2380, 1400)
fx1, fy1, fx2, fy2 = fork_box
fork_color = (220, 100, 255)  # Purple
# 2. Top-Right HUD Panel Background
panel_w, panel_h = 950, 420
px1, py1 = w - panel_w - 30, 30
px2, py2 = px1 + panel_w, py1 + panel_h

cv2.rectangle(overlay, (px1, py1), (px2, py2), (15, 18, 22), -1)
alpha = 0.85
img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
cv2.rectangle(img, (px1, py1), (px2, py2), (75, 85, 100), 2)
cv2.line(img, (px1 + 25, py1 + 85), (px2 - 25, py1 + 85), (60, 70, 85), 2)

# Progress bar background
bar_x, bar_y, bar_w, bar_h = px1 + 25, py1 + 140, 900, 22
cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (35, 40, 50), -1)
fill_w = int(bar_w * p_coll)
cv2.rectangle(img, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (50, 205, 100), -1)

# Status Badge Box
cv2.rectangle(img, (px1 + 25, py1 + 345), (px2 - 25, py1 + 395), (25, 75, 35), -1)
# Convert to PIL Image for Bilingual Chinese-English text drawing
img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(img_pil)

# Draw box badge labels
for x, y, text, col_bgr in box_labels:
    col_rgb = (col_bgr[2], col_bgr[1], col_bgr[0])
    bbox = draw.textbbox((x, max(y - 35, 0)), text, font=font_box)
    draw.rectangle((bbox[0] - 4, bbox[1] - 4, bbox[2] + 4, bbox[3] + 4), fill=col_rgb)
    draw.text((x, max(y - 35, 0)), text, font=font_box, fill=(10, 10, 10))

# HUD Panel Texts
draw.text((px1 + 25, py1 + 18), "智盾 2.0 | System 1 决策探针实时雷达 (PROBE HUD)", font=font_title, fill=(0, 235, 255))
# Row 1: Collision Probability
p_status = "安全缓冲区间 (Safe Buffer)" if p_coll < 0.4 else "预警关注 (Warning)"
draw.text((px1 + 25, py1 + 105), f"碰撞风险概率 P(collision): {p_coll:.1%}  [{p_status}]", font=font_body, fill=(255, 255, 255))

# Row 2: Worker Attention
unaware_p = awareness.get("unaware", 0.0)
yielding_p = awareness.get("yielding", 0.0)
separated_p = awareness.get("separated", 0.0)
draw.text((px1 + 25, py1 + 180), "工人注意力分布 (Choice 探针分类):", font=font_body, fill=(215, 225, 235))
attn_desc = f"安全隔离: {separated_p:.1%}  |  注视避让: {yielding_p:.1%}  |  分心背对: {unaware_p:.1%}"
draw.text((px1 + 25, py1 + 215), attn_desc, font=font_attn, fill=(0, 225, 175))

# Row 3: Threat Score
threat_desc = "1级-轻度缓冲作业 (Level 1 Buffer)" if threat < 1.8 else "2级-紧迫关注"
draw.text((px1 + 25, py1 + 260), f"综合危害烈度评分: {threat:.2f} / 3.0  [{threat_desc}]", font=font_body, fill=(215, 225, 235))
draw.text((px1 + 25, py1 + 295), f"单帧稳态推理时延: {probes.get('latency_ms', 107.0):.1f} ms  (毫秒级直觉快决策)", font=font_sub, fill=(160, 180, 200))

# Status Badge Text
draw.text((px1 + 50, py1 + 355), "当前状态: [正常 - 人车安全隔离 (NORMAL SAFE CLEARANCE)]", font=font_status, fill=(110, 255, 160))

# Save
img_bgr_final = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
cv2.imwrite(out_path, img_bgr_final)
print(f"Successfully generated bilingual annotated image: {out_path}")
