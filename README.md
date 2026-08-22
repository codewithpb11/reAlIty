# reAlIty Detector API

Backend API for the **reAlIty** mobile app — detect whether an image is AI-generated or human-made.

## Endpoints

- `POST /detect` — Upload an image or video for AI/human detection
- `GET /health` — Health check

## Model

Uses a fine-tuned SigLIP model hosted on Hugging Face Hub: `pb11-x/reality-detector-model`

## How to use

This Space powers the reAlIty mobile app. The app sends images here and receives detection results.
