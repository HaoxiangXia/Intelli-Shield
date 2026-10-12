"""Integration test for pipeline runner components with SpatialTemporalGate."""

import unittest
from pipeline.models import BoundingBox, PerceptionResult, AlarmLevel, OmniJevProbes
from pipeline.gating import SpatialTemporalGate
from pipeline.risk_fusion import RiskFusionEngine


class TestPipelineGatingIntegration(unittest.TestCase):

    def test_gating_and_fusion_flow(self):
        gate = SpatialTemporalGate(trigger_distance_px=250.0, static_frame_threshold=3)
        fusion = RiskFusionEngine()

        # Step 1: Forklift and ground worker close (< 250px), moving
        forklift = BoundingBox(x1=100, y1=100, x2=250, y2=250, confidence=0.9, class_name="forklift")
        ped = BoundingBox(x1=300, y1=150, x2=340, y2=230, confidence=0.88, class_name="person")

        p_close = PerceptionResult(frame_id=1, timestamp=0.1, forklifts=[forklift], pedestrians=[ped])
        gate_dec = gate.evaluate(p_close)
        self.assertTrue(gate_dec.should_trigger, "Gate must open when worker and vehicle are near")

        # Simulate OmniJev probe output
        probes = OmniJevProbes(
            collision_risk=0.82,
            worker_awareness={"unaware/distracted": 0.75},
            threat_score=2.5,
            latency_ms=105.0,
        )
        decision = fusion.arbitrate(1, 0.1, p_close, probes=probes, gating=gate_dec)
        self.assertEqual(decision.alarm_level, AlarmLevel.CRITICAL)

        # Step 2: Now test motionless cancellation over frames
        for f in range(2, 6):
            p_static = PerceptionResult(frame_id=f, timestamp=f * 0.1, forklifts=[forklift], pedestrians=[ped])
            gate_dec = gate.evaluate(p_static)

        self.assertFalse(gate_dec.should_trigger, "After multiple static frames, gate must SHUT")
        # Probe is skipped (None)
        decision = fusion.arbitrate(5, 0.5, p_static, probes=None, gating=gate_dec)
        self.assertEqual(decision.alarm_level, AlarmLevel.NORMAL)
        self.assertIn("Fast-Path NORMAL", decision.reasons[0])


if __name__ == "__main__":
    unittest.main()
