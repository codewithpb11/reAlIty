FROM python:3.11-slim

WORKDIR /app

# Install system libraries required by OpenCV and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY webapp/ ./webapp/
COPY detector.py .
COPY media_utils.py .
COPY video_utils.py .

# Hugging Face Spaces expects port 7860
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "7860"]
