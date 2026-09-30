#!/usr/bin/env python3
"""Train YOLOv8n sapling detector (forestry) or water body detector (water).

Run:
  python -m training.scripts.train_yolo forestry
  python -m training.scripts.train_yolo water --source s1s2_water
"""

from __future__ import annotations

import argparse
from pathlib import Path

from training.config import CFG
from ultralytics import YOLO


def train_forestry() -> Path:
    cfg = CFG.forestry
    data_yaml = CFG.prepared_root / "forestry_yolo" / "dataset.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"dataset.yaml not found at {data_yaml}. Run prepare_yolo first.")

    print(f"Training forestry sapling detector for {cfg.sapling_epochs} epochs...")
    model = YOLO(cfg.sapling_pretrained)
    model.train(
        data=str(data_yaml),
        epochs=cfg.sapling_epochs,
        imgsz=cfg.sapling_imgsz,
        batch=cfg.sapling_batch,
        lr0=cfg.sapling_lr0,
        lrf=cfg.sapling_lrf,
        momentum=cfg.sapling_momentum,
        weight_decay=cfg.sapling_weight_decay,
        warmup_epochs=cfg.sapling_warmup_epochs,
        patience=cfg.sapling_patience,
        seed=CFG.seed,
        device=CFG.device,
        workers=CFG.num_workers,
        project=str(CFG.logs_dir / "forestry_yolo"),
        name="train",
        exist_ok=True,
    )

    best = Path("runs/detect/forestry_yolo/train/weights/best.pt")
    out = CFG.weights_dir / cfg.sapling_output_name
    if best.exists():
        best.replace(out)
        print(f"Saved best weights to {out}")
    else:
        # Fallback: last.pt
        last = Path("runs/detect/forestry_yolo/train/weights/last.pt")
        if last.exists():
            last.replace(out)
            print(f"Saved last weights to {out}")
        else:
            raise FileNotFoundError("No weights produced by training")

    return out


def train_water(source: str) -> Path:
    cfg = CFG.water
    data_yaml = CFG.prepared_root / f"water_yolo_{source}" / "dataset.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"dataset.yaml not found at {data_yaml}. Run prepare_yolo first.")

    print(f"Training water body detector ({source}) for {cfg.water_epochs} epochs...")
    model = YOLO(cfg.water_pretrained)
    model.train(
        data=str(data_yaml),
        epochs=cfg.water_epochs,
        imgsz=cfg.water_imgsz,
        batch=cfg.water_batch,
        lr0=cfg.water_lr0,
        lrf=cfg.water_lrf,
        momentum=cfg.water_momentum,
        weight_decay=cfg.water_weight_decay,
        warmup_epochs=cfg.water_warmup_epochs,
        patience=cfg.water_patience,
        seed=CFG.seed,
        device=CFG.device,
        workers=CFG.num_workers,
        project=str(CFG.logs_dir / f"water_yolo_{source}"),
        name="train",
        exist_ok=True,
    )

    best = Path(f"runs/detect/water_yolo_{source}/train/weights/best.pt")
    out = CFG.weights_dir / cfg.water_output_name
    if best.exists():
        best.replace(out)
        print(f"Saved best weights to {out}")
    else:
        last = Path(f"runs/detect/water_yolo_{source}/train/weights/last.pt")
        if last.exists():
            last.replace(out)
            print(f"Saved last weights to {out}")
        else:
            raise FileNotFoundError("No weights produced by training")

    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Train YOLO detector")
    p.add_argument("sector", choices=["forestry", "water"])
    p.add_argument(
        "--source",
        choices=["s1s2_water", "glh_water", "atlantis"],
        default="s1s2_water",
    )
    args = p.parse_args()

    if args.sector == "forestry":
        train_forestry()
    else:
        train_water(args.source)