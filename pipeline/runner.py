"""Main orchestrator for Intelli-Shield perception-decision pipeline."""

from __future__ import annotations
import argparse
import json
import sys
import time

from .detector import YOLODetector
from .models import FrameDecision
from .omnijev_engine import OmniJevEngine
from .risk_fusion import RiskFusionEngine
from .video_source import VideoSource


def run_pipeline(
    video_path: str,
    endpoint: str = "http://127.0.0.1:8000/probe",
    replay_log: str = None,
    target_fps: float = 10.0,
    yolo_model: str = "yolo26n.pt",
    max_frames: int = 0,
):
    print("=" * 60)
    print("  Intelli-Shield: CCTV + YOLO + OmniJev System 1 Pipeline")
    print("=" * 60)
    print(f"Video Source   : {video_path}")
    print(f"OmniJev Endpoint: {endpoint}")
    if replay_log:
        print(f"Replay Log File: {replay_log}")
    print(f"Target FPS     : {target_fps}")
    print("-" * 60)

    video = VideoSource(video_path=video_path, target_fps=target_fps, loop=False)
    detector = YOLODetector(model_path=yolo_model)
    engine = OmniJevEngine(endpoint_url=endpoint, replay_log_path=replay_log)
    fusion = RiskFusionEngine()

    processed_frames = 0
    t0 = time.time()
    for frame_id, timestamp, frame_bgr in video.frames():
        # 1. Perception Layer (YOLO)
        perception = detector.detect(frame_bgr, frame_id, timestamp)

        # 2. Decision Layer (OmniJev Probes)
        probes = None
        if (perception.pedestrians and perception.forklifts) or engine.replay_cache:
            probes = engine.evaluate(frame_bgr, frame_id)
        # 3. Risk Fusion Engine
        decision: FrameDecision = fusion.arbitrate(frame_id, timestamp, perception, probes)

        # 4. Stream output (Console visualization)
        status_color = {
            "NORMAL": "\033[92m[NORMAL]\033[0m",
            "WARNING": "\033[93m[WARNING]\033[0m",
            "CRITICAL": "\033[91m[CRITICAL]\033[0m",
        }.get(decision.alarm_level.value, "[UNKNOWN]")

        p_cnt = len(decision.perception.pedestrians)
        f_cnt = len(decision.perception.forklifts)
        dist_str = f"{decision.perception.min_distance_px:.1f}px" if decision.perception.min_distance_px else "N/A"

        probe_str = "No Probes"
        if decision.probes:
            p = decision.probes
            probe_str = f"P(coll)={p.collision_risk:.2f} | Score={p.threat_score:.1f} | {p.latency_ms:.0f}ms"

        print(
            f"Frame #{frame_id:04d} | {status_color} | Ped: {p_cnt} | Forklift: {f_cnt} | Dist: {dist_str:>7} | {probe_str}"
        )

        processed_frames += 1
        if max_frames > 0 and processed_frames >= max_frames:
            break

    total_time = time.time() - t0
    fps = processed_frames / max(total_time, 0.001)
    print("-" * 60)
    print(f"Finished {processed_frames} frames in {total_time:.2f}s ({fps:.1f} FPS)")

def main():
    parser = argparse.ArgumentParser(description="Intelli-Shield CCTV Perception-Decision Runner")
    parser.add_argument("--video", type=str, default="samples/cctv/videos/demo_forklift.mp4", help="Path to CCTV video")
    parser.add_argument("--endpoint", type=str, default="http://127.0.0.1:8000/probe", help="OmniJev probe endpoint")
    parser.add_argument("--replay", type=str, default=None, help="Path to precomputed Slurm JSON log")
    parser.add_argument("--fps", type=float, default=10.0, help="Target processing FPS")
    parser.add_argument("--yolo", type=str, default="yolo26n.pt", help="YOLO model path")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames to process (0 = all)")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        endpoint=args.endpoint,
        replay_log=args.replay,
        target_fps=args.fps,
        yolo_model=args.yolo,
        max_frames=args.max_frames,
    )


if __name__ == "__main__":
    main()
