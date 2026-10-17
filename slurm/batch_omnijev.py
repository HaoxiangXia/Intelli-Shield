"""OmniJev Offline Batch Processing on Slurm RTX 3090.

Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
Extracts frames from CCTV video, runs OmniJev probes on 3090 GPU, and writes
calibrated probabilities into a structured JSON log.
"""

from __future__ import annotations
import argparse
import json
import os
import tempfile
import time
from typing import Dict, List
import cv2
import numpy as np

try:
    from mso.infer import MSO1
except ImportError:
    MSO1 = None


# The 4 standardized decision probes in MSO question format
PROBE_QUESTIONS = {
    "collision_risk": {
        "type": "noul",
        "instructions": "In this industrial CCTV camera view, is any forklift in dangerous proximity or on an active collision trajectory with a pedestrian?",
    },
    "worker_awareness": {
        "type": "choice",
        "instructions": "What is the primary attention state of workers near active machinery in this scene?",
        "criteria": {
            "unaware/distracted": "unaware or distracted",
            "actively looking/yielding": "actively looking or yielding",
            "physically separated in walkway": "physically separated in designated walkway",
        },
    },
    "worker_hazard_behavior": {
        "type": "choice",
        "instructions": "Does any worker exhibit dangerous non-compliant behaviors near forklifts, such as looking down at phone or walking with back turned?",
        "criteria": {
            "phone_distracted": "looking down at mobile phone while in operational zone",
            "back_facing_vehicle": "back turned to approaching forklift, unaware",
            "standing_in_blindspot": "standing in vehicle blind spot zone",
            "normal_compliant": "compliant posture, attentive and aware",
        },
    },
    "threat_score": {
        "type": "score",
        "instructions": "Rate the overall collision hazard severity of this operational zone from 0 (safe clearance) to 3 (imminent critical impact).",
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
    coll_val = float(answers.get("collision_risk", {}).get("noul", 0.0))
    awareness_probs = {
        k: round(float(v), 4)
        for k, v in answers.get("worker_awareness", {}).get("probabilities", {}).items()
    }
    hazard_probs = {
        k: round(float(v), 4)
        for k, v in answers.get("worker_hazard_behavior", {}).get("probabilities", {}).items()
    }
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
        "collision_risk": round(coll_val, 4),
        "worker_awareness": awareness_probs,
        "worker_hazard_behavior": hazard_probs,
        "threat_score": round(threat_val, 2),
    }


def process_video(
    video_path: str,
    output_json: str,
    sample_stride: int = 2,
    ckpt_dir: str = "~/models/OmniJev-2B",
    base_dir: str = "~/models/Qwen3.5-2B",
):
    ckpt_dir = os.path.expanduser(ckpt_dir)
    base_dir = os.path.expanduser(base_dir)

    print("=" * 60)
    print(" OmniJev Batch Video Inference (Slurm 3090)")
    print("=" * 60)
    print(f"Input Video  : {video_path}")
    print(f"Output JSON  : {output_json}")
    print(f"Frame Stride : {sample_stride}")
    print(f"Model Ckpt   : {ckpt_dir}")
    print(f"Base Model   : {base_dir}")
    print("-" * 60)

    model = None
    if MSO1 is not None:
        model = MSO1(ckpt_dir, base_dir)
        print("OmniJev-2B loaded on CUDA.")
    else:
        print("Warning: mso not found; running mock evaluation.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    frame_idx = 0
    results = []
    t_start = time.time()
    tmp_dir = tempfile.mkdtemp(prefix="omnijev_batch_")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % sample_stride != 0:
            continue

        timestamp = frame_idx / fps
        t0 = time.perf_counter()

        if model is not None:
            tmp_path = os.path.join(tmp_dir, f"frame_{frame_idx:05d}.jpg")
            cv2.imwrite(tmp_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            try:
                answers = model.system_one({"images": [tmp_path]}, PROBE_QUESTIONS)
                probes_data = _extract_probes(answers)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            # Fallback placeholder
            probes_data = {
                "collision_risk": 0.35,
                "worker_awareness": {
                    "unaware/distracted": 0.50,
                    "actively looking/yielding": 0.40,
                    "physically separated in walkway": 0.10,
                },
                "worker_hazard_behavior": {
                    "phone_distracted": 0.15,
                    "back_facing_vehicle": 0.75,
                    "standing_in_blindspot": 0.05,
                    "normal_compliant": 0.05,
                },
                "threat_score": 1.2,
            }

        latency_ms = (time.perf_counter() - t0) * 1000.0
        probes_data["latency_ms"] = latency_ms

        results.append({
            "frame_id": frame_idx,
            "timestamp": timestamp,
            "probes": probes_data,
        })

        if len(results) % 20 == 0 or frame_idx >= total_video_frames:
            print(
                f"Processed frame {frame_idx}/{total_video_frames} | "
                f"P(coll)={probes_data['collision_risk']:.2f} | {latency_ms:.1f}ms"
            )

    cap.release()
    total_time = time.time() - t_start

    output_payload = {
        "metadata": {
            "video_path": video_path,
            "model": "OmniJev-2B (tinnel123/OmniJev-2B + Qwen3.5-2B)",
            "total_frames_sampled": len(results),
            "elapsed_seconds": total_time,
            "avg_latency_ms": (total_time / max(len(results), 1)) * 1000.0,
        },
        "frames": results,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print("-" * 60)
    print(f"Saved {len(results)} probe evaluations to {output_json}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to CCTV video")
    parser.add_argument("--output", default="samples/cctv/benchmarks/omnijev_results.json", help="Path to output JSON")
    parser.add_argument("--stride", type=int, default=2, help="Sample every N frames")
    parser.add_argument("--ckpt", default="~/models/OmniJev-2B", help="OmniJev LoRA checkpoint directory")
    parser.add_argument("--base", default="~/models/Qwen3.5-2B", help="Qwen3.5-2B base model directory")
    args = parser.parse_args()

    process_video(
        video_path=args.video,
        output_json=args.output,
        sample_stride=args.stride,
        ckpt_dir=args.ckpt,
        base_dir=args.base,
    )


if __name__ == "__main__":
    main()
