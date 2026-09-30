#!/usr/bin/env python3
"""Evaluate trained models (YOLO + ChangeFormer) on test splits.

Run:
  python -m training.scripts.evaluate forestry
  python -m training.scripts.evaluate water --source s1s2_water
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.config import CFG
from ultralytics import YOLO


def evaluate_yolo(weights: Path, data_yaml: Path, sector: str) -> dict:
    """Run YOLO validation and return mAP metrics."""
    print(f"Evaluating {sector} YOLO on {data_yaml}...")
    model = YOLO(str(weights))
    results = model.val(data=str(data_yaml), split="test", device=CFG.device)
    return {
        "mAP50": float(results.box.map50),
        "mAP50_95": float(results.box.map),
        "precision": float(results.box.mp),
        "recall": float(results.box.mr),
    }


def evaluate_changeformer(weights: Path, sector: str) -> dict:
    """Evaluate ChangeFormer on test pairs (placeholder)."""
    print(f"Evaluating {sector} ChangeFormer...")
    # TODO: Implement actual evaluation on test pairs
    # Load model, run on test DataLoader, compute IoU, F1
    return {
        "IoU": 0.0,
        "F1": 0.0,
        "precision": 0.0,
        "recall": 0.0,
    }


def evaluate_forestry() -> dict:
    cfg = CFG.forestry
    weights = CFG.weights_dir / cfg.sapling_output_name
    data_yaml = CFG.prepared_root / "forestry_yolo" / "dataset.yaml"

    yolo_metrics = evaluate_yolo(weights, data_yaml, "forestry")
    cf_metrics = evaluate_changeformer(CFG.weights_dir / cfg.change_output_name, "forestry")

    return {
        "sector": "forestry",
        "version": "v1.0",  # Will be set by promote_model.py
        "yolo": yolo_metrics,
        "changeformer": cf_metrics,
    }


def evaluate_water(source: str) -> dict:
    cfg = CFG.water
    weights = CFG.weights_dir / cfg.water_output_name
    data_yaml = CFG.prepared_root / f"water_yolo_{source}" / "dataset.yaml"

    yolo_metrics = evaluate_yolo(weights, data_yaml, f"water_{source}")
    cf_metrics = evaluate_changeformer(
        CFG.weights_dir / cfg.water_change_output_name, f"water_{source}"
    )

    return {
        "sector": "water",
        "source": source,
        "version": "v1.0",
        "yolo": yolo_metrics,
        "changeformer": cf_metrics,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Evaluate trained models")
    p.add_argument("sector", choices=["forestry", "water"])
    p.add_argument(
        "--source",
        choices=["s1s2_water", "glh_water", "atlantis"],
        default="s1s2_water",
    )
    p.add_argument("--output", type=Path, help="Output JSON path")
    args = p.parse_args()

    metrics = (
        evaluate_forestry() if args.sector == "forestry" else evaluate_water(args.source)
    )

    out_path = args.output or (
        CFG.eval_dir / f"eval_{args.sector}_{metrics.get('version', 'v1.0')}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Evaluation saved to {out_path}")