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
The System 1 multimodal cognitive model (OmniJev) operating via single forward pass on every processed frame to output calibrated probabilities for risk, attention, dangerous worker behavior, and threat severity without generating text tokens.
_Avoid_: LLM, chatbot, generative model, slow thinking, sporadic invocation

**Decision Probe**:
A structured query (`Noul`, `Choice`, `Score`) evaluated directly against image and prompt inputs in a single forward pass on every frame. Currently encompasses collision probability, worker attention, hazardous worker behavior, and threat score.
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

**Pre-Perception Sanitizer**:
The spatial pre-filtering mechanism that sanitizes visual detections (e.g., excluding on-board drivers via Intersection-over-Person) and validates ground anchors before dispatching full-frame imagery to OmniJev on every frame.
_Avoid_: Spatial-temporal compute gate, frame skipper, bypass filter

**Hazardous Worker Behavior**:
Specific non-compliant or high-risk worker states (such as smartphone distraction or turning back to oncoming machinery) detected directly by OmniJev's cognitive probes.
_Avoid_: Generic distraction, posture anomaly, rule-based skeleton analysis

**Fleet Power Interlock**:
The active safety mechanism commanding immediate traction power cutoff and audible/visual alarms across all forklifts localized in the camera view whenever risk exceeds critical threshold.
_Avoid_: Physical AEB pedal control, manual handbrake, individual vehicle steering

**Two-Stage Safety Clearance**:
The human-in-the-loop arbitration state machine requiring an initial hazard confirmation followed by a mandatory secondary on-site clearance verification before vehicle power can be restored.
_Avoid_: Single-click dismissal, auto-resume timer, unverified power recovery

**Audit Sample Feedback Repository**:
The multimodal archival repository capturing synchronized CCTV snapshots, model probe predictions, and safety officer audit labels to provide verified training corpora for continuous model fine-tuning and federated learning aggregation.
_Avoid_: Raw video archive, simple server access log, unstructured telemetry dump, data flywheel buzzword

**Cognitive Decision Architecture**:
The theoretical framework grounding the system in Kahneman's System 1 (Fast Intuition):
- **Front-Stage Spatial Perception**: Lightweight YOLO model outputting bounding boxes and coarse geometric anchors.
- **Pre-Perception Sanitization**: Geometry filter excluding in-cab drivers to prevent false positives.
- **Full-Frame Cognitive Decision Layer**: OmniJev evaluated via single forward pass (~107ms, ZERO generative tokens) on every processed frame across 4 synchronized probes.
- **Asymmetric Risk Fusion & Interlock**: Geometry and probe risk arbitration triggering fleet power interlock and two-stage safety clearance.
_Avoid_: Generative LLM, Chatbot, external API, slow text generation, token streaming

**Virtual Hardware Interlock Console**:
The digital twin telemetry and logic terminal that visualizes edge hardware GPIO states, relay interlock transitions, and sub-millisecond electrical latencies on screen.
_Avoid_: Fake UI, dummy indicator, mock dashboard

**EVT-1 Breadboard Prototype**:
The first-stage desktop electrical validation hardware comprising the microcontroller, optocoupled relays, laser modules, and acoustic-optic beacons to verify circuit logic and microsecond command execution.
_Avoid_: Toy circuit, temporary hack, breadboard mess

**DVT-2 Industrial Enclosure & PCB Design**:
The second-stage mechanical packaging (3D CAD chassis with heatsinks and IP65 glands) and customized PCB schematic/layout engineered for high-vibration forklift operating environments.
_Avoid_: Conceptual drawing, unfinished product, pure 3D art
