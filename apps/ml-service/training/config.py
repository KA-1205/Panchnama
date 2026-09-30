"""Training configuration for Phase 6.5 — single source of truth for all hyperparameters.

This module is imported by every training/eval/export script so no value is
hard-coded in more than one place. Change here, and every downstream script
inherits the update.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingConfig:
    """Global training config shared by forestry + water pipelines."""

    # --- Runtime ---
    seed: int = 42
    device: str = "cuda"  # "cuda" or "cpu"
    num_workers: int = 8

    # --- Paths (relative to project root or absolute) ---
    data_root: Path = Path("data/raw")
    prepared_root: Path = Path("data/prepared")
    weights_dir: Path = Path("weights")
    logs_dir: Path = Path("logs")
    eval_dir: Path = Path("eval")

    # --- Forestry (sapling) ---
    forestry: ForestryConfig = None  # type: ignore[assignment]

    # --- Water ---
    water: WaterConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Deferred instantiation to avoid circular refs at module load
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


@dataclass(frozen=True)
class ForestryConfig:
    """Forestry-specific (sapling) training config."""

    # YOLOv8n sapling detector
    sapling_epochs: int = 50
    sapling_imgsz: int = 640
    sapling_batch: int = 16
    sapling_lr0: float = 0.01
    sapling_lrf: float = 0.01
    sapling_momentum: float = 0.937
    sapling_weight_decay: float = 0.0005
    sapling_warmup_epochs: float = 3.0
    sapling_patience: int = 10
    sapling_pretrained: str = "yolov8n.pt"  # COCO base
    sapling_output_name: str = "sapling_yolov8n.pt"

    # ChangeFormer (forestry)
    change_epochs: int = 30
    change_imgsz: int = 256
    change_batch: int = 8
    change_lr: float = 1e-4
    change_output_name: str = "changeformer.pt"

    # Datasets
    forestnet_url: str = "https://github.com/forestnet/forestnet/releases/download/v1.0/forestnet_v1.zip"
    levir_cd_url: str = "https://github.com/justchenhao/LEVIR-CD/releases/download/v1.0/LEVIR-CD.zip"


@dataclass(frozen=True)
class WaterConfig:
    """Water-specific training config."""

    # YOLOv8n water body detector
    water_epochs: int = 50
    water_imgsz: int = 640
    water_batch: int = 16
    water_lr0: float = 0.01
    water_lrf: float = 0.01
    water_momentum: float = 0.937
    water_weight_decay: float = 0.0005
    water_warmup_epochs: float = 3.0
    water_patience: int = 10
    water_pretrained: str = "yolov8n.pt"
    water_output_name: str = "water_yolov8n.pt"

    # ChangeFormer (water)
    water_change_epochs: int = 30
    water_change_imgsz: int = 256
    water_change_batch: int = 8
    water_change_lr: float = 1e-4
    water_change_output_name: str = "changeformer_water.pt"

    # Datasets
    s1s2_water_zenodo: str = "https://zenodo.org/records/11278238"
    glh_water_url: str = "https://jack-bo1220.github.io/project/GLH-water.html"
    atlantis_github: str = "https://github.com/smhassanerfani/atlantis"


# Global singleton
CFG = TrainingConfig()