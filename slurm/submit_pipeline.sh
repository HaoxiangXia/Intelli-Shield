#!/bin/bash
#SBATCH --job-name=cctv-pipeline
#SBATCH --partition=dlq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=/archive/xhx/Intelli-Shield/slurm/logs/pipeline_%j.log
#SBATCH --error=/archive/xhx/Intelli-Shield/slurm/logs/pipeline_%j.err

mkdir -p /archive/xhx/Intelli-Shield/slurm/logs

echo "=========================================================="
echo " Starting Full CCTV Pipeline on Node: $(hostname)"
echo " GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null)"
echo " Job ID: $SLURM_JOB_ID"
echo " Date: $(date)"
echo "=========================================================="

source /archive/xhx/miniconda3/etc/profile.d/conda.sh
conda activate omnijev

export CUDA_VISIBLE_DEVICES=0

python3 /archive/xhx/Intelli-Shield/slurm/run_full_cctv_pipeline.py \
    --video /archive/xhx/Intelli-Shield/samples/cctv/videos/output_video7.mp4 \
    --output /archive/xhx/Intelli-Shield/samples/cctv/benchmarks/cctv_frames_metadata.json \
    --yolo /archive/xhx/Intelli-Shield/yolo26n.pt \
    --model /archive/xhx/models/OneJev-0.8B \
    --stride 1
