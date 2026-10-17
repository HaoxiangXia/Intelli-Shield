"""End-to-End Batch Inference with OmniJev (OmniJev-2B) on RTX 3090.

Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
Runtime: mso.infer.MSO1 (LoRA on Qwen3.5-2B backbone)
"""

from __future__ import annotations
import argparse
import json
import os
import tempfile
import time
from typing import Dict, List
import cv2

try:
    from mso.infer import MSO1
except ImportError:
    print("Error: mso library not found in python environment.")
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
    worker_probs = answers.get("worker_awareness", {}).get("probabilities", {})
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
        "collision_risk": round(coll_prob, 4),
        "worker_awareness": worker_probs,
        "threat_score": round(threat_val, 2),
    }


def run_batch_evaluation(
    video_path: str,
    output_json: str,
    ckpt_dir: str = "~/models/OmniJev-2B",
    base_dir: str = "~/models/Qwen3.5-2B",
    stride: int = 5,
    max_frames: int = 20,
):
    ckpt_dir = os.path.expanduser(ckpt_dir)
    base_dir = os.path.expanduser(base_dir)

    print("=" * 65)
    print(" Intelli-Shield: Real RTX 3090 OmniJev System 1 Batch Inference")
    print("=" * 65)
    print(f"Video File : {video_path}")
    print(f"Model Ckpt : {ckpt_dir}")
    print(f"Base Model : {base_dir}")
    print(f"Output Log : {output_json}")
    print(f"Frame Stride: {stride} (evaluating every {stride} frames)")
    print("-" * 65)

    print(">>> Loading OmniJev-2B into RTX 3090 VRAM...")
    model = MSO1(ckpt_dir, base_dir)
    print(">>> OmniJev-2B loaded successfully.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video file: {video_path}")

    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0

    tmp_dir = tempfile.mkdtemp(prefix="omnijev_real_")
    frame_idx = 0
    sampled_results = []

    t_all_start = time.time()

    try:
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % stride != 0:
                continue

            frame_time = frame_idx / fps
            temp_path = os.path.join(tmp_dir, f"frame_{frame_idx:05d}.jpg")
            cv2.imwrite(temp_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Send to OmniJev-2B System 1 Model
            t0 = time.perf_counter()
            try:
                answers = model.system_one(
                    {"images": [temp_path]},
                    PROBE_QUESTIONS,
                )
                probes_data = _extract_probes(answers)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            dt_ms = (time.perf_counter() - t0) * 1000.0

            frame_record = {
                "frame_id": frame_idx,
                "timestamp": round(frame_time, 3),
                "probes": {
                    "collision_risk": probes_data["collision_risk"],
                    "worker_awareness": probes_data["worker_awareness"],
                    "threat_score": probes_data["threat_score"],
                    "latency_ms": round(dt_ms, 1),
                },
            }
            sampled_results.append(frame_record)

            print(
                f"Frame #{frame_idx:04d} ({frame_time:4.1f}s) | "
                f"P(coll)={probes_data['collision_risk']:.2f} | Threat={probes_data['threat_score']:.2f} | "
                f"Latency={dt_ms:.1f}ms"
            )

            if max_frames > 0 and len(sampled_results) >= max_frames:
                break
    finally:
        cap.release()

    total_eval_time = time.time() - t_all_start
    avg_latency = (
        sum(r["probes"]["latency_ms"] for r in sampled_results) / len(sampled_results)
        if sampled_results
        else 0.0
    )

    output_payload = {
        "metadata": {
            "video_path": video_path,
            "model": "OmniJev-2B (tinnel123/OmniJev-2B + Qwen3.5-2B)",
            "device": "NVIDIA GeForce RTX 3090 (24GB)",
            "frames_analyzed": len(sampled_results),
            "total_elapsed_sec": round(total_eval_time, 2),
            "avg_latency_ms": round(avg_latency, 1),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "frames": sampled_results,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print("-" * 65)
    print(f" SUCCESS: Saved {len(sampled_results)} real 3090 probe evaluations to:")
    print(f" {output_json}")
    print(f" Average System 1 Latency: {avg_latency:.1f} ms")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="/archive/xhx/Intelli-Shield/samples/cctv/videos/demo_forklift.mp4")
    parser.add_argument("--output", default="/archive/xhx/Intelli-Shield/samples/cctv/benchmarks/omnijev_results_real3090.json")
    parser.add_argument("--ckpt", default="/archive/xhx/models/OmniJev-2B")
    parser.add_argument("--base", default="/archive/xhx/models/Qwen3.5-2B")
    parser.add_argument("--stride", type=int, default=3)
    parser.add_argument("--max-frames", type=int, default=15)
    args = parser.parse_args()

    run_batch_evaluation(
        video_path=args.video,
        output_json=args.output,
        ckpt_dir=args.ckpt,
        base_dir=args.base,
        stride=args.stride,
        max_frames=args.max_frames,
    )


if __name__ == "__main__":
    main()
