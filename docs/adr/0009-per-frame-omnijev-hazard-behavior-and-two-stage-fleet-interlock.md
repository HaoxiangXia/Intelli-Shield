# 0009. Per-Frame OmniJev Cognitive Inference, Hazardous Worker Behavior Probe, and Two-Stage Fleet Interlock

## Context & Problem
In earlier iterations (ADR 0007), the pipeline employed `SpatialTemporalGate` to bypass remote OmniJev inference for motionless vehicles or distant pedestrians, aiming to conserve GPU compute. However, this intermittent invocation strategy introduced notable gaps in continuous behavioral surveillance:
1. **Surveillance Gaps**: Sporadic gating prevented continuous tracking of high-risk human behaviors (e.g., workers walking through operational zones while looking down at mobile phones or with their backs turned to approaching vehicles).
2. **Passive Interventions**: The legacy PRD strictly designated emergency braking (AEB) as out-of-scope, limiting system actions to passive siren alerts without active traction interruption.
3. **Audit Vulnerability**: Human audit workflows relied on single-click dismissals, introducing risks of premature vehicle power restoration before on-site hazard clearance was confirmed.

## Decisions

1. **Abolition of Compute Gating & Full-Frame 10 FPS Ingestion**:
   - Decommission all compute-saving bypasses (`Fast-Path NORMAL`) in `SpatialTemporalGate`.
   - Lock intake frame rate to **10.0 FPS** (100ms per frame), achieving high temporal synchronization with OmniJev-4B single-forward-pass latency (~107.4 ms on NVIDIA RTX 3090).
   - Retain Intersection-over-Person (IoP $\ge 0.65$) pre-perception filtering solely to exclude seated forklift drivers from obstacle tracking.

2. **Dedicated Hazardous Worker Behavior Probe (`worker_hazard_behavior`)**:
   - Expand OmniJev to evaluate 4 synchronized probes within a single forward pass (107ms, 0 generative tokens):
     - Probe 1: `collision_risk` (`Noul`: $[0.0, 1.0]$)
     - Probe 2: `worker_awareness` (`Choice`: `unaware`, `yielding`, `separated`)
     - Probe 3: `worker_hazard_behavior` (`Choice`: `phone_distracted`, `back_facing_vehicle`, `standing_in_blindspot`, `normal_compliant`)
     - Probe 4: `threat_score` (`Score`: $[0.0, 3.0]$ expected value over 4 ordinal bins)
   - Hazardous behavior provides direct causal attribution for incidents, populating audit dashboards and training corpora.

3. **Four-Tier Threat Severity Standard & UI Color Encoding**:
   - Formalize discrete hazard severity mapping across backend arbitration and frontend visualization:
     - **Level 0 ($0.00 \sim 0.49$)**: Safe Clearance — Emerald Green (`#10B981`)
     - **Level 1 ($0.50 \sim 1.49$)**: Cautionary Proximity — Sky Blue (`#38BDF8`)
     - **Level 2 ($1.50 \sim 2.19$)**: Warning Alert — Amber Yellow (`#F59E0B`)
     - **Level 3 ($2.20 \sim 3.00$)**: Critical Danger — Emergency Red (`#EF4444`)

4. **Vision-Guided Fleet Power Interlock (`Fleet Power Interlock`)**:
   - Reclassify active power cutoff from Non-Goal to Core Requirement.
   - Upon `CRITICAL` decision ($P_{\text{coll}} \ge 0.70$ or Red-Zone intrusion $<0\text{m}$), the system triggers on-site audible/visual alarms and broadcasts MQTT traction power cutoff commands (`factory/forklift/{device_id}/control/power_cutoff`) to all forklifts localized in the camera view.
   - Scope delivery: Phase 1 (v2.0) implements software-level MQTT signaling and UI simulation; Phase 2 (v2.1) retrofits physical wireless relays and CAN bus actuators.

5. **Two-Stage Human-in-the-Loop Safety Clearance FSM**:
   - Establish a deterministic two-stage finite state machine for safety officer intervention:
     - **Branch A (False Alarm)**: Officer clicks `[判定误报 · 恢复动力]` $\rightarrow$ Immediate power restoration (`power_restore`) and alarm shutdown $\rightarrow$ Incident archived as `Hard_Negative`.
     - **Branch B (Confirmed Emergency)**: Officer clicks `[确认危急 · 维持制动]` $\rightarrow$ Traction power remains cut off (`HAZARD_CONFIRMED_LOCKED`) while on-site clearance proceeds $\rightarrow$ Officer clicks secondary verification `[危情已解除 · 恢复动力]` $\rightarrow$ Power restored, alarm stopped $\rightarrow$ Incident archived as `True_Positive`.

6. **Audit Sample Feedback & Federated Learning Readiness**:
   - Discard generic buzzwords ("data flywheel").
   - Structure verified audit incidents into multimodal triples: 1080P original frame + YOLO/RedZone/OmniJev features + Officer ground truth.
   - Establish local active learning storage for continuous fine-tuning, with architectural readiness for privacy-preserving Federated Learning across multi-factory deployments.
