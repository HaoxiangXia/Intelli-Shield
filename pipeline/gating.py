"""Spatial-temporal gating engine for OmniJev cognitive inference.

Migrated and enhanced from advisor's C++ IsCarAway algorithm:
1. Driver exclusion: Filters out workers sitting inside forklift / truck cabin.
2. Motionless cancellation (静止对消): Filters out parked/stationary forklifts.
3. ROI Geofencing (电子围栏): Restricts hazard monitoring to designated work zones.
4. Dynamic Proximity Gating: Only triggers costly OmniJev probes when moving vehicles
   and ground workers are within interaction range.
"""

from __future__ import annotations
import math
from typing import List, Optional, Sequence, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from .models import BoundingBox, GatingDecision, PerceptionResult


class _TrackedVehicle:
    """Internal tracker state for stationary vehicle cancellation."""

    def __init__(self, box: BoundingBox, frame_id: int):
        self.box = box
        self.last_frame_id = frame_id
        self.static_count = 0

    @property
    def center(self) -> Tuple[float, float]:
        return (self.box.x1 + self.box.x2) / 2.0, (self.box.y1 + self.box.y2) / 2.0

    @property
    def width(self) -> float:
        return max(1.0, self.box.x2 - self.box.x1)

    @property
    def height(self) -> float:
        return max(1.0, self.box.y2 - self.box.y1)


