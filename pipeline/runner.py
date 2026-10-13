"""Main orchestrator for Intelli-Shield perception-decision pipeline."""

from __future__ import annotations
import argparse
import json
import sys
import time

from .detector import YOLODetector
from .gating import SpatialTemporalGate
from .models import FrameDecision
from .omnijev_engine import OmniJevEngine
from .risk_fusion import RiskFusionEngine
from .video_source import VideoSource


def run_pipeline(
    video_path: str,
    endpoint: str = "http://127.0.0.1:8000/probe",
    replay_log: str = None,
    target_fps: float = 10.0,
    cfg_path: str = "models/yolov4-custom-hebei.cfg",
    weights_path: str = "models/yolov4-custom-hebei_last.weights",
    names_path: str = "models/voc-hebei.names",
    conf_threshold: float = 0.25,
    max_frames: int = 0,
    enable_gating: bool = True,
    gating_dist_px: float = 250.0,
    static_frames: int = 3,
):
    print("=" * 60)
    print("  Intelli-Shield: CCTV + YOLO + OmniJev System 1 Pipeline")
    print("=" * 60)
    print(f"Video Source   : {video_path}")
    print(f"OmniJev Endpoint: {endpoint}")
    if replay_log:
        print(f"Replay Log File: {replay_log}")
    print(f"Target FPS     : {target_fps}")
    print(f"OmniJev Gating : {'ENABLED (SpatialTemporalGate)' if enable_gating else 'DISABLED'}")
    print("-" * 60)

    video = VideoSource(video_path=video_path, target_fps=target_fps, loop=False)
    detector = YOLODetector(
        cfg_path=cfg_path,
        weights_path=weights_path,
        names_path=names_path,
        conf_threshold=conf_threshold,
    )
    engine = OmniJevEngine(endpoint_url=endpoint, replay_log_path=replay_log)
    fusion = RiskFusionEngine()
    gate = (
        SpatialTemporalGate(
            trigger_distance_px=gating_dist_px,
            static_frame_threshold=static_frames,
        )
        if enable_gating
        else None
    )
    processed_frames = 0
    t0 = time.time()
    for frame_id, timestamp, frame_bgr in video.frames():
        # 1. Perception Layer (YOLO)
        perception = detector.detect(frame_bgr, frame_id, timestamp)

        # 2. Decision Layer (SpatialTemporalGate -> OmniJev Probes)
        gate_decision = None
        should_probe = False

        if enable_gating and gate is not None:
            gate_decision = gate.evaluate(perception)
            should_probe = gate_decision.should_trigger
        else:
            should_probe = bool(perception.pedestrians and perception.forklifts)

        probes = None
        if should_probe:
            probes = engine.evaluate(frame_bgr, frame_id)

        # 3. Risk Fusion Engine
        decision: FrameDecision = fusion.arbitrate(
            frame_id, timestamp, perception, probes, gating=gate_decision
        )
        # 4. Stream output (Console visualization)
        status_color = {
            "NORMAL": "\033[92m[NORMAL]\033[0m",
            "WARNING": "\033[93m[WARNING]\033[0m",
            "CRITICAL": "\033[91m[CRITICAL]\033[0m",
        }.get(decision.alarm_level.value, "[UNKNOWN]")

        p_cnt = len(decision.perception.pedestrians)
        f_cnt = len(decision.perception.forklifts)
        dist_str = f"{decision.perception.min_distance_px:.1f}px" if decision.perception.min_distance_px else "N/A"

        rz = decision.red_zone
        rz_str = f"RedZone: {rz.state.value}({rz.min_dist_px:+.1f}px/{rz.min_dist_m:+.2f}m)" if rz and rz.min_dist_px != float("inf") else "RedZone: SAFE"

        probe_str = "Gated (Skip OmniJev)"
        if gate_decision and not gate_decision.should_trigger:
            probe_str = f"Gate [SHUT]: {gate_decision.reason[:36]}"
        elif decision.probes:
            p = decision.probes
            probe_str = f"Gate [OPEN] -> P(coll)={p.collision_risk:.2f} | Score={p.threat_score:.1f} | {p.latency_ms:.0f}ms"
        elif gate_decision and gate_decision.should_trigger:
            probe_str = "Gate [OPEN] -> Probes Unavailable (Timeout/Mock)"

        print(
            f"Frame #{frame_id:04d} | {status_color} | {rz_str} | Ped: {p_cnt} | Forklift: {f_cnt} | Dist: {dist_str:>7} | {probe_str}"
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
    parser.add_argument("--cfg", type=str, default="models/yolov4-custom-hebei.cfg", help="YOLOv4 cfg path")
    parser.add_argument("--weights", type=str, default="models/yolov4-custom-hebei_last.weights", help="YOLOv4 weights path")
    parser.add_argument("--names", type=str, default="models/voc-hebei.names", help="YOLOv4 class names path")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames to process (0 = all)")
    parser.add_argument("--no-gating", action="store_true", help="Disable spatial-temporal gating filter")
    parser.add_argument("--gating-dist", type=float, default=250.0, help="Gating distance trigger threshold in px")
    parser.add_argument("--static-frames", type=int, default=3, help="Consecutive frames to cancel stationary forklift")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        endpoint=args.endpoint,
        replay_log=args.replay,
        target_fps=args.fps,
        cfg_path=args.cfg,
        weights_path=args.weights,
        names_path=args.names,
        conf_threshold=args.conf,
        max_frames=args.max_frames,
        enable_gating=not args.no_gating,
        gating_dist_px=args.gating_dist,
        static_frames=args.static_frames,
    )


if __name__ == "__main__":
    main()
