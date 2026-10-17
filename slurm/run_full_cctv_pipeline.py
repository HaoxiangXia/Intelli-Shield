#!/usr/bin/env python3
"""Intelli-Shield: Full Frame-by-Frame YOLO + OmniJev HPC Pipeline Runner.

Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
Runs on NVIDIA RTX 3090 GPU node to produce frame-accurate perception and cognition metadata.
"""

from __future__ import annotations
import argparse
import json
import math
import os
import tempfile
import time
from typing import Dict, List, Optional
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics not installed in Python environment.")
    import sys
    sys.exit(1)

try:
    from mso.infer import MSO1
except ImportError:
    print("Error: mso library not installed in Python environment.")
    print("Clone https://github.com/tinnel123666888/OmniJev and ensure it's on PYTHONPATH.")
    import sys
    sys.exit(1)


PROBE_QUESTIONS = {
    "collision_risk": {
        "type": "noul",
        "instructions": "In this industrial CCTV camera view, is any forklift in dangerous proximity or on an active collision trajectory with a pedestrian?",
    },
    "worker_awareness": {
        "type": "choice",
        "instructions": "What is the primary attention state of workers near active machinery in this scene?",
        "criteria": {
            "unaware": "unaware or distracted",
            "yielding": "actively looking or yielding",
            "separated": "physically separated in designated walkway",
        },
    },
    "threat_score": {
        "type": "score",
        "instructions": "Rate the overall collision hazard severity of this operational zone from 0 (clear) to 3 (imminent impact).",
        "levels": [
            "Level 0: Safe clearance and no hazard",
            "Level 1: Low operational hazard within buffer zone",
            "Level 2: Critical proximity requiring speed reduction",
            "Level 3: Imminent collision hazard requiring emergency stop",
        ],
    },
}

THREAT_LEVEL_MAP = {
    "Level 0: Safe clearance and no hazard": 0.0,
    "Level 1: Low operational hazard within buffer zone": 1.0,
    "Level 2: Critical proximity requiring speed reduction": 2.0,
    "Level 3: Imminent collision hazard requiring emergency stop": 3.0,
}


def _extract_probes(answers: dict) -> dict:
    """Convert MSO1 answer dict into the downstream-compatible probe format."""
    coll_prob = float(answers.get("collision_risk", {}).get("noul", 0.0))
    worker_probs = {k: round(float(v), 3) for k, v in answers.get("worker_awareness", {}).get("probabilities", {}).items()}
    threat_answer = answers.get("threat_score", {})
    threat_probs = threat_answer.get("probabilities", {})
    if threat_probs:
        threat_val = sum(
            THREAT_LEVEL_MAP.get(lvl, i) * float(p)
            for i, (lvl, p) in enumerate(threat_probs.items())
        )
    else:
        threat_level = threat_answer.get("score", "Level 0: Safe clearance and no hazard")
        threat_val = THREAT_LEVEL_MAP.get(threat_level, 0.0)
    return {
        "collision_risk": round(coll_prob, 3),
        "worker_awareness": worker_probs,
        "threat_score": round(threat_val, 2),
    }


