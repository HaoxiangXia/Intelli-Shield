#!/bin/bash
#SBATCH --job-name=onejev-batch
#SBATCH --partition=dlq
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/archive/xhx/Intelli-Shield/slurm/logs/batch_%j.log
#SBATCH --error=/archive/xhx/Intelli-Shield/slurm/logs/batch_%j.err

mkdir -p /archive/xhx/Intelli-Shield/slurm/logs

echo "=========================================================="
echo " Starting OneJev-0.8B Batch Evaluation on Node: $(hostname)"
echo " Job ID: $SLURM_JOB_ID"
echo " Date: $(date)"
echo "=========================================================="

# Activate Conda Environment
source /archive/xhx/miniconda3/etc/profile.d/conda.sh
conda activate omnijev

export CUDA_VISIBLE_DEVICES=0

python3 /archive/xhx/Intelli-Shield/slurm/run_real_3090_batch.py \
    --video /archive/xhx/Intelli-Shield/samples/cctv/demo_forklift.mp4 \
    --output /archive/xhx/Intelli-Shield/samples/cctv/omnijev_results_real3090.json \
    --model /archive/xhx/models/OneJev-0.8B \
    --stride 4 \
    --max-frames 20
