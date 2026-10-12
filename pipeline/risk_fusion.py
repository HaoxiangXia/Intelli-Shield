"""Risk fusion engine combining geometric perception metrics with OmniJev decision probes."""

from __future__ import annotations
from typing import List, Optional, Tuple

from .models import AlarmLevel, FrameDecision, GatingDecision, OmniJevProbes, PerceptionResult


class RiskFusionEngine:
    """Arbitrates alarm level using dual-system inputs."""

    def __init__(
        self,
        collision_prob_critical: float = 0.70,
        collision_prob_warning: float = 0.40,
        dist_critical_px: float = 120.0,
        dist_warning_px: float = 250.0,
        threat_score_critical: float = 2.2,
    ):
        self.collision_prob_critical = collision_prob_critical
        self.collision_prob_warning = collision_prob_warning
        self.dist_critical_px = dist_critical_px
        self.dist_warning_px = dist_warning_px
        self.threat_score_critical = threat_score_critical

    def arbitrate(
        self,
        frame_id: int,
        timestamp: float,
        perception: PerceptionResult,
        probes: Optional[OmniJevProbes],
        gating: Optional[GatingDecision] = None,
    ) -> FrameDecision:
        reasons: List[str] = []
        alarm_level = AlarmLevel.NORMAL

        # Rule 1: No interaction if pedestrians or forklifts absent
        if not perception.pedestrians or not perception.forklifts:
            return FrameDecision(
                frame_id=frame_id,
                timestamp=timestamp,
                perception=perception,
                probes=probes,
                alarm_level=AlarmLevel.NORMAL,
                reasons=["No co-occurring pedestrian and forklift in frame"],
            )
        # Spatial metric reference (prefer dynamic distance from gating if available)
        dist = gating.min_dynamic_distance_px if (gating and gating.min_dynamic_distance_px is not None) else perception.min_distance_px

        # Gating fast-path: if gating actively determined safe / motionless / driver-only
        if gating is not None and not gating.should_trigger:
            reasons.append(f"OmniJev probe gated (Fast-Path NORMAL): {gating.reason}")
            return FrameDecision(
                frame_id=frame_id,
                timestamp=timestamp,
                perception=perception,
                probes=None,
                alarm_level=AlarmLevel.NORMAL,
                reasons=reasons,
                gating=gating,
            )

        if gating is not None and gating.should_trigger:
            reasons.append(f"Gating trigger: {gating.reason}")

        if dist is not None:
            if dist < self.dist_critical_px:
                reasons.append(f"Spatial distance ({dist:.1f}px) within critical buffer ({self.dist_critical_px}px)")
            elif dist < self.dist_warning_px:
                reasons.append(f"Spatial distance ({dist:.1f}px) within warning buffer ({self.dist_warning_px}px)")
        # OmniJev System 1 Decision Probes
        if probes is not None:
            # Check collision probability
            if probes.collision_risk >= self.collision_prob_critical:
                alarm_level = AlarmLevel.CRITICAL
                reasons.append(
                    f"OmniJev P(collision) = {probes.collision_risk:.2f} >= {self.collision_prob_critical:.2f}"
                )
            elif probes.collision_risk >= self.collision_prob_warning:
                alarm_level = max(alarm_level, AlarmLevel.WARNING, key=lambda x: [AlarmLevel.NORMAL, AlarmLevel.WARNING, AlarmLevel.CRITICAL].index(x))
                reasons.append(
                    f"OmniJev P(collision) = {probes.collision_risk:.2f} >= {self.collision_prob_warning:.2f}"
                )

            # Check threat score
            if probes.threat_score >= self.threat_score_critical:
                alarm_level = AlarmLevel.CRITICAL
                reasons.append(f"Hazard threat score = {probes.threat_score:.2f} >= {self.threat_score_critical:.2f}")

            # Check worker attention
            unaware = probes.worker_awareness.get("unaware/distracted", 0.0)
            if unaware > 0.65 and alarm_level != AlarmLevel.NORMAL:
                reasons.append(f"High worker distraction probability: {unaware:.2f}")
        else:
            # Fallback to pure geometric distance if probes unavailable
            if dist is not None:
                if dist < self.dist_critical_px:
                    alarm_level = AlarmLevel.CRITICAL
                elif dist < self.dist_warning_px:
                    alarm_level = AlarmLevel.WARNING

        return FrameDecision(
            frame_id=frame_id,
            timestamp=timestamp,
            perception=perception,
            probes=probes,
            alarm_level=alarm_level,
            reasons=reasons,
            gating=gating,
        )
