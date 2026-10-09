#!/bin/bash
#SBATCH --job-name=omnijev-batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=slurm/logs/batch_%j.log
#SBATCH --error=slurm/logs/batch_%j.err

mkdir -p slurm/logs

echo "=========================================================="
echo " Running OmniJev Batch Analysis on Node: $(hostname)"
echo " Job ID: $SLURM_JOB_ID"
echo " Date: $(date)"
echo "=========================================================="

VIDEO=${1:-"samples/cctv/demo_forklift.mp4"}
OUTPUT=${2:-"samples/cctv/omnijev_results.json"}

# source ~/.bashrc
# conda activate omnijev

python3 slurm/batch_omnijev.py --video "$VIDEO" --output "$OUTPUT" --stride 2 --model "OneJev-0.8B"
