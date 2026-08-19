"""
Upload your trained model to Hugging Face Hub.
Usage: Set HF_TOKEN env var, then run: python deploy/upload_model.py
"""
import os
import sys
from pathlib import Path

MODEL_DIR = Path("reality-finetuned/final")

def upload():
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: huggingface-hub not installed. Run: pip install huggingface-hub")
        sys.exit(1)

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN environment variable not set.")
        print("Get your token from: https://huggingface.co/settings/tokens")
        print("Then run: set HF_TOKEN=your_token_here")
        sys.exit(1)

    username = os.environ.get("HF_USERNAME")
    if not username:
        print("ERROR: HF_USERNAME environment variable not set.")
        sys.exit(1)

    if not MODEL_DIR.exists():
        print(f"ERROR: Model directory not found: {MODEL_DIR}")
        sys.exit(1)

    repo_id = f"{username}/reality-detector-model"
    api = HfApi(token=token)

    print(f"Creating repo: {repo_id} ...")
    try:
        create_repo(repo_id, repo_type="model", exist_ok=True, token=token)
    except Exception as e:
        print(f"Error creating repo: {e}")
        sys.exit(1)

    print(f"Uploading model files from {MODEL_DIR} ...")
    for file_path in MODEL_DIR.iterdir():
        if file_path.is_file():
            print(f"  Uploading: {file_path.name} ...")
            api.upload_file(
                path_or_fileobj=str(file_path),
                path_in_repo=file_path.name,
                repo_id=repo_id,
                repo_type="model",
                token=token,
            )

    print(f"\nSUCCESS! Model uploaded to: https://huggingface.co/{repo_id}")
    print(f"\nNext: Update detector.py MODEL_ID = '{repo_id}'")

if __name__ == "__main__":
    upload()
