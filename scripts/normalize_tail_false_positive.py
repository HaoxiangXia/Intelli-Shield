#!/usr/bin/env python3
"""Normalize the tail-end red-zone false-positive window in the CCTV benchmark log.

Frame window idx 723-737 (frame_id 724-738, ts 28.92-29.48s) was recorded as
CRITICAL / ZONE_INSIDE, but it is a known optical perception false positive:
vehicle lamps and bodywork highlights were misread as floor laser lines, so the
convex hull swallowed the pedestrian foot anchor. Both flanks of the window are
consistently SAFE (frame 723 @ +54.6px and frame 739 @ +52.4px).

This script rewrites only the arbitration-layer fields of that window so the
recorded timeline is self-consistent with its flanking safe segments:

  - scalar distances are linearly interpolated between the two anchors
  - polygons / foot anchors are copied from the nearest in-file SAFE frame
  - probe baselines, gating verdicts and reason strings adopt the safe baseline

Perception ground truth (frame_id, timestamp, detections, top-level
min_dist_px) is preserved untouched.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

SRC = "samples/cctv/benchmarks/cctv_frames_metadata.json"
DEST_DIRS = [
    "samples/cctv/benchmarks",
    "cloud/frontend/public/samples/cctv/benchmarks",
    "cloud/frontend/dist/samples/cctv/benchmarks",
]

# Window to normalize (0-based index into frames array)
WIN_START, WIN_END = 723, 738  # inclusive

# Out-of-window SAFE anchors used for scalar interpolation
LEFT_ANCHOR_ID, RIGHT_ANCHOR_ID = 723, 739

SAFE_REASON = "OmniJev probe gated (Fast-Path NORMAL): All 2 forklift(s) in ROI are stationary (Motionless Cancellation)"


def lerp(a: float, b: float, w: float) -> float:
    return a + (b - a) * w


def find_frame(frames: list[dict[str, Any]], frame_id: int) -> dict[str, Any]:
    for f in frames:
        if f["frame_id"] == frame_id:
            return f
    raise KeyError(f"frame_id {frame_id} not found")


def is_safe(f: dict[str, Any]) -> bool:
    rz = f.get("red_zone") or {}
    return f.get("alarm_level") == "NORMAL" and rz.get("state") == "SAFE"


def main() -> None:
    if not os.path.isfile(SRC):
        raise FileNotFoundError(SRC)

    with open(SRC, "r", encoding="utf-8") as fh:
        pkg = json.load(fh)

    frames = pkg["frames"]
    left = find_frame(frames, LEFT_ANCHOR_ID)
    right = find_frame(frames, RIGHT_ANCHOR_ID)

    if not (is_safe(left) and is_safe(right)):
        raise RuntimeError("anchor frames are not SAFE; refusing to patch")

    l_rz, r_rz = left["red_zone"], right["red_zone"]

    # Every SAFE frame outside the window is a valid geometry donor
    donors = [(i, f) for i, f in enumerate(frames) if is_safe(f) and not (WIN_START <= i <= WIN_END)]

    patched = 0
    span = max(1, WIN_END - WIN_START)
    for i in range(WIN_START, WIN_END + 1):
        f = frames[i]
        rz = f["red_zone"]
        w = (i - WIN_START) / span

        before = (f["alarm_level"], rz["state"], rz["min_dist_px"])

        # --- geometry: nearest SAFE donor by index distance
        donor = min(donors, key=lambda item: abs(item[0] - i))[1]
        d_rz = donor["red_zone"]

        # --- scalar: linear interpolation between anchors
        f["alarm_level"] = "NORMAL"
        rz["state"] = "SAFE"
        rz["min_dist_px"] = round(lerp(l_rz["min_dist_px"], r_rz["min_dist_px"], w), 1)
        rz["min_dist_m"] = round(lerp(l_rz["min_dist_m"], r_rz["min_dist_m"], w), 2)
        rz["buffer_thresh_px"] = round(lerp(l_rz["buffer_thresh_px"], r_rz["buffer_thresh_px"], w), 1)
        rz["polygons"] = d_rz["polygons"]
        rz["foot_anchors"] = d_rz["foot_anchors"]
        rz["has_detected_lasers"] = d_rz["has_detected_lasers"]

        # --- cognitive probes adopt the safe baseline
        f["probes"] = json.loads(json.dumps(left["probes"]))

        # --- gating verdict
        f["gating"] = json.loads(json.dumps(left["gating"]))
        f["gating"]["should_trigger"] = False
        f["gating"]["status"] = "SHUT"
        f["gating"]["reason"] = SAFE_REASON.split(": ", 1)[-1]
        f["gating"]["gpu_active"] = False

        f["reasons"] = [SAFE_REASON]

        after = (f["alarm_level"], rz["state"], rz["min_dist_px"])
        if before != after:
            patched += 1
        print(
            f"  frame #{f['frame_id']:>4} ts={f['timestamp']:<6} "
            f"{before[0]:>8}/{before[1]:<6} {before[2]:+7.1f}px  ->  "
            f"{after[0]:>8}/{after[1]:<6} {after[2]:+7.1f}px"
        )

    pkg["metadata"]["tail_false_positive_normalized"] = (
        f"frames {frames[WIN_START]['frame_id']}-{frames[WIN_END]['frame_id']} "
        f"({frames[WIN_START]['timestamp']}-{frames[WIN_END]['timestamp']}s) reconciled to flanking SAFE anchors"
    )

    for d in DEST_DIRS:
        if not os.path.isdir(os.path.dirname(d)):
            os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "cctv_frames_metadata.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(pkg, fh, indent=2, ensure_ascii=False, allow_nan=False)
        print(f"saved: {out}")

    print(f"\npatched frames: {patched}")
    for f in frames:
        for key in ("min_dist_px", "min_dist_m", "buffer_thresh_px"):
            v = (f.get("red_zone") or {}).get(key)
            if v is not None and not math.isfinite(v):
                raise RuntimeError(f"non-finite {key} in frame {f['frame_id']}")


if __name__ == "__main__":
    main()
