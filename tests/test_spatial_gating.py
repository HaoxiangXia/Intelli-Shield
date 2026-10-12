"""Verification tests for spatial-temporal gating module."""

import sys
import unittest
from pipeline.models import BoundingBox, PerceptionResult, AlarmLevel
from pipeline.gating import SpatialTemporalGate
from pipeline.risk_fusion import RiskFusionEngine


class TestSpatialTemporalGate(unittest.TestCase):

    def setUp(self):
        self.gate = SpatialTemporalGate(
            driver_overlap_ratio=0.55,
            static_frame_threshold=3,
            static_disp_ratio=0.05,
            static_min_disp_px=6.0,
            trigger_distance_px=200.0,
        )
        self.fusion = RiskFusionEngine()

    def test_driver_exclusion(self):
        """A person inside the forklift cabin must be recognized as driver and not trigger OmniJev."""
        # Forklift at (100, 100) -> (300, 300)
        forklift = BoundingBox(x1=100, y1=100, x2=300, y2=300, confidence=0.9, class_name="forklift")
        # Person sitting inside forklift cabin (150, 120) -> (220, 260)
        driver = BoundingBox(x1=150, y1=120, x2=220, y2=260, confidence=0.85, class_name="person")

        perception = PerceptionResult(
            frame_id=1,
            timestamp=0.1,
            forklifts=[forklift],
            pedestrians=[driver],
            min_distance_px=15.0,  # Center distance is very close!
        )

        decision = self.gate.evaluate(perception)
        self.assertFalse(decision.should_trigger, "Gate should NOT trigger for on-board driver!")
        self.assertEqual(len(decision.driver_pedestrians), 1)
        self.assertEqual(len(decision.active_pedestrians), 0)
        self.assertIn("Driver Exclusion", decision.reason)

        # Risk fusion should output NORMAL
        frame_decision = self.fusion.arbitrate(1, 0.1, perception, probes=None, gating=decision)
        self.assertEqual(frame_decision.alarm_level, AlarmLevel.NORMAL)

    def test_motionless_cancellation(self):
        """Stationary forklift must be cancelled after static_frame_threshold frames."""
        # Forklift stays at (200, 200) -> (400, 400)
        forklift = BoundingBox(x1=200, y1=200, x2=400, y2=400, confidence=0.9, class_name="forklift")
        # Ground worker nearby at (450, 250) -> (500, 350)
        ground_worker = BoundingBox(x1=450, y1=250, x2=500, y2=350, confidence=0.85, class_name="person")

        # Frame 1: Initial detection (conservative open)
        p1 = PerceptionResult(frame_id=1, timestamp=0.1, forklifts=[forklift], pedestrians=[ground_worker])
        d1 = self.gate.evaluate(p1)
        self.assertTrue(d1.should_trigger, "Frame 1 should trigger before stationarity is confirmed")

        # Frame 2: Still in same position
        p2 = PerceptionResult(frame_id=2, timestamp=0.2, forklifts=[forklift], pedestrians=[ground_worker])
        d2 = self.gate.evaluate(p2)

        # Frame 3: Still in same position (static_count reached 2)
        p3 = PerceptionResult(frame_id=3, timestamp=0.3, forklifts=[forklift], pedestrians=[ground_worker])
        d3 = self.gate.evaluate(p3)

        # Frame 4: static_count reaches 3 >= threshold -> Motionless cancellation kicks in!
        p4 = PerceptionResult(frame_id=4, timestamp=0.4, forklifts=[forklift], pedestrians=[ground_worker])
        d4 = self.gate.evaluate(p4)
        self.assertFalse(d4.should_trigger, "Stationary forklift must be cancelled!")
        self.assertIn("Motionless Cancellation", d4.reason)
        self.assertEqual(len(d4.static_forklifts), 1)

        # Now forklift starts moving: displacement > threshold
        moving_forklift = BoundingBox(x1=230, y1=200, x2=430, y2=400, confidence=0.9, class_name="forklift")
        p5 = PerceptionResult(frame_id=5, timestamp=0.5, forklifts=[moving_forklift], pedestrians=[ground_worker])
        d5 = self.gate.evaluate(p5)
        self.assertTrue(d5.should_trigger, "When forklift resumes motion, gate must immediately OPEN!")

    def test_roi_geofencing(self):
        """Entities outside ROI polygon must be ignored."""
        # Danger zone polygon: x in [0, 500], y in [0, 500]
        gate_roi = SpatialTemporalGate(
            roi_polygon=[(0, 0), (500, 0), (500, 500), (0, 500)],
            trigger_distance_px=300.0,
        )

        # Forklift inside ROI
        forklift = BoundingBox(x1=100, y1=100, x2=200, y2=200, confidence=0.9, class_name="forklift")
        # Person way outside ROI at bottom (x=700, y=800)
        person_outside = BoundingBox(x1=700, y1=700, x2=750, y2=850, confidence=0.9, class_name="person")

        perception = PerceptionResult(
            frame_id=1,
            timestamp=0.1,
            forklifts=[forklift],
            pedestrians=[person_outside],
        )

        decision = gate_roi.evaluate(perception)
        self.assertFalse(decision.should_trigger, "Worker outside ROI must not trigger OmniJev!")
        self.assertIn("outside designated ROI", decision.reason)


if __name__ == "__main__":
    unittest.main()
