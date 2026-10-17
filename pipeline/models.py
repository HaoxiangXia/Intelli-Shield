"""Core data structures and probe contracts for Intelli-Shield pipeline."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple


class AlarmLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RedZoneState(str, Enum):
    INSIDE = "INSIDE"      # < 0m: Pedestrian feet stepped inside red laser exclusion zone
    BUFFER = "BUFFER"      # 0 ~ 0.3m: Within outer perimeter buffer zone
    SAFE = "SAFE"          # > 0.3m: Outside red safety zone


@dataclass
class RedZoneEvaluation:
    state: RedZoneState = RedZoneState.SAFE
    min_dist_px: float = float("inf")  # Negative if inside polygon, positive if outside
    min_dist_m: float = float("inf")   # Estimated metric distance (meters)
    buffer_thresh_px: float = 22.0     # Adaptive buffer threshold in pixels (0.28m)
    violating_pedestrians: List[BoundingBox] = field(default_factory=list)
    polygons: List[List[Tuple[int, int]]] = field(default_factory=list)
    has_detected_lasers: bool = False


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
    red_zone: Optional[RedZoneEvaluation] = None


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
    red_zone: Optional[RedZoneEvaluation] = None


@dataclass
class OmniJevProbes:
    # Probe 1: Noul calibrated binary collision probability [0.0, 1.0]
    collision_risk: float
    # Probe 2: Choice worker attention distribution
    worker_awareness: Dict[str, float]
    # Probe 3: Choice worker hazard behaviors (phone_distracted, back_facing_vehicle, etc.)
    worker_hazard_behavior: Dict[str, float] = field(default_factory=dict)
    # Probe 4: Score expected hazard rating [0.0, 3.0] (4-tier standard)
    threat_score: float = 0.0
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
    red_zone: Optional[RedZoneEvaluation] = None
    # Fleet Traction Interlock control signal (PRD 3.3 / 4.4)
    interlock_engaged: bool = False
    interlocked_forklifts: List[BoundingBox] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
