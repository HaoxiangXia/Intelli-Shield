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

# 2. Determine package manager (uv pip if available, fallback to pip)
INSTALL_CMD="pip install"
if command -v uv &> /dev/null; then
    echo ">>> Detected uv, using fast 'uv pip install'..."
    INSTALL_CMD="uv pip install"
else
    echo ">>> uv not found, falling back to standard pip..."
    pip install --upgrade pip || true
fi

# 3. Install PyTorch with CUDA 12.1
echo ">>> Installing PyTorch with CUDA support..."
$INSTALL_CMD torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 4. Install Core Libraries & HuggingFace Hub
echo ">>> Installing FastAPI, OpenCV, and utilities..."
$INSTALL_CMD fastapi uvicorn "opencv-python-headless>=4.8,<5.0" pydantic requests "numpy>=1.24" huggingface_hub

# 5. Install OmniJev (qev) & Clone OneJev official repository
echo ">>> Installing OmniJev runtime (qev)..."
$INSTALL_CMD qev || $INSTALL_CMD git+https://github.com/OmniJev/OneJev.git || echo "Notice: Ensure network access to github.com/OmniJev/OneJev"
# 6. Download Model Weights (PlayJev-0.8B for 30ms latency or OneJev-9B)
echo ""
echo ">>> To download the model weights to your cluster scratch space, run:"
echo ">>> huggingface-cli download OmniJev/PlayJev-0.8B --local-dir ~/models/PlayJev-0.8B"
echo ""

echo "=========================================================="
echo " Setup Complete! Test GPU with:"
echo " python3 -c \"import torch; print('CUDA Ready:', torch.cuda.is_available(), torch.cuda.get_device_name(0))\""
echo "=========================================================="
