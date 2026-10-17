# 0006. Successful RTX 3090 OmniJev System 1 Execution on Cluster

We verified the complete execution of OmniJev (OmniJev-4B via MSO1) on node `compute01` of the YSU HPC cluster (`ysuhpc`).

Key Metrics Recorded from Slurm GPU Execution:
- **Device**: NVIDIA GeForce RTX 3090 (24GB VRAM)
- **Model Scale**: OmniJev-4B (Qwen3.5-4B + LoRA adapter)
- **Steady-State System 1 Latency**: ~107.4 ms per frame (single forward pass, zero generative tokens)
- **Output Artifact**: batch inference output successfully generated and synchronized back to local development environment. Superseded by `samples/cctv/benchmarks/cctv_frames_metadata.json` (752-frame temporal metadata for deterministic replay via `pipeline/runner.py --replay`).
