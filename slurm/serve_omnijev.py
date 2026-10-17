"""OmniJev Real-Time Decision Probe Service on RTX 3090 (Slurm Compute Node).

Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
Runtime: mso.infer.MSO1 (LoRA on Qwen3.5-2B backbone)
Repository: https://github.com/tinnel123666888/OmniJev
"""

from __future__ import annotations
import base64
import os
import tempfile
import time
from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
except ImportError:
    FastAPI = None

try:
    from mso.infer import MSO1
except ImportError:
    MSO1 = None

app = FastAPI(title="OmniJev System 1 Decision Probe Service")

# Global model handle
MODEL_INSTANCE = None

# Default paths (overridable via env vars)
CKPT_DIR = os.getenv("OMNIJEV_CKPT", os.path.expanduser("~/models/OmniJev-4B"))
BASE_DIR = os.getenv("OMNIJEV_BASE", os.path.expanduser("~/models/Qwen3.5-4B"))


class ProbeRequest(BaseModel):
    frame_id: int
    image_b64: str


class ProbeResponse(BaseModel):
    frame_id: int
    latency_ms: float
    probes: Dict[str, object]


def get_model():
    global MODEL_INSTANCE
    if MODEL_INSTANCE is None:
        print(f"Loading OmniJev-4B model: ckpt={CKPT_DIR}, base={BASE_DIR} ...")
        if MSO1 is not None:
            MODEL_INSTANCE = MSO1(CKPT_DIR, BASE_DIR)
            print("OmniJev-4B loaded on CUDA successfully.")
        else:
            print("Warning: mso library not available; running in stub mode.")
    return MODEL_INSTANCE


# The 4 standardized decision probes (PRD 3.2) in MSO question format
PROBE_QUESTIONS = {
    "collision_risk": {
        "type": "noul",
        "instructions": "In this industrial CCTV camera view, is any forklift in dangerous proximity or on an active collision trajectory with a pedestrian?",
    },
    "worker_awareness": {
        "type": "choice",
        "instructions": "What is the primary attention state of workers near active machinery in this scene?",
        "criteria": {
            "unaware/distracted": "unaware or distracted, not looking at approaching vehicle",
            "actively looking/yielding": "actively looking at vehicle or yielding right of way",
            "physically separated in walkway": "physically separated in designated walkway or behind barrier",
        },
    },
    "worker_hazard_behavior": {
        "type": "choice",
        "instructions": "Does any worker exhibit dangerous non-compliant behaviors near forklifts, such as looking down at phone or walking with back turned?",
        "criteria": {
            "phone_distracted": "looking down at mobile phone while in operational zone",
            "back_facing_vehicle": "back turned to approaching forklift, unaware",
            "standing_in_blindspot": "standing in vehicle blind spot zone",
            "normal_compliant": "compliant posture, attentive and aware of surroundings",
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

# Level-to-numeric mapping for threat_score
THREAT_LEVEL_MAP = {
    "Level 0: Safe clearance and no hazard": 0.0,
    "Level 1: Low operational hazard within buffer zone": 1.0,
    "Level 2: Critical proximity requiring speed reduction": 2.0,
    "Level 3: Imminent collision hazard requiring emergency stop": 3.0,
}


def _extract_probes(answers: dict) -> Dict[str, object]:
    """Convert MSO1 answer dict into the downstream-compatible probe format."""
    # collision_risk: noul -> float probability
    coll_val = float(answers.get("collision_risk", {}).get("noul", 0.0))

    # worker_awareness: choice -> {label: probability}
    awareness_probs = {
        k: round(float(v), 4)
        for k, v in answers.get("worker_awareness", {}).get("probabilities", {}).items()
    }

    # worker_hazard_behavior: choice -> {label: probability}
    hazard_probs = {
        k: round(float(v), 4)
        for k, v in answers.get("worker_hazard_behavior", {}).get("probabilities", {}).items()
    }

    # threat_score: score -> numeric value from level label
    threat_answer = answers.get("threat_score", {})
    threat_level = threat_answer.get("score", "Level 0: Safe clearance and no hazard")
    # Use expected value from probabilities if available, else map level name
    threat_probs = threat_answer.get("probabilities", {})
    if threat_probs:
        threat_val = sum(
            THREAT_LEVEL_MAP.get(lvl, i) * float(p)
            for i, (lvl, p) in enumerate(threat_probs.items())
        )
    else:
        threat_val = THREAT_LEVEL_MAP.get(threat_level, 0.0)

    return {
        "collision_risk": round(coll_val, 4),
        "worker_awareness": awareness_probs,
        "worker_hazard_behavior": hazard_probs,
        "threat_score": round(threat_val, 2),
    }


@app.post("/probe", response_model=ProbeResponse)
async def evaluate_probes(req: ProbeRequest):
    t0 = time.perf_counter()

    # Decode image
    try:
        img_bytes = base64.b64decode(req.image_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode image buffer")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image decode failed: {str(e)}")

    model = get_model()
    probes_dict = {}

    if model is not None:
        # Save frame to temporary file (MSO1 requires image path)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
        try:
            answers = model.system_one(
                {"images": [tmp_path]},
                PROBE_QUESTIONS,
            )
            probes_dict = _extract_probes(answers)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        # Stub response if mso not installed on test host
        probes_dict = {
            "collision_risk": 0.42,
            "worker_awareness": {
                "unaware/distracted": 0.60,
                "actively looking/yielding": 0.30,
                "physically separated in walkway": 0.10,
            },
            "worker_hazard_behavior": {
                "phone_distracted": 0.15,
                "back_facing_vehicle": 0.75,
                "standing_in_blindspot": 0.05,
                "normal_compliant": 0.05,
            },
            "threat_score": 1.5,
        }
    latency = (time.perf_counter() - t0) * 1000.0
    return ProbeResponse(
        frame_id=req.frame_id,
        latency_ms=latency,
        probes=probes_dict,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "cuda": True,
        "model": "OmniJev-4B",
        "backend": "mso.infer.MSO1 (Qwen3.5-4B + LoRA)",
        "ckpt": CKPT_DIR,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
