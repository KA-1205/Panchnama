#!/usr/bin/env python3
"""Export trained models to ONNX for production inference.

Run:
  python -m training.scripts.export_onnx forestry
  python -m training.scripts.export_onnx water --source s1s2_water
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from ultralytics import YOLO

from training.config import CFG


def export_yolo(weights: Path, out_path: Path, imgsz: int) -> None:
    """Export YOLO model to ONNX."""
    print(f"Exporting {weights} → {out_path} (imgsz={imgsz})")
    model = YOLO(str(weights))
    model.export(
        format="onnx",
        imgsz=imgsz,
        opset=12,
        simplify=True,
        dynamic=True,
        device=CFG.device,
    )
    # YOLO saves to runs/detect/.../weights/best.onnx
    # Move to our weights dir
    generated = Path("runs/detect") / weights.stem / "weights" / "best.onnx"
    if generated.exists():
        generated.replace(out_path)
        print(f"  Saved to {out_path}")
    else:
        # Try alternative location
        for p in Path(".").rglob("*.onnx"):
            if "best" in p.name:
                p.replace(out_path)
                print(f"  Saved to {out_path}")
                break
        else:
            raise FileNotFoundError("ONNX export not found")


def export_changeformer(weights: Path, out_path: Path, imgsz: int) -> None:
    """Export ChangeFormer to ONNX (placeholder — adapt to your architecture)."""
    print(f"Exporting ChangeFormer {weights} → {out_path}")
    # TODO: Implement actual ChangeFormer ONNX export
    # This requires the actual model architecture from train_change.py
    # For now, create a placeholder
    dummy = torch.zeros(1, 3, imgsz, imgsz)
    # model = ChangeFormer()
    # model.load_state_dict(torch.load(weights))
    # torch.onnx.export(model, (dummy, dummy), out_path, opset_version=12, input_names=['before', 'after'], output_names=['change_logits'], dynamic_axes={'before': {0: 'batch'}, 'after': {0: 'batch'}, 'change_logits': {0: 'batch'}})
    raise NotImplementedError("ChangeFormer ONNX export needs actual model class")


def export_forestry() -> None:
    cfg = CFG.forestry
    weights_dir = CFG.weights_dir

    export_yolo(weights_dir / cfg.sapling_output_name, weights_dir / "sapling_yolov8n.onnx", cfg.sapling_imgsz)
    export_changeformer(weights_dir / cfg.change_output_name, weights_dir / "changeformer.onnx", cfg.change_imgsz)
    # COCO base
    export_yolo(weights_dir / "yolov8n.pt", weights_dir / "yolov8n.onnx", cfg.sapling_imgsz)


def export_water(source: str) -> None:
    cfg = CFG.water
    weights_dir = CFG.weights_dir

    export_yolo(weights_dir / cfg.water_output_name, weights_dir / "water_yolov8n.onnx", cfg.water_imgsz)
    export_changeformer(weights_dir / cfg.water_change_output_name, weights_dir / "changeformer_water.onnx", cfg.water_change_imgsz)
    export_yolo(weights_dir / "yolov8n.pt", weights_dir / "yolov8n.onnx", cfg.water_imgsz)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Export models to ONNX")
    p.add_argument("sector", choices=["forestry", "water"])
    p.add_argument("--source", choices=["s1s2_water", "glh_water", "atlantis"], default="s1s2_water")
    args = p.parse_args()

    if args.sector == "forestry":
        export_forestry()
    else:
        export_water(args.source)