"""Single Frame OmniJev (OneJev-0.8B) Probe Evaluation on RTX 3090."""

from __future__ import annotations
import argparse
import base64
import json
import os
import subprocess
import sys
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


def to_data_uri(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def run_probe_evaluation(image_path: str, model_dir: str, port: int = 8000) -> Dict[str, Any]:
    import urllib.request
    from qev import Client, Choice, Noul, Score

    base_url = f"http://127.0.0.1:{port}"
    server_proc = None

    def server_ready():
        try:
            req = urllib.request.Request(f"{base_url}/v1/models")
            with urllib.request.urlopen(req, timeout=1) as r:
                return r.status == 200
        except Exception:
            return False

    if not server_ready():
        print(f">>> Launching qev server for {model_dir} on GPU...")
        cmd = [
            sys.executable,
            "-m",
            "qev.cli",
            "serve",
            "--model",
            model_dir,
            "--multimodal",
            "--port",
            str(port),
        ]
        server_proc = subprocess.Popen(cmd)
        print(">>> Waiting for OneJev-0.8B weights and CUDA graphs to initialize...")
        for _ in range(90):
            if server_ready():
                break
            time.sleep(1)
        if not server_ready():
            if server_proc:
                server_proc.kill()
            raise RuntimeError("qev server failed to start within 90s")
        print(">>> OneJev-0.8B server is ONLINE and READY!")
    else:
        print(">>> Found existing active qev server.")

    client = Client(base_url=base_url)
    questions = {
        "collision_risk": Noul(
            "In this industrial CCTV camera view, is any forklift in dangerous proximity or on an active collision trajectory with a pedestrian?"
        ),
        "worker_awareness": Choice(
            "What is the primary attention state of workers near active machinery in this scene?",
            {
                "unaware": "unaware or distracted",
                "yielding": "actively looking or yielding",
                "separated": "physically separated in designated walkway",
            },
        ),
        "threat_score": Score(
            "Rate the overall collision hazard severity of this operational zone from 0 (clear) to 3 (imminent impact).",
            [
                "Level 0: Safe clearance and no hazard",
                "Level 1: Low operational hazard within buffer zone",
                "Level 2: Critical proximity requiring speed reduction",
                "Level 3: Imminent collision hazard requiring emergency stop",
            ],
        ),
    }

    processed_image_path = resize_image_if_needed(image_path, max_dim=1280)
    img_uri = to_data_uri(processed_image_path)

    t0 = time.perf_counter()
    try:
        resp = client.system_one(
            state={"scene": "<image:1>"},
            media=[{"type": "image", "data": img_uri}],
            questions=questions,
        )
    finally:
        if server_proc:
            print(">>> Stopping temporary qev server...")
            server_proc.terminate()
            server_proc.wait(5)

    latency_ms = (time.perf_counter() - t0) * 1000.0

    coll_prob = float(resp.answers["collision_risk"].raw.get("noul", 0.0))
    worker_probs = resp.answers["worker_awareness"].raw.get("probabilities", {})
    threat_val = float(resp.answers["threat_score"].raw.get("score", 0.0))

    return {
        "collision_risk": round(coll_prob, 4),
        "worker_awareness": worker_probs,
        "threat_score": round(threat_val, 2),
        "latency_ms": round(latency_ms, 1),
        "backend": "OneJev-0.8B (qev server on RTX 3090)",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to image file")
    parser.add_argument("--model", default="/archive/xhx/models/OneJev-0.8B", help="Path to model weights")
    parser.add_argument("--output", default="samples/cctv/benchmarks/probe_real_cctv.json", help="Path to output JSON")
    args = parser.parse_args()

    print("=" * 65)
    print(" OmniJev Real CCTV Frame Probe Inference on RTX 3090")
    print("=" * 65)
    print(f"Target Image: {args.image}")
    print(f"Model Path  : {args.model}")
    print("-" * 65)

    probes = run_probe_evaluation(args.image, args.model)

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
            "model": "OneJev-0.8B",
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
