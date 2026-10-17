#!/bin/bash
# One-click environment setup script for Slurm RTX 3090 node.
# Model: OmniJev-2B (中科院自动化所 / 北京中关村学院 / Zevo)
# Repository: https://github.com/tinnel123666888/OmniJev

set -e

echo "=========================================================="
echo " Setting up OmniJev (MSO) Environment on RTX 3090 Node"
echo " Model: OmniJev-2B  |  Base: Qwen3.5-2B"
echo "=========================================================="

ENV_NAME="omnijev"
MODEL_DIR="${OMNIJEV_MODEL_DIR:-$HOME/models}"
REPO_DIR="${OMNIJEV_REPO_DIR:-$HOME/OmniJev}"

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

# 5. Install OmniJev inference dependencies (transformers >= 5, peft, pillow)
echo ">>> Installing OmniJev (MSO) inference stack..."
$INSTALL_CMD "transformers>=5" peft pillow accelerate

# 6. Clone OmniJev repository (provides mso package)
echo ">>> Cloning OmniJev repository..."
if [ -d "$REPO_DIR" ]; then
    echo ">>> Repository already exists at $REPO_DIR, pulling latest..."
    git -C "$REPO_DIR" pull || true
else
    git clone https://github.com/tinnel123666888/OmniJev.git "$REPO_DIR"
fi
# Install repo dependencies
$INSTALL_CMD -r "$REPO_DIR/requirements.txt" || true

# 7. Download Model Weights
echo ""
echo ">>> Downloading Qwen3.5-2B base model..."
huggingface-cli download Qwen/Qwen3.5-2B --local-dir "$MODEL_DIR/Qwen3.5-2B" || \
    echo "Notice: Download failed. Set HF_TOKEN or ensure network access to huggingface.co"

echo ">>> Downloading OmniJev-2B LoRA checkpoint..."
huggingface-cli download tinnel123/OmniJev-2B --revision v1.1 --local-dir "$MODEL_DIR/OmniJev-2B" || \
    echo "Notice: Download failed. Set HF_TOKEN or ensure network access to huggingface.co"

echo ""
echo "=========================================================="
echo " Setup Complete!"
echo ""
echo " Models installed to: $MODEL_DIR"
echo " OmniJev repo at:     $REPO_DIR"
echo ""
echo " Test GPU:"
echo "   python3 -c \"import torch; print('CUDA Ready:', torch.cuda.is_available(), torch.cuda.get_device_name(0))\""
echo ""
echo " Quick smoke test:"
echo "   PYTHONPATH=$REPO_DIR python3 -c \"from mso.infer import MSO1; print('MSO1 import OK')\""
echo "=========================================================="
