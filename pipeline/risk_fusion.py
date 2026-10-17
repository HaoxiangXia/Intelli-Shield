"""Risk fusion engine combining physical red-zone safety boundaries with OmniJev decision probes."""

from __future__ import annotations
from typing import List, Optional

from .models import (
    AlarmLevel,
    FrameDecision,
    GatingDecision,
    OmniJevProbes,
    PerceptionResult,
    RedZoneEvaluation,
    RedZoneState,
)


class RiskFusionEngine:
    """Arbitrates alarm level using dual-system inputs.

    System Hierarchy:
    1. Physical Boundary Layer (Floor): Red laser perimeter intrusion is a hard constraint.
       - Pedestrian feet inside red line (< 0m) -> CRITICAL (One-vote veto)
       - Pedestrian feet within proximity buffer (0 ~ 0.3m) -> WARNING
    2. Cognitive Probe Layer (Context): OmniJev System 1 probes provide semantic attribution:
       - Worker attention (unaware vs yielding)
       - Threat severity score & collision probability
    3. Predictive Trigger: High collision probability (>=0.7) can trigger proactive CRITICAL
       even if worker has not yet crossed the red line.
    """

    def __init__(
        self,
        collision_prob_critical: float = 0.70,
        collision_prob_warning: float = 0.40,
        dist_critical_px: float = 120.0,
        dist_warning_px: float = 250.0,
        threat_score_critical: float = 2.2,
        hysteresis_trigger_frames: int = 1,
        hysteresis_release_frames: int = 4,
    ):
        self.collision_prob_critical = collision_prob_critical
        self.collision_prob_warning = collision_prob_warning
        self.dist_critical_px = dist_critical_px
        self.dist_warning_px = dist_warning_px
        self.threat_score_critical = threat_score_critical
        self.hysteresis_trigger_frames = hysteresis_trigger_frames
        self.hysteresis_release_frames = hysteresis_release_frames

        # Temporal state tracking
        self._consecutive_critical = 0
        self._consecutive_warning = 0
        self._consecutive_safe = 0
        self._last_alarm_level = AlarmLevel.NORMAL

    def reset(self) -> None:
        """Reset temporal hysteresis state."""
        self._consecutive_critical = 0
        self._consecutive_warning = 0
        self._consecutive_safe = 0
        self._last_alarm_level = AlarmLevel.NORMAL

    def arbitrate(
        self,
        frame_id: int,
        timestamp: float,
        perception: PerceptionResult,
        probes: Optional[OmniJevProbes],
        gating: Optional[GatingDecision] = None,
    ) -> FrameDecision:
        reasons: List[str] = []
        candidate_level = AlarmLevel.NORMAL

        # Rule 0: No interaction if pedestrians or forklifts absent
        if not perception.pedestrians or not perception.forklifts:
            self._last_alarm_level = AlarmLevel.NORMAL
            return FrameDecision(
                frame_id=frame_id,
                timestamp=timestamp,
                perception=perception,
                probes=probes,
                alarm_level=AlarmLevel.NORMAL,
                reasons=["No pedestrian or forklift present in scene"],
                gating=gating,
                red_zone=perception.red_zone,
            )

        red_zone: Optional[RedZoneEvaluation] = (
            perception.red_zone if perception.red_zone is not None else (gating.red_zone if gating else None)
        )

        # ---------------------------------------------------------
        # Layer 1: Physical Red-Zone Hard Constraint (Floor Baseline)
        # ---------------------------------------------------------
        is_physically_breached = False
        if red_zone is not None:
            if red_zone.state == RedZoneState.INSIDE:
                candidate_level = AlarmLevel.CRITICAL
                is_physically_breached = True
                reasons.append(
                    f"【红光禁区侵入】人员双脚踏入叉车红光安全隔离线内侧 "
                    f"(侵入深度: {-red_zone.min_dist_px:.1f}px / {-red_zone.min_dist_m:.2f}m)"
                )
            elif red_zone.state == RedZoneState.BUFFER:
                candidate_level = AlarmLevel.WARNING
                is_physically_breached = True
                reasons.append(
                    f"【红光外沿缓冲预警】人员双脚处于红光外沿临界区 "
                    f"(间距: {red_zone.min_dist_px:.1f}px / {red_zone.min_dist_m:.2f}m <= 0.30m)"
                )

        # ---------------------------------------------------------
        # Layer 2: Pre-Perception Driver Sanitization Check
        # ---------------------------------------------------------
        # Driver-in-cab pedestrians are sanitized in gating/perception;
        # OmniJev inference proceeds per-frame without compute-saving bypasses.
        if gating is not None and gating.driver_pedestrians:
            reasons.append(f"Sanitized {len(gating.driver_pedestrians)} driver(s) inside forklift cabs")
        # ---------------------------------------------------------
        # Layer 3: Cognitive Probe Fusion & Context Attribution
        # ---------------------------------------------------------
        if probes is not None:
            # Probe A: Calibrated Collision Risk
            if probes.collision_risk >= self.collision_prob_critical:
                candidate_level = AlarmLevel.CRITICAL
                reasons.append(
                    f"OmniJev P(collision) = {probes.collision_risk:.2f} >= {self.collision_prob_critical:.2f} (高危轨迹)"
                )
            elif probes.collision_risk >= self.collision_prob_warning:
                if candidate_level == AlarmLevel.NORMAL:
                    candidate_level = AlarmLevel.WARNING
                reasons.append(
                    f"OmniJev P(collision) = {probes.collision_risk:.2f} >= {self.collision_prob_warning:.2f}"
                )

            # Probe B: Hazard Threat Score
            if probes.threat_score >= self.threat_score_critical:
                candidate_level = AlarmLevel.CRITICAL
                reasons.append(
                    f"Hazard threat score = {probes.threat_score:.2f} >= {self.threat_score_critical:.2f}"
                )

            # Probe C: Worker Attention & Hazardous Behavior Attribution
            unaware = probes.worker_awareness.get(
                "unaware", probes.worker_awareness.get("unaware/distracted", 0.0)
            )
            yielding = probes.worker_awareness.get("yielding", 0.0)

            if unaware >= 0.50:
                if candidate_level != AlarmLevel.NORMAL:
                    reasons.append(f"【盲区背对/分心】工人注意力缺失 P(unaware) = {unaware:.2f}")
            elif yielding >= 0.50:
                reasons.append(f"【工人注视避让】工人面向叉车注意观察 P(yielding) = {yielding:.2f}")

            # Probe D: Worker Hazardous Behavior Quantization (PRD 3.2)
            if probes.worker_hazard_behavior:
                phone = probes.worker_hazard_behavior.get("phone_distracted", 0.0)
                back = probes.worker_hazard_behavior.get("back_facing_vehicle", 0.0)
                blindspot = probes.worker_hazard_behavior.get("standing_in_blindspot", 0.0)
                if phone >= 0.50:
                    reasons.append(f"【严重违章】工人低头看手机 P(phone) = {phone:.2f}")
                elif back >= 0.50:
                    reasons.append(f"【视线盲区】工人背对驶来叉车 P(back) = {back:.2f}")
                elif blindspot >= 0.50:
                    reasons.append(f"【盲区停留】工人处于通道视线盲区 P(blindspot) = {blindspot:.2f}")
            # Fallback to spatial geometric distance when probes unavailable
            dist = (
                gating.min_dynamic_distance_px
                if (gating and gating.min_dynamic_distance_px is not None)
                else perception.min_distance_px
            )
            if dist is not None and not is_physically_breached:
                if dist < self.dist_critical_px:
                    candidate_level = AlarmLevel.CRITICAL
                    reasons.append(f"几何距离 ({dist:.1f}px) < 紧急阈值 ({self.dist_critical_px:.1f}px)")
                elif dist < self.dist_warning_px:
                    if candidate_level == AlarmLevel.NORMAL:
                        candidate_level = AlarmLevel.WARNING
                    reasons.append(f"几何距离 ({dist:.1f}px) < 预警阈值 ({self.dist_warning_px:.1f}px)")

        # ---------------------------------------------------------
        # Layer 4: Temporal Hysteresis Smoothing
        # ---------------------------------------------------------
        final_level = self._apply_hysteresis(candidate_level, frame_id)

        # ---------------------------------------------------------
        # Layer 5: Fleet Power Interlock Activation (PRD 3.3 / 4.4)
        # ---------------------------------------------------------
        interlock_engaged = False
        interlocked_forklifts: List[BoundingBox] = []
        if final_level == AlarmLevel.CRITICAL:
            interlock_engaged = True
            interlocked_forklifts = list(perception.forklifts)
            reasons.append(
                f"🛑 【全车动力切断】已向画面内全部在编叉车 ({len(interlocked_forklifts)}台) 触发动力切断与制动联锁"
            )

        return FrameDecision(
            frame_id=frame_id,
            timestamp=timestamp,
            perception=perception,
            probes=probes,
            alarm_level=final_level,
            reasons=reasons,
            gating=gating,
            red_zone=red_zone,
            interlock_engaged=interlock_engaged,
            interlocked_forklifts=interlocked_forklifts,
        )
    def _apply_hysteresis(self, candidate: AlarmLevel, frame_id: int) -> AlarmLevel:
        """Smooths alarm transitions to eliminate single-frame visual jitter."""
        if frame_id == 0 or self._last_alarm_level is None:
            self._last_alarm_level = candidate
            return candidate

        if candidate == AlarmLevel.CRITICAL:
            self._consecutive_critical += 1
            self._consecutive_warning = 0
            self._consecutive_safe = 0
            if self._consecutive_critical >= self.hysteresis_trigger_frames:
                self._last_alarm_level = AlarmLevel.CRITICAL
                return AlarmLevel.CRITICAL
            return self._last_alarm_level

        if candidate == AlarmLevel.WARNING:
            self._consecutive_warning += 1
            self._consecutive_critical = 0
            self._consecutive_safe = 0
            if self._last_alarm_level == AlarmLevel.CRITICAL:
                # Stepping down from CRITICAL requires release frames
                if self._consecutive_warning >= self.hysteresis_release_frames:
                    self._last_alarm_level = AlarmLevel.WARNING
                    return AlarmLevel.WARNING
                return AlarmLevel.CRITICAL
            else:
                self._last_alarm_level = AlarmLevel.WARNING
                return AlarmLevel.WARNING

        # Candidate is NORMAL
        self._consecutive_safe += 1
        self._consecutive_critical = 0
        self._consecutive_warning = 0
        if self._last_alarm_level != AlarmLevel.NORMAL:
            if self._consecutive_safe >= self.hysteresis_release_frames:
                self._last_alarm_level = AlarmLevel.NORMAL
                return AlarmLevel.NORMAL
            return self._last_alarm_level

        self._last_alarm_level = AlarmLevel.NORMAL
        return AlarmLevel.NORMAL
