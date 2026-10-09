#!/bin/bash
# One-click environment setup script for Slurm RTX 3090 node (OmniJev / OneJev).

set -e

echo "=========================================================="
echo " Setting up OmniJev / OneJev Environment on RTX 3090 Node"
echo "=========================================================="

ENV_NAME="omnijev"

# 1. Check Conda
if command -v conda &> /dev/null; then
    echo ">>> Found Conda. Initializing environment: $ENV_NAME"
    conda create -n $ENV_NAME python=3.10 -y
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate $ENV_NAME
else
    echo ">>> Conda not found. Creating virtualenv via python3 -m venv..."
    python3 -m venv ~/.venvs/$ENV_NAME
    source ~/.venvs/$ENV_NAME/bin/activate
fi

# 2. Install PyTorch with CUDA 12.1
echo ">>> Installing PyTorch with CUDA support..."
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Install Core Libraries & HuggingFace Hub
echo ">>> Installing FastAPI, OpenCV, and utilities..."
pip install fastapi uvicorn opencv-python-headless pydantic requests numpy huggingface_hub

# 4. Install OmniJev (qev) & Clone OneJev official repository
echo ">>> Installing OmniJev runtime (qev)..."
pip install qev || pip install git+https://github.com/OmniJev/OneJev.git || echo "Notice: Ensure network access to github.com/OmniJev/OneJev"

# 5. Download Model Weights (PlayJev-0.8B for 30ms latency or OneJev-9B)
echo ""
echo ">>> To download the model weights to your cluster scratch space, run:"
echo ">>> huggingface-cli download OmniJev/PlayJev-0.8B --local-dir ~/models/PlayJev-0.8B"
echo ""

echo "=========================================================="
echo " Setup Complete! Test GPU with:"
echo " python3 -c \"import torch; print('CUDA Ready:', torch.cuda.is_available(), torch.cuda.get_device_name(0))\""
echo "=========================================================="
