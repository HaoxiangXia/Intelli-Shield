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
_Avoid_: If-else filter, alarm script