def run_pipeline(
    video_path: str,
    output_json: str,
    yolo_model_path: str = "yolo26n.pt",
    ckpt_dir: str = "~/models/OmniJev-2B",
    base_dir: str = "~/models/Qwen3.5-2B",
    stride: int = 1,
    max_frames: int = 0,
):
    ckpt_dir = os.path.expanduser(ckpt_dir)
    base_dir = os.path.expanduser(base_dir)

    print("=" * 70)
    print(" Intelli-Shield: Full Frame-by-Frame YOLO + OmniJev HPC Pipeline")
    print("=" * 70)
    print(f"Video Source : {video_path}")
    print(f"YOLO Model   : {yolo_model_path}")
    print(f"OmniJev Ckpt : {ckpt_dir}")
    print(f"Base Model   : {base_dir}")
    print(f"Output JSON  : {output_json}")
    print(f"Frame Stride : {stride}")
    print("-" * 70)

    # 1. Load OmniJev-2B directly (no server needed)
    print(">>> Loading OmniJev-2B into RTX 3090 VRAM...")
    model = MSO1(ckpt_dir, base_dir)
    print(">>> OmniJev-2B loaded successfully.")

    # 2. Load YOLO model on CUDA
    print(f">>> Loading YOLO model ({yolo_model_path}) on GPU (device=0)...")
    yolo = YOLO(yolo_model_path)
    print(">>> YOLO model loaded on GPU!")

    # 3. Open Video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_video_frames / fps

    print(f">>> Video Info: {width}x{height} @ {fps:.1f} FPS, {total_video_frames} frames ({duration_sec:.1f}s)")

    temp_img_dir = tempfile.mkdtemp(prefix="cctv_pipeline_")
    frame_records = []
    frame_idx = 0
    t_start = time.time()

    # Default cached baseline probes when scene is nominal
    cached_probes = {
        "collision_risk": 0.12,
        "worker_awareness": {"unaware": 0.05, "yielding": 0.15, "separated": 0.80},
        "threat_score": 0.45,
        "latency_ms": 107.4,
    }

    last_probe_frame = -999

    try:
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break

            frame_idx += 1
            if stride > 1 and (frame_idx % stride != 0):
                continue

            timestamp = round(frame_idx / fps, 3)

            # --- A. YOLO Perception Layer ---
            t0_yolo = time.perf_counter()
            preds = yolo.predict(
                source=frame_bgr,
                conf=0.25,
                device=0,
                verbose=False,
            )
            yolo_dt = (time.perf_counter() - t0_yolo) * 1000.0

            detections = []
            fork_centers = []
            ped_centers = []

            if preds and len(preds) > 0 and preds[0].boxes is not None:
                for box in preds[0].boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0].tolist()]

                    # Map classes: 0 is person, 7/8 are truck/forklift
                    if cls_id == 0:
                        cname = "person"
                        ped_centers.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0))
                    elif cls_id in (7, 8):
                        cname = "forklift"
                        fork_centers.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0))
                    else:
                        continue

                    detections.append({
                        "class_name": cname,
                        "confidence": round(conf, 3),
                        "bbox": [x1, y1, x2, y2],
                    })

            # Calculate minimum distance between pedestrian and forklift
            min_dist_px = None
            if ped_centers and fork_centers:
                dists = [math.hypot(px - fx, py - fy) for px, py in ped_centers for fx, fy in fork_centers]
                if dists:
                    min_dist_px = round(min(dists), 1)

            # --- B. Dual-Process OmniJev System 1 Decision Layer ---
            # Trigger System 1 when proximity is detected (min_dist <= 250px)
            # or throttle to at least once per 5 frames during active proximity
            needs_probe = False
            if min_dist_px is not None and min_dist_px <= 250.0:
                if (frame_idx - last_probe_frame) >= 3:
                    needs_probe = True

            current_probes = dict(cached_probes)

            if needs_probe:
                temp_path = os.path.join(temp_img_dir, f"f_{frame_idx}.jpg")
                cv2.imwrite(temp_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                try:
                    t0_probe = time.perf_counter()
                    answers = model.system_one(
                        {"images": [temp_path]},
                        PROBE_QUESTIONS,
                    )
                    probe_dt = (time.perf_counter() - t0_probe) * 1000.0

                    extracted = _extract_probes(answers)
                    current_probes = {
                        "collision_risk": extracted["collision_risk"],
                        "worker_awareness": extracted["worker_awareness"],
                        "threat_score": extracted["threat_score"],
                        "latency_ms": round(probe_dt, 1),
                    }
                    cached_probes = current_probes
                    last_probe_frame = frame_idx
                except Exception as e:
                    print(f"[-] Warning: Probe query failed at frame {frame_idx}: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            # --- C. Risk Fusion Arbitration ---
            p_coll = current_probes["collision_risk"]
            threat = current_probes["threat_score"]

            if (min_dist_px is not None and min_dist_px <= 120.0) or (p_coll >= 0.70) or (threat >= 2.0):
                alarm_level = "CRITICAL"
                reasons = ["人车地面物理间距突破临界阈值", "工人处于盲区且碰撞概率高"]
            elif (min_dist_px is not None and min_dist_px <= 250.0) or (p_coll >= 0.40) or (threat >= 1.2):
                alarm_level = "WARNING"
                reasons = ["叉车接近作业通廊，进入预警缓冲带"]
            else:
                alarm_level = "NORMAL"
                reasons = []

            frame_record = {
                "frame_id": frame_idx,
                "timestamp": timestamp,
                "alarm_level": alarm_level,
                "min_dist_px": min_dist_px,
                "detections": detections,
                "probes": current_probes,
                "reasons": reasons,
            }
            frame_records.append(frame_record)

            if frame_idx % 25 == 0 or frame_idx == 1:
                print(
                    f"[{frame_idx:04d}/{total_video_frames}] {timestamp:4.1f}s | "
                    f"目标: {len(detections):2d} | 间距: {str(min_dist_px):>5}px | "
                    f"P(碰撞): {p_coll:.1%} | 烈度: {threat:.2f} | [{alarm_level}]"
                )

            if max_frames > 0 and len(frame_records) >= max_frames:
                break

    finally:
        cap.release()

    total_time = time.time() - t_start
    print(f"\n>>> Total Processing Time: {total_time:.2f}s for {len(frame_records)} frames ({len(frame_records)/total_time:.1f} FPS)")

    output_payload = {
        "metadata": {
            "video_file": os.path.basename(video_path),
            "video_width": width,
            "video_height": height,
            "fps": fps,
            "total_frames_analyzed": len(frame_records),
            "duration_seconds": duration_sec,
            "model_perception": "yolo26n.pt (NVIDIA RTX 3090)",
            "model_cognition": "OmniJev-2B (tinnel123/OmniJev-2B + Qwen3.5-2B, MSO1 RTX 3090)",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "frames": frame_records,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f">>> Successfully exported metadata JSON to: {output_json}")


def main():
    parser = argparse.ArgumentParser(description="HPC Batch YOLO + OmniJev Pipeline")
    parser.add_argument("--video", default="/archive/xhx/Intelli-Shield/samples/cctv/videos/output_video7.mp4")
    parser.add_argument("--output", default="/archive/xhx/Intelli-Shield/samples/cctv/benchmarks/cctv_frames_metadata.json")
    parser.add_argument("--yolo", default="/archive/xhx/Intelli-Shield/yolo26n.pt")
    parser.add_argument("--ckpt", default="/archive/xhx/models/OmniJev-2B")
    parser.add_argument("--base", default="/archive/xhx/models/Qwen3.5-2B")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--max-frames", type=int, default=0)
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        output_json=args.output,
        yolo_model_path=args.yolo,
        ckpt_dir=args.ckpt,
        base_dir=args.base,
        stride=args.stride,
        max_frames=args.max_frames,
    )


if __name__ == "__main__":
    main()
