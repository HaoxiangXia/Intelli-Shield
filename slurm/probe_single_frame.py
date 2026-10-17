"""Single Frame OmniJev (OmniJev-2B) Probe Evaluation on RTX 3090.

Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
Runtime: mso.infer.MSO1 (LoRA on Qwen3.5-2B backbone)
"""

from __future__ import annotations
import argparse
import json
import os
import time
from typing import Dict, Any
from PIL import Image


def resize_image_if_needed(image_path: str, max_dim: int = 1280) -> str:
    """Resizes high-resolution camera images to standard CCTV inference size."""
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            out_path = f"/tmp/resized_{os.path.basename(image_path)}.jpg"
            im_resized.save(out_path, format="JPEG", quality=90)
            print(f">>> Resized input image from {w}x{h} to {new_w}x{new_h} for optimal VLM token budget.")
            return out_path
    return image_path


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


def run_probe_evaluation(image_path: str, ckpt_dir: str, base_dir: str) -> Dict[str, Any]:
    from mso.infer import MSO1

    print(f">>> Loading OmniJev-2B: ckpt={ckpt_dir}, base={base_dir}")
    model = MSO1(ckpt_dir, base_dir)
    print(">>> OmniJev-2B loaded on CUDA successfully.")

    processed_image_path = resize_image_if_needed(image_path, max_dim=1280)

    t0 = time.perf_counter()
    answers = model.system_one(
        {"images": [processed_image_path]},
        PROBE_QUESTIONS,
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0

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
        "latency_ms": round(latency_ms, 1),
        "backend": "OmniJev-2B (MSO1 on RTX 3090)",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument("--ckpt", default=os.path.expanduser("~/models/OmniJev-2B"), help="Path to LoRA checkpoint")
    parser.add_argument("--base", default=os.path.expanduser("~/models/Qwen3.5-2B"), help="Path to base model")
    parser.add_argument("--output", default="samples/cctv/benchmarks/probe_real_cctv.json", help="Path to output JSON")
    args = parser.parse_args()

    print("=" * 65)
    print(" OmniJev Real CCTV Frame Probe Inference on RTX 3090")
    print("=" * 65)
    print(f"Target Image: {args.image}")
    print(f"Model Ckpt  : {args.ckpt}")
    print(f"Base Model  : {args.base}")
    print("-" * 65)

    probes = run_probe_evaluation(args.image, args.ckpt, args.base)

    print("=" * 65)
    print(" PROBE INFERENCE RESULTS:")
    print(f"  Collision Risk P(coll): {probes['collision_risk']}")
    print(f"  Worker Awareness      : {probes['worker_awareness']}")
    print(f"  Hazard Threat Score   : {probes['threat_score']} / 3.0")
    print(f"  Inference Latency     : {probes['latency_ms']} ms")
    print(f"  Engine Backend        : {probes['backend']}")
    print("=" * 65)

    out_data = {
        "metadata": {
            "image": args.image,
            "model": "OmniJev-2B (tinnel123/OmniJev-2B + Qwen3.5-2B)",
            "device": "NVIDIA GeForce RTX 3090 (24GB)",
            "backend": probes["backend"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "probes": probes,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"Saved probe results to: {args.output}")


if __name__ == "__main__":
    main()
