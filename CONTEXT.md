# Intelli-Shield Domain Context

Server-side industrial safety perception and fast-decision system using high-mounted CCTV video feeds, YOLO spatial perception, and OmniJev System 1 decision probes.

## Language

**Pipeline**:
The unified server-side processing loop coordinating video intake, object detection, ROI extraction, OmniJev probe inference, and risk state output.
_Avoid_: Backend worker, script, batch job

**Perception Layer**:
The front-stage vision model (YOLO26 Nano) responsible for bounding-box detection, tracking, and spatial distance calculation of pedestrians and vehicles.
_Avoid_: Decision model, AI core, detector only, YOLO11

**Decision Layer**:
The System 1 multimodal decision model (OmniJev) operating via single forward pass to output calibrated probabilities for risk, attention, and threat levels without generating text tokens.
_Avoid_: LLM, chatbot, generative model, slow thinking

**Decision Probe**:
A structured query (`Noul`, `Choice`, `Score`) evaluated directly against image and prompt inputs in a single forward pass to yield calibrated probabilities.
_Avoid_: Prompt prompt-engineering, text completion, conversation

**Scene Input**:
The visual feed passed to the decision layer, currently evaluated as full-frame CCTV imagery before considering localized dynamic cropping.
_Avoid_: Thumbnail, raw crop, bbox

**Inference Host**:
The remote GPU node (NVIDIA RTX 3090, 24GB VRAM) running OmniJev serving probe evaluations over network API.
_Avoid_: Local worker, edge device, serverless
**Slurm Job**:
The scheduled compute allocation on the cluster running OmniJev on an RTX 3090 node, executed either as batch analysis or interactive tunnel service.
_Avoid_: Daemon, background process, cron

**Risk Fusion Engine**:
The arbitration component that combines geometric metrics (distance, trajectory, velocity) with OmniJev's calibrated probabilities into definitive alert levels (`NORMAL`, `WARNING`, `CRITICAL`).

**Spatial-Temporal Gate**:
The pre-probe filtering mechanism (migrated and enhanced from the advisor's legacy C++ `IsCarAway` algorithm) that excludes on-board drivers, cancels motionless vehicles, and enforces ROI geofences before invoking OmniJev.
_Avoid_: Simple threshold, OpenCV filter, C++ wrapper

**Cognitive Decision Architecture**:
The theoretical framework grounding the system in Kahneman's System 1 (Fast Intuition):
- **Front-Stage Spatial Perception**: Lightweight YOLO model outputting bounding boxes and coarse geometric anchors.
- **Spatial-Temporal Gating**: Self-developed lightweight filter (0.5ms) excluding drivers and stationary vehicles, saving >70% remote GPU compute.
- **Cognitive Decision Layer**: OmniJev evaluated via single forward pass (~107ms, ZERO generative tokens, 0 external LLM APIs) on remote RTX 3090, outputting calibrated probabilities for risk, worker attention, and threat level.
- **Asymmetric Risk Fusion**: Geometry overrides model at critical thresholds (<120px) to guarantee functional safety.
_Avoid_: Generative LLM, Chatbot, external API, slow text generation, token streaming
