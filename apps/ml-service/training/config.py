"""Training configuration for Phase 6.5 — single source of truth for all hyperparameters.

This module is imported by every training/eval/export script so no value is
hard-coded in more than one place. Change here, and every downstream script
inherits the update.

Environment variables override config for CI/demo vs production:
- TRAINING_EPOCHS_OVERRIDE: comma-separated "forestry_change=200,water_change=200"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _get_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _get_num_workers() -> int:
    cpu = os.cpu_count() or 2
    return min(8, cpu)


def _parse_epochs_override() -> dict[str, int]:
    """Parse TRAINING_EPOCHS_OVERRIDE env var: 'forestry_change=200,water_change=200'."""
    raw = os.environ.get("TRAINING_EPOCHS_OVERRIDE", "")
    out = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = int(v)
    return out


_EPOCHS_OVERRIDE = _parse_epochs_override()


@dataclass(frozen=True)
class TrainingConfig:
    """Global training config shared by forestry + water pipelines."""

    # --- Runtime ---
    seed: int = 42
    device: str = field(default_factory=_get_device)
    num_workers: int = field(default_factory=_get_num_workers)

    # --- Paths (anchored to project root) ---
    project_root: Path = Path(__file__).resolve().parents[2]  # apps/ml-service/
    data_root: Path = field(default_factory=lambda: Path("data/raw"))
    prepared_root: Path = field(default_factory=lambda: Path("data/prepared"))
    weights_dir: Path = field(default_factory=lambda: Path("weights"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    eval_dir: Path = field(default_factory=lambda: Path("eval"))

    # --- Forestry (sapling) ---
    forestry: ForestryConfig = None  # type: ignore[assignment]

    # --- Water ---
    water: WaterConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "forestry", ForestryConfig())
        object.__setattr__(self, "water", WaterConfig())

        for d in (
            self.data_root,
            self.prepared_root,
            self.weights_dir,
            self.logs_dir,
            self.eval_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


def _get_batch_size() -> int:
    """Get batch size from env var, default to 16."""
    try:
        return int(os.environ.get("TRAINING_BATCH_SIZE", "16"))
    except ValueError:
        return 16


@dataclass(frozen=True)
class ForestryConfig:
    """Forestry-specific (sapling) training config."""

    # YOLOv8n sapling detector — production defaults
    sapling_epochs: int = 50
    sapling_imgsz: int = 640
    sapling_batch: int = field(default_factory=_get_batch_size)
    sapling_lr0: float = 0.01
    sapling_lrf: float = 0.01
    sapling_momentum: float = 0.937
    sapling_weight_decay: float = 0.0005
    sapling_warmup_epochs: float = 3.0
    sapling_patience: int = 10
    sapling_pretrained: str = "yolov8n.pt"  # COCO base
    sapling_output_name: str = "sapling_yolov8n.pt"

    # ChangeFormer (forestry) — production epochs for LEVIR-CD
    change_epochs: int = _EPOCHS_OVERRIDE.get("forestry_change", 200)
    change_imgsz: int = 256
    change_batch: int = field(default_factory=_get_batch_size)
    change_lr: float = 1e-4
    change_output_name: str = "changeformer.pt"

    # Datasets
    forestnet_url: str = "https://zenodo.org/records/8008717/files/data.zip"
    levir_cd_train_url: str = "https://huggingface.co/datasets/satellite-image-deep-learning/LEVIR-CD/resolve/main/train.zip"
    levir_cd_val_url: str = "https://huggingface.co/datasets/satellite-image-deep-learning/LEVIR-CD/resolve/main/val.zip"
    levir_cd_test_url: str = "https://huggingface.co/datasets/satellite-image-deep-learning/LEVIR-CD/resolve/main/test.zip"


@dataclass(frozen=True)
class WaterConfig:
    """Water-specific training config."""

    # YOLOv8n water body detector — production defaults
    water_epochs: int = 50
    water_imgsz: int = 640
    water_batch: int = field(default_factory=_get_batch_size)
    water_lr0: float = 0.01
    water_lrf: float = 0.01
    water_momentum: float = 0.937
    water_weight_decay: float = 0.0005
    water_warmup_epochs: float = 3.0
    water_patience: int = 10
    water_pretrained: str = "yolov8n.pt"
    water_output_name: str = "water_yolov8n.pt"

    # ChangeFormer (water) — production epochs
    water_change_epochs: int = _EPOCHS_OVERRIDE.get("water_change", 200)
    water_change_imgsz: int = 256
    water_change_batch: int = field(default_factory=_get_batch_size)
    water_change_lr: float = 1e-4
    water_change_output_name: str = "changeformer_water.pt"

    # Datasets
    s1s2_water_zenodo: str = "https://zenodo.org/records/11278238"
    glh_water_url: str = "https://jack-bo1220.github.io/project/GLH-water.html"
    atlantis_github: str = "https://github.com/smhassanerfani/atlantis"


# Global singleton
CFG = TrainingConfig()