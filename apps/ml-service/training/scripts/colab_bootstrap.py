#!/usr/bin/env python3
"""Colab/Kaggle bootstrap — run this FIRST in your notebook to set up the environment.

Usage in Colab:
    from google.colab import drive
    drive.mount('/content/drive')
    %cd /content/drive/MyDrive/impact-platform
    !pip install -q -r apps/ml-service/training/requirements_colab.txt
    %run apps/ml-service/training/scripts/colab_bootstrap.py

Usage in Kaggle:
    - Add this repo as a dataset or use GitHub integration
    - Enable Internet + GPU in settings
    - Run this cell first
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def in_colab() -> bool:
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        return False


def in_kaggle() -> bool:
    return os.environ.get("KAGGLE_KERNEL_RUN_TYPE") is not None


def setup_colab() -> Path:
    """Mount Drive, clone repo, install deps."""
    from google.colab import drive
    print("Mounting Google Drive...")
    drive.mount("/content/drive")

    repo_path = Path("/content/drive/MyDrive/impact-platform")
    if not repo_path.exists():
        print("Cloning repo to Drive...")
        subprocess.run(
            ["git", "clone", "https://github.com/YOUR_REPO.git", str(repo_path)],
            check=True,
        )
    else:
        print(f"Repo exists at {repo_path}")

    os.chdir(repo_path / "apps" / "ml-service")
    return repo_path


def setup_kaggle() -> Path:
    """Kaggle has the repo in /kaggle/working or as a dataset."""
    # If added as dataset, it's at /kaggle/input/impact-platform
    # If cloned in working, it's at /kaggle/working/impact-platform
    candidates = [
        Path("/kaggle/input/impact-platform"),
        Path("/kaggle/working/impact-platform"),
        Path("/kaggle/working"),
    ]
    for c in candidates:
        if (c / "apps" / "ml-service").exists():
            os.chdir(c / "apps" / "ml-service")
            print(f"Found repo at {c}")
            return c
    raise FileNotFoundError("Could not find impact-platform repo in Kaggle environment")


def install_requirements(platform: str) -> None:
    """Install platform-specific requirements."""
    req_file = {
        "colab": "requirements_colab.txt",
        "kaggle": "requirements_kaggle.txt",
    }[platform]

    req_path = Path("training") / req_file
    if req_path.exists():
        print(f"Installing {req_file}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_path)],
            check=True,
        )
    else:
        print(f"Warning: {req_path} not found, installing base requirements")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "ultralytics",
                "torch",
                "torchvision",
                "albumentations",
            ],
            check=True,
        )


def verify_gpu() -> None:
    import torch
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("WARNING: No GPU detected! Training will be very slow.")


def main() -> None:
    if in_colab():
        print("=== Google Colab detected ===")
        setup_colab()
        install_requirements("colab")
    elif in_kaggle():
        print("=== Kaggle detected ===")
        setup_kaggle()
        install_requirements("kaggle")
    else:
        print("=== Local environment ===")
        # Assume we're already in the right place
        pass

    verify_gpu()
    print("\nEnvironment ready. You can now run:")
    print("  python -m training.data.download_forestnet")
    print("  python -m training.data.download_levir_cd")
    print("  python -m training.data.prepare_yolo forestry")
    print("  python -m training.scripts.train_yolo forestry")


if __name__ == "__main__":
    main()