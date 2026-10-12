"""End-to-End Batch Inference with OmniJev (OneJev-0.8B) on RTX 3090."""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from typing import Dict, List
import cv2

try:
    from qev import Client, Choice, Noul, Score
    from qev.media import data_uri
except ImportError:
    print("Error: qev library not found in python environment.")
    sys.exit(1)


def wait_for_server(url: str, timeout: int = 60) -> bool:
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{url}/v1/models", headers={"User-Agent": "qev-probe"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def build_probes():
    return {
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


def run_batch_evaluation(
    video_path: str,
    output_json: str,
    model_dir: str = "/archive/xhx/models/OneJev-0.8B",
    port: int = 8000,
    stride: int = 5,
    max_frames: int = 20,
):
    print("=" * 65)
    print(" Intelli-Shield: Real RTX 3090 OmniJev System 1 Batch Inference")
    print("=" * 65)
    print(f"Video File : {video_path}")
    print(f"Model Path : {model_dir}")
    print(f"Output Log : {output_json}")
    print(f"Port       : {port}")
    print(f"Frame Stride: {stride} (evaluating every {stride} frames)")
    print("-" * 65)

    base_url = f"http://127.0.0.1:{port}"
    server_proc = None

    # Check if server is already running
    if not wait_for_server(base_url, timeout=2):
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
        print(">>> Waiting for OneJev-0.8B weights to load into RTX 3090 VRAM...")
        if not wait_for_server(base_url, timeout=90):
            if server_proc:
                server_proc.kill()
            raise RuntimeError("qev server failed to initialize within 90 seconds.")
        print(">>> OneJev-0.8B server is ONLINE and READY on GPU!")
    else:
        print(">>> Found existing active qev server.")

    client = Client(base_url=base_url)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        if server_proc:
            server_proc.terminate()
        raise RuntimeError(f"Failed to open video file: {video_path}")

    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0

    temp_img_dir = "/tmp/cctv_eval_frames"
    os.makedirs(temp_img_dir, exist_ok=True)

    frame_idx = 0
    sampled_results = []
    questions = build_probes()

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
            temp_path = os.path.join(temp_img_dir, f"frame_{frame_idx:05d}.jpg")
            cv2.imwrite(temp_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Send to OneJev System 1 Model
            t0 = time.perf_counter()
            resp = client.system_one(
                state={"scene": "<image:1>"},
                media=[{"type": "image", "data": data_uri(temp_path)}],
                questions=questions,
            )
            dt_ms = (time.perf_counter() - t0) * 1000.0

            # Extract calibrated responses
            coll_prob = float(resp.answers["collision_risk"].raw.get("noul", 0.0))
            worker_probs = resp.answers["worker_awareness"].raw.get("probabilities", {})
            threat_val = float(resp.answers["threat_score"].raw.get("score", 0.0))

            frame_record = {
                "frame_id": frame_idx,
                "timestamp": round(frame_time, 3),
                "probes": {
                    "collision_risk": round(coll_prob, 4),
                    "worker_awareness": worker_probs,
                    "threat_score": round(threat_val, 2),
                    "latency_ms": round(dt_ms, 1),
                },
            }
            sampled_results.append(frame_record)

            print(
                f"Frame #{frame_idx:04d} ({frame_time:4.1f}s) | "
                f"P(coll)={coll_prob:.2f} | Threat={threat_val:.2f} | "
                f"Latency={dt_ms:.1f}ms"
            )

            # Cleanup temp frame
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if max_frames > 0 and len(sampled_results) >= max_frames:
                break
    finally:
        cap.release()
        if server_proc:
            print(">>> Stopping temporary qev server...")
            server_proc.terminate()
            server_proc.wait(timeout=10)

    total_eval_time = time.time() - t_all_start
    avg_latency = (
        sum(r["probes"]["latency_ms"] for r in sampled_results) / len(sampled_results)
        if sampled_results
        else 0.0
    )

    output_payload = {
        "metadata": {
            "video_path": video_path,
            "model": "OneJev-0.8B",
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
    parser.add_argument("--model", default="/archive/xhx/models/OneJev-0.8B")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--stride", type=int, default=3)
    parser.add_argument("--max-frames", type=int, default=15)
    args = parser.parse_args()

    run_batch_evaluation(
        video_path=args.video,
        output_json=args.output,
        model_dir=args.model,
        port=args.port,
        stride=args.stride,
        max_frames=args.max_frames,
    )


if __name__ == "__main__":
    main()
