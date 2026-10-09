#!/bin/bash
#SBATCH --job-name=omnijev-serve
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=slurm/logs/serve_%j.log
#SBATCH --error=slurm/logs/serve_%j.err

mkdir -p slurm/logs

echo "=========================================================="
echo " Starting OmniJev Service on Node: $(hostname)"
echo " Job ID: $SLURM_JOB_ID"
echo " CUDA Visible Devices: $CUDA_VISIBLE_DEVICES"
echo " Date: $(date)"
echo "=========================================================="

# Port to bind
PORT=8000
NODE_IP=$(hostname -I | awk '{print $1}')
NODE_NAME=$(hostname)

echo ""
echo ">>> SSH Tunnel Instruction for Local Client:"
echo ">>> Run this command on your local machine to forward port 8000:"
echo ">>> ssh -N -L 8000:${NODE_NAME}:${PORT} <your_cluster_login_host>"
echo ""

# Activate your cluster virtual environment if needed
# source ~/.bashrc
# conda activate omnijev

export PORT=${PORT}
export OMNIJEV_MODEL="OneJev-0.8B"

python3 slurm/serve_omnijev.py
