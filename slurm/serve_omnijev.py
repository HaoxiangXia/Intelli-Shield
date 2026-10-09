"""OmniJev Real-Time Decision Probe Service on RTX 3090 (Slurm Compute Node)."""

from __future__ import annotations
import base64
import os
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
    from qev import Choice, Noul, Score, Model
except ImportError:
    Model = None
    Choice = Noul = Score = None

app = FastAPI(title="OmniJev System 1 Decision Probe Service")

# Global model handle
MODEL_INSTANCE = None


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
        model_name = os.getenv("OMNIJEV_MODEL", "OneJev-0.8B")
        print(f"Loading OmniJev model: {model_name} on CUDA...")
        if Model is not None:
            MODEL_INSTANCE = Model(model_name, device="cuda")
        else:
            print("Warning: qev library not installed; running in stub mode.")
    return MODEL_INSTANCE


# The 3 standardized decision probes
def build_probes():
    return {
        "collision_risk": Noul(
            "In this industrial CCTV camera view, is any forklift in dangerous proximity or on an active collision trajectory with a pedestrian?"
        ),
        "worker_awareness": Choice(
            "What is the primary attention state of workers near active machinery in this scene?",
            ["unaware/distracted", "actively looking/yielding", "physically separated in walkway"],
        ),
        "threat_score": Score(
            "Rate the overall collision hazard severity of this operational zone from 0 (safe clearance) to 3 (imminent critical impact).",
            levels=4,
        ),
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

    if model is not None and Noul is not None:
        # Real OmniJev single forward pass inference on 3090
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        questions = build_probes()
        results = model.evaluate(img_rgb, questions)

        coll_obj = results["collision_risk"]
        coll_val = getattr(coll_obj, "noul", getattr(coll_obj, "probability", 0.0))
        probes_dict = {
            "collision_risk": float(coll_val),
            "worker_awareness": {
                choice: float(prob)
                for choice, prob in results["worker_awareness"].probabilities.items()
            },
            "threat_score": float(results["threat_score"].score),
        }
    else:
        # Stub response if qev not installed on test host
        probes_dict = {
            "collision_risk": 0.42,
            "worker_awareness": {
                "unaware/distracted": 0.60,
                "actively looking/yielding": 0.30,
                "physically separated in walkway": 0.10,
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
    return {"status": "ok", "cuda": True, "model": os.getenv("OMNIJEV_MODEL", "OneJev-0.8B")}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
