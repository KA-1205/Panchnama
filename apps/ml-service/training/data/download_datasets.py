#!/usr/bin/env python3
"""Download ForestNet and LEVIR-CD for forestry training.

Run: python -m training.data.download_forestnet
     python -m training.data.download_levir_cd

These are public datasets — no auth required. The downloads are large (~1-2 GB each)
so this script supports resume and checksum verification.
"""

from __future__ import annotations

import hashlib
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

from training.config import CFG

CHUNK_SIZE = 1024 * 1024  # 1 MB


def _download_with_resume(url: str, dest: Path, expected_sha256: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {}
    if dest.exists():
        headers["Range"] = f"bytes={dest.stat().st_size}-"

    req = Request(url, headers=headers)
    with urlopen(req) as resp, dest.open("ab") as f:
        total = resp.length or 0
        if headers:
            print(f"Resuming {dest.name} from {dest.stat().st_size} bytes...")
        else:
            print(f"Downloading {dest.name} ({total / 1e9:.1f} GB)...")

        downloaded = 0
        while chunk := resp.read(CHUNK_SIZE):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = (dest.stat().st_size / (total + headers.get("Range", 0))) * 100
                print(f"\r  {pct:.1f}%", end="", flush=True)

    print(f"\n  Done: {dest}")

    if expected_sha256:
        print("  Verifying SHA256...")
        sha = hashlib.sha256(dest.read_bytes()).hexdigest()
        if sha != expected_sha256:
            raise ValueError(f"Checksum mismatch: got {sha}, expected {expected_sha256}")
        print("  Checksum OK")


def _extract(archive: Path, out_dir: Path) -> None:
    print(f"Extracting {archive.name}...")
    out_dir.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(out_dir)
    elif archive.suffix in (".tar", ".gz", ".tgz"):
        with tarfile.open(archive) as tf:
            tf.extractall(out_dir)
    else:
        raise ValueError(f"Unknown archive format: {archive.suffix}")
    print(f"  Extracted to {out_dir}")


def download_forestnet() -> None:
    """Download ForestNet (GEO-Bench version, ~1.2 GB)."""
    url = CFG.forestry.forestnet_url
    dest = CFG.data_root / "forestnet.zip"
    _download_with_resume(url, dest)
    _extract(dest, CFG.data_root / "forestnet")


def download_levir_cd() -> None:
    """Download LEVIR-CD train/val/test splits (~1 GB total)."""
    urls = {
        "train": CFG.forestry.levir_cd_train_url,
        "val": CFG.forestry.levir_cd_val_url,
        "test": CFG.forestry.levir_cd_test_url,
    }
    for split, url in urls.items():
        dest = CFG.data_root / f"LEVIR-CD_{split}.zip"
        _download_with_resume(url, dest)
        # Extract each split into LEVIR-CD/{split}/
        _extract(dest, CFG.data_root / "LEVIR-CD" / split)


def download_s1s2_water() -> None:
    """Download S1S2-Water from Zenodo (huge, ~170 GB) — use mirror or subset.

    This is a placeholder. In practice you would:
    1. Use the Hugging Face mirror: `huggingface-cli download idomogalla/s1s2_water`
    2. Or download only the validation split for quick iteration.
    """
    print("S1S2-Water is ~170 GB — use the Hugging Face mirror for faster download:")
    print("  huggingface-cli download idomogalla/s1s2_water --local-dir data/raw/s1s2_water")
    print("Or download a subset from the Zenodo record:", CFG.water.s1s2_water_zenodo)


def download_glh_water() -> None:
    """GLH-Water (~40 GB) — manual download from project page."""
    print(f"GLH-Water: visit {CFG.water.glh_water_url} for download links")
    print("Or use the Hugging Face mirror if available")


def download_atlantis() -> None:
    """ATLANTIS (~5 GB) — from Google Drive link in GitHub repo."""
    print(f"ATLANTIS: see {CFG.water.atlantis_github} for Google Drive download")


if __name__ == "__main__":
    cmds = (
        "download_forestnet|download_levir_cd|download_s1s2_water|"
        "download_glh_water|download_atlantis"
    )
    if len(sys.argv) < 2:
        print(f"Usage: python -m training.data.{cmds}")
        sys.exit(1)

    fn = sys.argv[1]
    if fn == "download_forestnet":
        download_forestnet()
    elif fn == "download_levir_cd":
        download_levir_cd()
    elif fn == "download_s1s2_water":
        download_s1s2_water()
    elif fn == "download_glh_water":
        download_glh_water()
    elif fn == "download_atlantis":
        download_atlantis()
    else:
        print(f"Unknown command: {fn}")
        sys.exit(1)