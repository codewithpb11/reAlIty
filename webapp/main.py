"""
reAlIty Web — FastAPI backend
Serves the detection API and the static frontend.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path and change CWD so relative model paths resolve correctly
import sys
PROJECT_ROOT = str(Path(__file__).parent.parent.resolve())
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from detector import detect_image, detect_video
from media_utils import detect_media_type

app = FastAPI(title="reAlIty Web", version="1.0.0")

# Serve static frontend files
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

# Upload temp directory
UPLOAD_DIR = Path("webapp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max upload sizes
MAX_IMAGE_MB = 50
MAX_VIDEO_MB = 200


@app.get("/")
async def root():
    return FileResponse("webapp/static/index.html")


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Accept an uploaded image or video and return the detection result.
    """
    # Validate file exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Check file size (read into memory to check)
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    # Save to temp file
    ext = Path(file.filename).suffix.lower()
    temp_name = f"{uuid.uuid4().hex}{ext}"
    temp_path = UPLOAD_DIR / temp_name

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        # Detect media type
        try:
            media_type = detect_media_type(str(temp_path))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Size limits
        if media_type == "image" and size_mb > MAX_IMAGE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large ({size_mb:.1f} MB). Max: {MAX_IMAGE_MB} MB."
            )
        if media_type == "video" and size_mb > MAX_VIDEO_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Video too large ({size_mb:.1f} MB). Max: {MAX_VIDEO_MB} MB."
            )

        # Run detection
        if media_type == "image":
            result = detect_image(str(temp_path))
        else:
            result = detect_video(str(temp_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Convert numpy types to native Python types for JSON serialization
        clean_result = {}
        for k, v in result.items():
            if hasattr(v, 'item'):  # numpy scalar
                clean_result[k] = v.item()
            else:
                clean_result[k] = v

        return JSONResponse(content={
            "success": True,
            "media_type": media_type,
            "filename": file.filename,
            **clean_result,
        })

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.get("/health")
async def health():
    return {"status": "ok"}
