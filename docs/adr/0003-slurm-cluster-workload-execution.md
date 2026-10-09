# 0003. Slurm Workload Execution on RTX 3090 Cluster

The RTX 3090 GPU compute environment is managed via the Slurm Workload Manager rather than an open web server.

We decided to support both:
1. A batch Slurm job (`sbatch`) that processes CCTV videos/frames offline and outputs structured OmniJev JSON logs.
2. An interactive/tunnelable Slurm job that runs the FastAPI probe worker with SSH port-forwarding for real-time streaming demonstrations.