class SpatialTemporalGate:
    """Pre-probe gating engine inspired by C++ IsCarAway.

    Evaluates whether a frame contains real dynamic risk before calling OmniJev.
    """

    def __init__(
        self,
        driver_overlap_ratio: float = 0.55,
        static_frame_threshold: int = 3,
        static_disp_ratio: float = 0.05,
        static_min_disp_px: float = 6.0,
        trigger_distance_px: float = 250.0,
        roi_polygon: Optional[Sequence[Tuple[float, float]]] = None,
        truck_head_boxes: bool = True,
    ):
        """Initialize the gating engine.

        Args:
            driver_overlap_ratio: Minimum overlap area ratio (inter / person_area)
                                  to classify a pedestrian as an onboard vehicle driver.
            static_frame_threshold: Consecutive stationary frames required to cancel a vehicle.
            static_disp_ratio: Displacement ratio relative to box dimensions (default 5%).
            static_min_disp_px: Absolute minimum pixel displacement to suppress jitter.
            trigger_distance_px: Maximum distance between active pedestrian and active vehicle
                                 to trigger OmniJev probe.
            roi_polygon: List of (x, y) vertices defining the active danger zone. None = full frame.
            truck_head_boxes: Whether to check truck head containment if available.
        """
        self.driver_overlap_ratio = driver_overlap_ratio
        self.static_frame_threshold = static_frame_threshold
        self.static_disp_ratio = static_disp_ratio
        self.static_min_disp_px = static_min_disp_px
        self.trigger_distance_px = trigger_distance_px
        self.roi_polygon = np.array(roi_polygon, dtype=np.int32) if roi_polygon is not None else None
        self.truck_head_boxes = truck_head_boxes

        self._tracked_vehicles: List[_TrackedVehicle] = []
        self._last_frame_id: int = -1

    def reset(self) -> None:
        """Reset internal temporal tracker state."""
        self._tracked_vehicles.clear()
        self._last_frame_id = -1

    def set_roi(self, polygon: Optional[Sequence[Tuple[float, float]]]) -> None:
        """Update active ROI polygon."""
        self.roi_polygon = np.array(polygon, dtype=np.int32) if polygon is not None else None

    def evaluate(self, perception: PerceptionResult) -> GatingDecision:
        """Evaluate perception detections and decide whether to open OmniJev gate."""
        frame_id = perception.frame_id

        # 1. Quick exit if either class is missing
        if not perception.pedestrians or not perception.forklifts:
            self._update_forklift_tracking(perception.forklifts, frame_id)
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=[],
                active_forklifts=[],
                driver_pedestrians=[],
                static_forklifts=[],
                min_dynamic_distance_px=None,
                reason="Pedestrian or forklift missing in frame",
            )

        # 2. Filter by ROI Geofence
        peds_in_roi = [p for p in perception.pedestrians if self._is_box_in_roi(p)]
        forks_in_roi = [f for f in perception.forklifts if self._is_box_in_roi(f)]

        if not peds_in_roi:
            self._update_forklift_tracking(perception.forklifts, frame_id)
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=[],
                active_forklifts=[],
                driver_pedestrians=[],
                static_forklifts=[],
                min_dynamic_distance_px=None,
                reason="All pedestrians outside designated ROI danger zone",
            )

        if not forks_in_roi:
            self._update_forklift_tracking(perception.forklifts, frame_id)
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=peds_in_roi,
                active_forklifts=[],
                driver_pedestrians=[],
                static_forklifts=[],
                min_dynamic_distance_px=None,
                reason="All forklifts outside designated ROI danger zone",
            )

        # 3. Driver Exclusion (check if person is sitting inside forklift/cabin)
        ground_pedestrians: List[BoundingBox] = []
        driver_pedestrians: List[BoundingBox] = []

        for ped in peds_in_roi:
            is_driver = False
            for fork in perception.forklifts:
                # Strict user directive: IoP only calculates against forkTruck, others do not participate
                if fork.class_name == "forkTruck" and self._is_driver_inside_vehicle(ped, fork):
                    is_driver = True
                    break
            if is_driver:
                driver_pedestrians.append(ped)
            else:
                ground_pedestrians.append(ped)

        if not ground_pedestrians:
            self._update_forklift_tracking(perception.forklifts, frame_id)
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=[],
                active_forklifts=[],
                driver_pedestrians=driver_pedestrians,
                static_forklifts=[],
                min_dynamic_distance_px=None,
                reason=f"All {len(driver_pedestrians)} pedestrian(s) identified as vehicle drivers (Driver Exclusion)",
            )

        # 4. Motionless Cancellation (静止对消)
        active_forklifts, static_forklifts = self._update_forklift_tracking(forks_in_roi, frame_id)

        if not active_forklifts:
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=ground_pedestrians,
                active_forklifts=[],
                driver_pedestrians=driver_pedestrians,
                static_forklifts=static_forklifts,
                min_dynamic_distance_px=None,
                reason=f"All {len(static_forklifts)} forklift(s) in ROI are stationary (Motionless Cancellation)",
            )

        # 5. Dynamic Spatial Proximity
        min_dynamic_dist = self._calc_min_distance(ground_pedestrians, active_forklifts)

        if min_dynamic_dist is not None and min_dynamic_dist <= self.trigger_distance_px:
            return GatingDecision(
                should_trigger=True,
                active_pedestrians=ground_pedestrians,
                active_forklifts=active_forklifts,
                driver_pedestrians=driver_pedestrians,
                static_forklifts=static_forklifts,
                min_dynamic_distance_px=min_dynamic_dist,
                reason=(
                    f"Dynamic risk detected: active pedestrian and moving forklift within "
                    f"{min_dynamic_dist:.1f}px (threshold: {self.trigger_distance_px:.1f}px)"
                ),
            )
        else:
            dist_desc = f"{min_dynamic_dist:.1f}px" if min_dynamic_dist is not None else "N/A"
            return GatingDecision(
                should_trigger=False,
                active_pedestrians=ground_pedestrians,
                active_forklifts=active_forklifts,
                driver_pedestrians=driver_pedestrians,
                static_forklifts=static_forklifts,
                min_dynamic_distance_px=min_dynamic_dist,
                reason=f"Ground worker and moving forklift separated beyond buffer ({dist_desc} > {self.trigger_distance_px:.1f}px)",
            )

    def _is_box_in_roi(self, box: BoundingBox) -> bool:
        """Check if bottom-center ground anchor of box is inside ROI polygon."""
        if self.roi_polygon is None or len(self.roi_polygon) < 3:
            return True

        foot_x = (box.x1 + box.x2) / 2.0
        foot_y = box.y2  # Bottom foot point

        if cv2 is not None:
            pt = (float(foot_x), float(foot_y))
            # pointPolygonTest returns >= 0 for inside or on boundary
            return cv2.pointPolygonTest(self.roi_polygon, pt, False) >= 0

        # Pure Python Ray-casting fallback
        return self._point_in_polygon(foot_x, foot_y, self.roi_polygon)

    @staticmethod
    def _point_in_polygon(x: float, y: float, poly: np.ndarray) -> bool:
        """Ray-casting algorithm for point-in-polygon testing."""
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(1, n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def _is_driver_inside_vehicle(self, ped: BoundingBox, vehicle: BoundingBox) -> bool:
        """Determine if a person box represents an on-board driver.

        Uses core enclosure and intersection-over-person (IoP) ratio.
        """
        # Person core box (20% margin as in advisor's C++ code)
        pw = ped.x2 - ped.x1
        ph = ped.y2 - ped.y1
        if pw <= 0 or ph <= 0:
            return False

        core_x1 = ped.x1 + 0.20 * pw
        core_y1 = ped.y1 + 0.20 * ph
        core_x2 = ped.x2 - 0.20 * pw
        core_y2 = ped.y2 - 0.20 * ph

        # Condition A: Person core box is fully enclosed inside vehicle box
        core_enclosed = (
            core_x1 >= vehicle.x1
            and core_y1 >= vehicle.y1
            and core_x2 <= vehicle.x2
            and core_y2 <= vehicle.y2
        )
        if core_enclosed:
            return True

        # Condition B: High overlap ratio of person inside vehicle
        ix1 = max(ped.x1, vehicle.x1)
        iy1 = max(ped.y1, vehicle.y1)
        ix2 = min(ped.x2, vehicle.x2)
        iy2 = min(ped.y2, vehicle.y2)

        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        inter_area = iw * ih
        ped_area = pw * ph

        iop = inter_area / ped_area
        if iop >= self.driver_overlap_ratio:
            return True

        # Condition C: Person center inside vehicle and overlap >= 40%
        pc_x = (ped.x1 + ped.x2) / 2.0
        pc_y = (ped.y1 + ped.y2) / 2.0
        center_inside = (
            vehicle.x1 <= pc_x <= vehicle.x2
            and vehicle.y1 <= pc_y <= vehicle.y2
        )
        if center_inside and iop >= 0.40:
            return True

        return False

    def _update_forklift_tracking(
        self, current_forklifts: List[BoundingBox], frame_id: int
    ) -> Tuple[List[BoundingBox], List[BoundingBox]]:
        """Track forklifts and classify into moving (active) and stationary (static)."""
        active_list: List[BoundingBox] = []
        static_list: List[BoundingBox] = []

        if not current_forklifts:
            return active_list, static_list

        new_tracked: List[_TrackedVehicle] = []

        for fork in current_forklifts:
            fc_x = (fork.x1 + fork.x2) / 2.0
            fc_y = (fork.y1 + fork.y2) / 2.0
            fw = max(1.0, fork.x2 - fork.x1)
            fh = max(1.0, fork.y2 - fork.y1)

            # Match with closest previous tracked vehicle
            best_match: Optional[_TrackedVehicle] = None
            min_dist = float("inf")

            for prev in self._tracked_vehicles:
                # Discard stale tracker
                if frame_id - prev.last_frame_id > 10:
                    continue
                d = math.hypot(fc_x - prev.center[0], fc_y - prev.center[1])
                # Center distance must be within half of box dimension
                if d < min_dist and d < max(prev.width, prev.height) * 0.8:
                    min_dist = d
                    best_match = prev

            disp_thresh = max(
                self.static_min_disp_px,
                self.static_disp_ratio * max(fw, fh),
            )

            tracker = _TrackedVehicle(fork, frame_id)
            if best_match is not None:
                if min_dist <= disp_thresh:
                    # Vehicle has remained stationary
                    tracker.static_count = best_match.static_count + 1
                else:
                    # Vehicle moved! Reset counter
                    tracker.static_count = 0
            else:
                # First time seeing this vehicle: conservative active state (static_count=0)
                tracker.static_count = 0

            new_tracked.append(tracker)

            if tracker.static_count >= self.static_frame_threshold:
                static_list.append(fork)
            else:
                active_list.append(fork)

        self._tracked_vehicles = new_tracked
        self._last_frame_id = frame_id
        return active_list, static_list

    @staticmethod
    def _calc_min_distance(
        peds: List[BoundingBox], forks: List[BoundingBox]
    ) -> Optional[float]:
        """Compute Euclidean distance between closest pedestrian and forklift centers."""
        if not peds or not forks:
            return None

        min_d = float("inf")
        for p in peds:
            pc_x = (p.x1 + p.x2) / 2.0
            pc_y = (p.y1 + p.y2) / 2.0
            for f in forks:
                fc_x = (f.x1 + f.x2) / 2.0
                fc_y = (f.y1 + f.y2) / 2.0
                dist = math.hypot(pc_x - fc_x, pc_y - fc_y)
                if dist < min_d:
                    min_d = dist

        return min_d if min_d != float("inf") else None
