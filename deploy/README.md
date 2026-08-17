# ReAlIty Web API

AI vs Human image/video detector API built with FastAPI and SigLIP.

## Deploy

### Option A: Hugging Face Spaces (Recommended for ML models)
1. Create a Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Choose "Docker" as the SDK
3. Push this repo to the Space (use Git LFS for `reality-finetuned/final/model.safetensors`)
4. Space will build and serve the API automatically

### Option B: Render
1. Create a new Web Service on [render.com](https://render.com)
2. Connect your GitHub repo
3. Set:
   - **Build Command:** `pip install -r deploy/requirements.txt`
   - **Start Command:** `python -m uvicorn webapp.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables if needed

### Option C: Railway
1. Connect repo on [railway.app](https://railway.app)
2. Railway auto-detects the Dockerfile

## API Endpoints

- `GET /` — Serves the web UI
- `POST /detect` — Upload image/video, returns detection result
- `GET /health` — Health check

### POST /detect Response
```json
{
  "success": true,
  "media_type": "image",
  "filename": "photo.jpg",
  "ai": 92.4,
  "hum": 7.6,
  "overlay_detected": false,
  "overlay_pct": 0.0
}
```
