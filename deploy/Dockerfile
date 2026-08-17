# reAlIty Web — Deploy-ready backend
# This Dockerfile packages the FastAPI app for cloud deployment.
# The model (355MB) must be provided via:
#   - Hugging Face Hub (recommended: push to a model repo)
#   - Git LFS in the deployment repo
#   - Download URL set via MODEL_URL env var

FROM python:3.11-slim

WORKDIR /app

# Install system deps for opencv and PIL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the webapp and shared modules
COPY webapp/ webapp/
COPY detector.py .
COPY media_utils.py .
COPY video_utils.py .

# Copy model files if present (via build context or mounted)
# If model is not in build context, set MODEL_URL to download it
COPY reality-finetuned/ reality-finetuned/ 2>/dev/null || true

# Download model from URL if MODEL_URL is set and local model not present
ARG MODEL_URL
RUN if [ ! -f "reality-finetuned/final/model.safetensors" ] && [ -n "$MODEL_URL" ]; then \
        echo "Downloading model from $MODEL_URL..." && \
        mkdir -p reality-finetuned/final && \
        pip install gdown && \
        python -c "import gdown; gdown.download('$MODEL_URL', 'reality-finetuned/final/model.safetensors', quiet=False)"; \
    fi

# Pre-download SigLIP processor config from Hugging Face if model missing
# (fallback to base model if custom model not provided)
RUN if [ ! -f "reality-finetuned/final/model.safetensors" ]; then \
        echo "WARNING: Custom model not found. Using base model from Hugging Face." && \
        pip install huggingface-hub && \
        python -c "from transformers import AutoImageProcessor, SiglipForImageClassification; \
                   AutoImageProcessor.from_pretrained('Ateeqq/ai-vs-human-image-detector'); \
                   SiglipForImageClassification.from_pretrained('Ateeqq/ai-vs-human-image-detector')"; \
    fi

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
