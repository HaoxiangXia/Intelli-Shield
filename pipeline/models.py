"""Core data structures and probe contracts for Intelli-Shield pipeline."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple


class AlarmLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_name: str  # "person" | "forklift" | "truck"
    track_id: Optional[int] = None


@dataclass
class PerceptionResult:
    frame_id: int
    timestamp: float
    forklifts: List[BoundingBox] = field(default_factory=list)
    pedestrians: List[BoundingBox] = field(default_factory=list)
    detections: List[BoundingBox] = field(default_factory=list)
    min_distance_px: Optional[float] = None


@dataclass
class GatingDecision:
    """Outcome of spatial-temporal gating filter before invoking OmniJev."""
    should_trigger: bool
    active_pedestrians: List[BoundingBox] = field(default_factory=list)
    active_forklifts: List[BoundingBox] = field(default_factory=list)
    driver_pedestrians: List[BoundingBox] = field(default_factory=list)
    static_forklifts: List[BoundingBox] = field(default_factory=list)
    min_dynamic_distance_px: Optional[float] = None
    reason: str = ""

@dataclass
class OmniJevProbes:
    # Probe 1: Noul calibrated binary collision probability [0.0, 1.0]
    collision_risk: float
    # Probe 2: Choice worker attention distribution
    worker_awareness: Dict[str, float]
    # Probe 3: Score expected hazard rating [0.0, 3.0]
    threat_score: float
    latency_ms: float = 0.0


@dataclass
class FrameDecision:
    frame_id: int
    timestamp: float
    perception: PerceptionResult
    probes: Optional[OmniJevProbes]
    alarm_level: AlarmLevel
    reasons: List[str] = field(default_factory=list)
    gating: Optional[GatingDecision] = None

    def to_dict(self) -> dict:
        return asdict(self)
