# 0008. Red-Zone Optical Perimeter Perception and Layered Risk Arbitration

## Context & Problem
In real factory CCTV footage (`samples/cctv/videos/output_video7.mp4`, `220121shenyang1509.png`, `4504.png`), forklifts are equipped with three-directional (left, right, rear) industrial red line laser projectors (Red-Zone Danger Area Perimeter Lights). According to warehouse safety compliance rules, any pedestrian stepping inside the projected red lines on the floor constitutes an immediate safety violation and run-over hazard.

Prior to this revision, the pipeline suffered from three critical disconnects:
1. **Unperceived Optical Boundary**: The perception layer only calculated Euclidean distance between bounding-box centers (`math.hypot(pc_x - fc_x, pc_y - fc_y)`), completely ignoring the physical red laser lines projected on the floor.
2. **Perspective Distortion on Body Centers**: Under elevated CCTV camera angles, using the bounding-box center `(x_mid, y_mid)` misrepresents where the worker is actually standing on the ground.
3. **Motionless Gating Blind Spot**: If a forklift paused briefly during loading/unloading, `SpatialTemporalGate` triggered motionless cancellation (`Fast-Path NORMAL`), suppressing alarms even when a worker was standing directly inside the red danger zone.

## Decisions

1. **Optical Red-Zone Extraction & Convex Hull Enclosure (`pipeline/red_zone.py`)**:
   - Extract high-intensity red laser projections ($R > 150, R - G > 40, R - B > 50$) within the floor region surrounding each detected `forkTruck`.
   - Combine the forklift's ground contact base with the three projected laser segments via `cv2.convexHull` to form the dynamic ground exclusion polygon (`RedZonePolygon`).
   - Provide a geometric fallback envelope ($\approx 1.5\text{ m}$ margin) when ambient lighting obscures laser lines.

2. **Foot Ground-Anchor Topology**:
   - Evaluate spatial intrusion using the pedestrian's bottom-center foot contact point $(x_{\text{foot}}, y_{\text{foot}}) = (\frac{x_1 + x_2}{2}, y_2)$ via `cv2.pointPolygonTest`.
   - Convert pixel distances to metric estimates using perspective-adaptive scaling anchored to pedestrian bounding-box height ($H_{\text{ped}} \leftrightarrow 1.75\text{ m}$, $\approx 85\sim 90\text{ px/m}$ at 1080p).

3. **Three-Tier Spatial Boundary Specification**:
   - **`ZONE_INSIDE` ($< 0\text{ m}$, inside red line)**: Pedestrian feet have crossed inside the red laser perimeter. Triggers an immediate, non-overridable **`CRITICAL`** alarm.
   - **`ZONE_BUFFER` ($0 \sim 0.30\text{ m}$ outside red line, $\approx 18\sim 26\text{ px}$)**: Pedestrian feet are within the outer proximity buffer band ($\text{buffer\_px} = H_{\text{ped}} \times \frac{0.28}{1.75}$). Triggers **`WARNING`**.
   - **`ZONE_SAFE` ($> 0.30\text{ m}$ outside red line)**: Physical boundary is clear; risk arbitration is delegated to OmniJev System 1 predictive probes.

4. **Layered Dual-System Risk Arbitration (`pipeline/risk_fusion.py`)**:
   - **Layer 1: Physical Hard Constraint (Floor Baseline)**: `ZONE_INSIDE` exercises one-vote veto power to enforce `CRITICAL`, bypassing motionless vehicle cancellation in `SpatialTemporalGate`.
   - **Layer 2: Cognitive Probe Attribution (OmniJev System 1)**: When a breach occurs, OmniJev probes (`worker_awareness`, `collision_risk`, `threat_score`) provide semantic context (e.g., distinguishing an unaware worker with their back turned from an attentive worker, or escalating `ZONE_BUFFER` to `CRITICAL` when $P(\text{collision}) \ge 0.70$).

5. **Division of Labor: YOLO (Retina) vs RedZone (Floor Boundary) vs OmniJev (System 1 Brain)**:
   - **YOLO (Retina / What & Where)**: Detects persons and vehicles; computes pedestrian bottom-center ground contact $(x_{\text{foot}}, y_{\text{foot}})$; masks out the upper $78\%$ of each forklift to prevent vehicle red paint from interfering with floor lasers; provides Voronoi ground clustering centers; and excludes seated drivers via IoP to prevent false-alarm deadlocks.
   - **RedZoneEngine (Floor Boundary / Hard Constraint Floor)**: Extracts floor laser strips, fits the safety exclusion polygon, evaluates signed point-in-polygon distances, and enforces one-vote veto `CRITICAL` upon physical breach.
   - **OmniJev (System 1 Brain / Context & Intention)**: Evaluates worker awareness distribution (unaware vs yielding), hazard threat severity, and collision probability in single-pass 107ms inference, providing actionable semantic context for safety directors and enabling predictive warnings outside the red line.

## Empirical Verification
Tested against `samples/cctv/videos/output_video7.mp4` across multiple timestamps:
- At $t = 4\text{s}, 10\text{s}, 16\text{s}, 22\text{s}$, the worker in the yellow reflective vest standing across the right red laser beam is accurately localized at foot anchor $(841, 520)$ with intrusion depths of $-0.88\text{ m}$ to $-1.46\text{ m}$ (`ZONE_INSIDE`), deterministically outputting `CRITICAL` and eliminating the prior false-normal defect.
