"""
Upload your trained model to Hugging Face Hub.
This makes it accessible to your deployed backend without committing 355MB to git.

Usage:
    1. pip install huggingface-hub
    2. huggingface-cli login
    3. python deploy/upload_model_to_hf.py
"""

import os
import sys
from pathlib import Path

# Model source (your local fine-tuned model)
MODEL_DIR = Path("reality-finetuned/final")

# Hugging Face repo name (change 'your-username' to your actual HF username)
HF_USERNAME = input("Enter your Hugging Face username: ").strip()
REPO_ID = f"{HF_USERNAME}/reality-detector-model"

def upload():
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: huggingface-hub not installed.")
        print("Run: pip install huggingface-hub")
        sys.exit(1)

    if not MODEL_DIR.exists():
        print(f"ERROR: Model directory not found: {MODEL_DIR}")
        print("Make sure you're running this from the project root.")
        sys.exit(1)

    api = HfApi()

    # Create the model repo if it doesn't exist
    print(f"Creating repo: {REPO_ID} ...")
    try:
        create_repo(REPO_ID, repo_type="model", exist_ok=True)
    except Exception as e:
        print(f"Error creating repo: {e}")
        print("Make sure you're logged in: huggingface-cli login")
        sys.exit(1)

    # Upload all files from the model directory
    print(f"Uploading model files from {MODEL_DIR} ...")
    for file_path in MODEL_DIR.iterdir():
        if file_path.is_file():
            print(f"  Uploading: {file_path.name} ...")
            api.upload_file(
                path_or_fileobj=str(file_path),
                path_in_repo=file_path.name,
                repo_id=REPO_ID,
                repo_type="model",
            )

    print(f"\nSUCCESS! Model uploaded to: https://huggingface.co/{REPO_ID}")
    print(f"\nNext steps:")
    print(f"  1. Update detector.py:")
    print(f'     MODEL_ID = "{REPO_ID}"')
    print(f"  2. Deploy to Hugging Face Spaces")
    print(f"  3. Update mobile-app/App.js with your Space URL")

if __name__ == "__main__":
    upload()
