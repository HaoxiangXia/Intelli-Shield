"""Red-Zone safety perimeter perception engine for industrial forklifts.

Detects projected 3-direction red laser lines on the warehouse floor,
assigns laser segments to their parent forklift via Voronoi ground-base clustering
(preventing multi-forklift polygon merging and excluding red vehicle bodywork),
and evaluates ground pedestrian foot anchor breach status:
  - ZONE_INSIDE (< 0m): Stepped inside red perimeter -> CRITICAL
  - ZONE_BUFFER (0 ~ 0.3m): Foot within outer proximity buffer -> WARNING
  - ZONE_SAFE (> 0.3m): Outside exclusion zone -> NORMAL (OmniJev arbitrated)
"""

from __future__ import annotations
from typing import List, Sequence, Tuple
import cv2
import numpy as np

from .models import BoundingBox, RedZoneEvaluation, RedZoneState


class RedZoneEngine:
    """Perceives industrial forklift floor laser projections and monitors spatial safety zones."""

    def __init__(
        self,
        buffer_meters: float = 0.28,
        reference_human_height_m: float = 1.75,
        min_laser_component_area: int = 60,
    ):
        self.buffer_meters = buffer_meters
        self.reference_human_height_m = reference_human_height_m
        self.min_laser_component_area = min_laser_component_area

    @staticmethod
    def is_driver_in_forklift(ped: BoundingBox, forklifts: Sequence[BoundingBox]) -> bool:
        """Filter out operators seated inside a forklift cabin so only ground workers are tested."""
        pw = max(1.0, ped.x2 - ped.x1)
        ph = max(1.0, ped.y2 - ped.y1)
        p_area = pw * ph
        pc_x = (ped.x1 + ped.x2) / 2.0
        pc_y = (ped.y1 + ped.y2) / 2.0

        for fork in forklifts:
            fw = max(1.0, fork.x2 - fork.x1)
            fh = max(1.0, fork.y2 - fork.y1)

            ix1 = max(ped.x1, fork.x1)
            iy1 = max(ped.y1, fork.y1)
            ix2 = min(ped.x2, fork.x2)
            iy2 = min(ped.y2, fork.y2)
            inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
            iop = inter / p_area

            # Driver sits inside cabin: high overlap and feet are above ground tire bottom
            if iop >= 0.55 and ped.y2 <= fork.y2 - fh * 0.08:
                return True
            if (
                fork.x1 + fw * 0.08 <= pc_x <= fork.x2 - fw * 0.08
                and fork.y1 + fh * 0.08 <= pc_y <= fork.y2 - fh * 0.22
                and ped.y2 <= fork.y2 - fh * 0.08
            ):
                return True
        return False

    def evaluate(
        self,
        frame_bgr: np.ndarray,
        forklifts: Sequence[BoundingBox],
        pedestrians: Sequence[BoundingBox],
    ) -> RedZoneEvaluation:
        """Evaluate all forklifts and ground pedestrians against red-zone safety boundaries."""
        if not forklifts:
            return RedZoneEvaluation(
                state=RedZoneState.SAFE,
                min_dist_px=float("inf"),
                min_dist_m=float("inf"),
                has_detected_lasers=False,
            )

        polygons, any_laser_detected = self._build_voronoi_forklift_polygons(frame_bgr, forklifts)

        # Filter out seated forklift drivers; only evaluate ground pedestrians
        ground_peds = [p for p in pedestrians if not self.is_driver_in_forklift(p, forklifts)]

        if not ground_peds:
            return RedZoneEvaluation(
                state=RedZoneState.SAFE,
                min_dist_px=float("inf"),
                min_dist_m=float("inf"),
                polygons=[p.reshape(-1, 2).tolist() for p in polygons],
                has_detected_lasers=any_laser_detected,
            )

        overall_state = RedZoneState.SAFE
        min_signed_dist_px = float("inf")
        min_signed_dist_m = float("inf")
        violating_peds: List[BoundingBox] = []
        used_buffer_thresh_px = 22.0

        for ped in ground_peds:
            foot_x = (ped.x1 + ped.x2) / 2.0
            foot_y = ped.y2
            ped_h = max(20.0, ped.y2 - ped.y1)
            px_per_meter = ped_h / self.reference_human_height_m
            buffer_thresh_px = max(15.0, min(35.0, self.buffer_meters * px_per_meter))
            used_buffer_thresh_px = buffer_thresh_px

            ped_min_dist = float("inf")
            for poly in polygons:
                # cv2.pointPolygonTest: >0 inside, <0 outside, 0 on boundary
                raw_test = cv2.pointPolygonTest(poly, (float(foot_x), float(foot_y)), True)
                signed_dist = -raw_test  # Negative inside, positive outside
                if signed_dist < ped_min_dist:
                    ped_min_dist = signed_dist

            if ped_min_dist < 0:
                ped_state = RedZoneState.INSIDE
            elif ped_min_dist <= buffer_thresh_px:
                ped_state = RedZoneState.BUFFER
            else:
                ped_state = RedZoneState.SAFE

            ped_dist_m = ped_min_dist / max(px_per_meter, 1e-3)

            if ped_min_dist < min_signed_dist_px:
                min_signed_dist_px = ped_min_dist
                min_signed_dist_m = ped_dist_m

            if ped_state in {RedZoneState.INSIDE, RedZoneState.BUFFER}:
                violating_peds.append(ped)
                if ped_state == RedZoneState.INSIDE:
                    overall_state = RedZoneState.INSIDE
                elif overall_state != RedZoneState.INSIDE:
                    overall_state = RedZoneState.BUFFER

        return RedZoneEvaluation(
            state=overall_state,
            min_dist_px=min_signed_dist_px,
            min_dist_m=min_signed_dist_m,
            buffer_thresh_px=used_buffer_thresh_px,
            violating_pedestrians=violating_peds,
            polygons=[p.reshape(-1, 2).tolist() for p in polygons],
            has_detected_lasers=any_laser_detected,
        )

    def _build_voronoi_forklift_polygons(
        self,
        frame_bgr: np.ndarray,
        forklifts: Sequence[BoundingBox],
    ) -> Tuple[List[np.ndarray], bool]:
        """Extract floor red laser components and assign each to its nearest forklift base."""
        h, w = frame_bgr.shape[:2]
        b, g, r = cv2.split(frame_bgr)

        # High-intensity red laser line mask on warehouse floor
        laser_mask = (
            (r > 165)
            & ((r.astype(int) - g.astype(int)) > 35)
            & ((r.astype(int) - b.astype(int)) > 65)
        ).astype(np.uint8) * 255

        # Mask out the upper 78% of each forklift bounding box so red-painted vehicle
        # bodywork and tail lamps are not mistaken for floor laser lines
        for fork in forklifts:
            fx1, fy1, fx2, fy2 = int(fork.x1), int(fork.y1), int(fork.x2), int(fork.y2)
            fw = max(10, fx2 - fx1)
            fh = max(10, fy2 - fy1)
            body_y2 = max(0, min(h, int(fy1 + fh * 0.78)))
            bx1_in = max(0, int(fx1 + fw * 0.05))
            bx2_in = min(w, int(fx2 - fw * 0.05))
            laser_mask[max(0, fy1):body_y2, bx1_in:bx2_in] = 0

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(laser_mask)
        fork_laser_pts: List[List[np.ndarray]] = [[] for _ in forklifts]

        for lbl_idx in range(1, num_labels):
            area = stats[lbl_idx, cv2.CC_STAT_AREA]
            if area < self.min_laser_component_area:
                continue
            cx, cy = centroids[lbl_idx]
            # Ignore far-right wall/gate reflections or upper ceiling regions
            if cx > w * 0.82 or cy < h * 0.25:
                continue

            best_f = -1
            best_dist = float("inf")
            for f_idx, fork in enumerate(forklifts):
                fw = max(10.0, fork.x2 - fork.x1)
                fh = max(10.0, fork.y2 - fork.y1)
                gx1, gx2 = fork.x1, fork.x2
                gy1, gy2 = fork.y1 + 0.65 * fh, fork.y2
                dx = max(gx1 - cx, 0.0, cx - gx2)
                dy = max(gy1 - cy, 0.0, cy - gy2)
                dist = float(np.hypot(dx, dy))
                max_reach = max(fw, fh) * 1.15
                if dist <= max_reach and dist < best_dist:
                    best_dist = dist
                    best_f = f_idx

            if best_f >= 0:
                x0 = stats[lbl_idx, cv2.CC_STAT_LEFT]
                y0 = stats[lbl_idx, cv2.CC_STAT_TOP]
                w0 = stats[lbl_idx, cv2.CC_STAT_WIDTH]
                h0 = stats[lbl_idx, cv2.CC_STAT_HEIGHT]
                sub_mask = (labels[y0 : y0 + h0, x0 : x0 + w0] == lbl_idx).astype(np.uint8)
                contours, _ = cv2.findContours(sub_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    pts = cnt.reshape(-1, 2) + np.array([x0, y0], dtype=np.int32)
                    fork_laser_pts[best_f].append(pts)

        polygons: List[np.ndarray] = []
        any_laser = False

        for f_idx, fork in enumerate(forklifts):
            fx1, fy1, fx2, fy2 = fork.x1, fork.y1, fork.x2, fork.y2
            fw = max(10.0, fx2 - fx1)
            fh = max(10.0, fy2 - fy1)

            # Ground contact footprint of the forklift chassis (bottom 30%)
            base_pts = np.array(
                [
                    [fx1 + fw * 0.10, fy2 - fh * 0.05],
                    [fx2 - fw * 0.10, fy2 - fh * 0.05],
                    [fx1 + fw * 0.10, fy2 - fh * 0.30],
                    [fx2 - fw * 0.10, fy2 - fh * 0.30],
                ],
                dtype=np.float32,
            )

            if fork_laser_pts[f_idx]:
                any_laser = True
                l_pts = np.vstack(fork_laser_pts[f_idx]).astype(np.float32)
                all_pts = np.vstack([base_pts, l_pts]).astype(np.int32)
                hull = cv2.convexHull(all_pts)
                polygons.append(hull)
            else:
                pad_x = fw * 0.35
                pad_y = fh * 0.25
                synth = np.array(
                    [
                        [fx1 - pad_x, fy2 - fh * 0.35],
                        [fx2 + pad_x, fy2 - fh * 0.35],
                        [fx2 + pad_x, min(h - 1, fy2 + pad_y)],
                        [fx1 - pad_x, min(h - 1, fy2 + pad_y)],
                    ],
                    dtype=np.int32,
                ).reshape(-1, 1, 2)
                polygons.append(synth)

        return polygons, any_laser
