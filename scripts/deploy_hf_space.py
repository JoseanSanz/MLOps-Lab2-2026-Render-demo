"""
Uploads the hf_space/ folder to the Hugging Face Space (used by the CI/CD pipeline).

Environment variables:
    HF_TOKEN   Hugging Face token with write permission (required)
    HF_SPACE   Space id, e.g. "username/MLOps-Lab2-demo" (required)
    API_URL    URL of the API on Render (optional): stored as a variable of the Space
    GIT_SHA    commit being deployed (optional): used in the commit message

Run locally:
    HF_TOKEN=... HF_SPACE=user/MLOps-Lab2-demo uv run python scripts/deploy_hf_space.py
"""

import os
from pathlib import Path

from huggingface_hub import HfApi

SPACE_DIR = Path(__file__).resolve().parent.parent / "hf_space"


def main():
    """Creates the Space if needed, sets API_URL and uploads hf_space/."""
    space_id = os.environ["HF_SPACE"]
    api = HfApi(token=os.environ["HF_TOKEN"])

    # Creates the Space the first time (does nothing if it already exists)
    api.create_repo(space_id, repo_type="space", space_sdk="gradio", exist_ok=True)

    # The URL of the API is a variable of the Space, read by app.py
    api_url = os.environ.get("API_URL")
    if api_url:
        api.add_space_variable(space_id, "API_URL", api_url)

    sha = os.environ.get("GIT_SHA", "local")[:7]
    api.upload_folder(
        folder_path=SPACE_DIR,
        repo_id=space_id,
        repo_type="space",
        commit_message=f"Deploy from GitHub ({sha})",
    )
    print(f"Space updated: https://huggingface.co/spaces/{space_id}")


if __name__ == "__main__":
    main()
