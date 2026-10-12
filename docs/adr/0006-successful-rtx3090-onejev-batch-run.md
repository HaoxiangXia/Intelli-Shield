# 0006. Successful RTX 3090 OneJev System 1 Execution on Cluster

We verified the complete execution of OmniJev (OneJev-0.8B) on node `compute01` of the YSU HPC cluster (`ysuhpc`).

Key Metrics Recorded from Slurm Job 18072:
- **Device**: NVIDIA GeForce RTX 3090 (24GB VRAM)
- **Engine Load Time**: 31.7s on remote storage
- **Steady-State System 1 Latency**: ~107.0 - 109.0 ms per frame (including CUDA graph execution)
- **Output Artifact**: batch inference output successfully generated and synchronized back to local development environment. It was originally written as `samples/cctv/benchmarks/omnijev_results_real3090.json`, later superseded by `samples/cctv/benchmarks/cctv_frames_metadata.json`（752 帧全时序元数据，`pipeline/runner.py --replay` 的实际输入格式）。
