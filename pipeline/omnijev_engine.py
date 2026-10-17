"""OmniJev System 1 Decision Engine client supporting remote Slurm worker and replay."""

from __future__ import annotations
import base64
import json
import os
import time
from typing import Dict, Optional
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import requests
except ImportError:
    requests = None

from .models import OmniJevProbes


class OmniJevEngine:
    """Client for OmniJev System 1 decision probes."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        replay_log_path: Optional[str] = None,
        timeout: float = 3.0,
    ):
        self.endpoint_url = endpoint_url or os.getenv("OMNIJEV_ENDPOINT", "http://127.0.0.1:8000/probe")
        self.replay_log_path = replay_log_path
        self.timeout = timeout
        self.replay_cache: Dict[int, OmniJevProbes] = {}

        if self.replay_log_path and os.path.exists(self.replay_log_path):
            self._load_replay_log(self.replay_log_path)

    def _load_replay_log(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("frames", []):
                fid = item.get("frame_id")
                probes = item.get("probes", {})
                hazard = probes.get("worker_hazard_behavior")
                if not hazard:
                    unaware = probes.get("worker_awareness", {}).get("unaware", 0.0)
                    hazard = (
                        {"back_facing_vehicle": 0.82, "phone_distracted": 0.15, "normal_compliant": 0.03}
                        if unaware >= 0.50
                        else {"normal_compliant": 0.90, "back_facing_vehicle": 0.05, "phone_distracted": 0.05}
                    )
                self.replay_cache[fid] = OmniJevProbes(
                    collision_risk=probes.get("collision_risk", 0.0),
                    worker_awareness=probes.get("worker_awareness", {}),
                    worker_hazard_behavior=hazard,
                    threat_score=probes.get("threat_score", 0.0),
                    latency_ms=probes.get("latency_ms", 35.0),
                )
    def evaluate(self, frame_bgr: np.ndarray, frame_id: int) -> Optional[OmniJevProbes]:
        """Evaluates OmniJev probes on the full-frame scene."""
        # 1. Replay log takes precedence if available
        if frame_id in self.replay_cache:
            return self.replay_cache[frame_id]

        # 2. Remote HTTP Inference on 3090 (via Slurm service or SSH tunnel)
        if requests is not None and self.endpoint_url:
            try:
                start_t = time.perf_counter()
                if cv2 is not None:
                    _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    img_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
                else:
                    return None

                payload = {
                    "frame_id": frame_id,
                    "image_b64": img_b64,
                }
                resp = requests.post(self.endpoint_url, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    probes_data = data.get("probes", {})
                    latency = (time.perf_counter() - start_t) * 1000.0
                    hazard = probes_data.get("worker_hazard_behavior")
                    if not hazard:
                        unaware = probes_data.get("worker_awareness", {}).get(
                            "unaware",
                            probes_data.get("worker_awareness", {}).get("unaware/distracted", 0.0),
                        )
                        hazard = (
                            {"back_facing_vehicle": 0.82, "phone_distracted": 0.15, "normal_compliant": 0.03}
                            if unaware >= 0.50
                            else {"normal_compliant": 0.90, "back_facing_vehicle": 0.05, "phone_distracted": 0.05}
                        )
                    return OmniJevProbes(
                        collision_risk=float(probes_data.get("collision_risk", 0.0)),
                        worker_awareness=probes_data.get("worker_awareness", {}),
                        worker_hazard_behavior=hazard,
                        threat_score=float(probes_data.get("threat_score", 0.0)),
                        latency_ms=latency,
                    )
                return None
            except Exception:
                return None

        return None
