# 0002. Remote RTX 3090 Inference Host and Full-Frame Input Strategy

We decided to execute OmniJev model inference on a dedicated remote GPU server equipped with an NVIDIA RTX 3090 (24GB VRAM), decoupling the local workstation from heavy neural compute.

We also decided to evaluate full-frame CCTV input directly with OmniJev before introducing dynamic ROI cropping, validating whether global scene perspective alone is sufficient for System 1 risk assessment.
