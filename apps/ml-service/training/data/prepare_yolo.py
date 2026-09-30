#!/usr/bin/env python3
"""Prepare YOLO-format datasets from raw downloads.

Forestry: ForestNet → YOLO layout (nc=1, names=['sapling'])
Water:    S1S2-Water / GLH-Water / ATLANTIS → YOLO layout (nc=1, names=['water'])

Run:
  python -m training.data.prepare_yolo forestry
  python -m training.data.prepare_yolo water --source s1s2_water|glh_water|atlantis
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import yaml
from training.config import CFG


def _split_indices(
    n: int, train_ratio: float = 0.8, val_ratio: float = 0.1
) -> tuple[list, list, list]:
    """Deterministic split indices."""
    np.random.seed(CFG.seed)
    idx = np.random.permutation(n)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    return (
        idx[:n_train].tolist(),
        idx[n_train:n_train + n_val].tolist(),
        idx[n_train + n_val:].tolist(),
    )


def _write_yaml(out_dir: Path, names: list[str]) -> None:
    data = {
        "path": str(out_dir),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(names),
        "names": {i: n for i, n in enumerate(names)},
    }
    with (out_dir / "dataset.yaml").open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f"  Wrote {out_dir / 'dataset.yaml'}")


def prepare_forestry() -> None:
    """ForestNet (GEO-Bench) → YOLO (single class: sapling).

    Expected GEO-Bench structure after extraction:
      data/raw/forestnet/
        data.zip contents extracted to:
          images/  (Landsat 8 composites)
          labels/  (driver labels, but we need sapling detection)

    NOTE: ForestNet is a deforestation driver classification dataset,
    not a sapling detection dataset. For actual sapling detection,
    you would need a different dataset (e.g., custom annotated data).
    This function creates a YOLO structure placeholder.
    """
    raw = CFG.data_root / "forestnet"
    if not raw.exists():
        raise FileNotFoundError(f"ForestNet not found at {raw}. Run download_forestnet first.")

    out = CFG.prepared_root / "forestry_yolo"
    if out.exists():
        shutil.rmtree(out)
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True)
        (out / "labels" / split).mkdir(parents=True)

    # TODO: Implement actual ForestNet → YOLO conversion
    # For now, create empty dataset.yaml as placeholder
    print("ForestNet preparation: placeholder — implement actual conversion")
    print(f"  Expected raw: {raw}")
    print(f"  Output: {out}")

    _write_yaml(out, ["sapling"])


def prepare_water(source: str) -> None:
    """Water dataset → YOLO (single class: water)."""
    raw_map = {
        "s1s2_water": CFG.data_root / "s1s2_water",
        "glh_water": CFG.data_root / "glh_water",
        "atlantis": CFG.data_root / "atlantis",
    }
    if source not in raw_map:
        raise ValueError(f"Unknown water source: {source}. Choose from {list(raw_map.keys())}")

    raw = raw_map[source]
    if not raw.exists():
        raise FileNotFoundError(f"Water source '{source}' not found at {raw}. Run download first.")

    out = CFG.prepared_root / f"water_yolo_{source}"
    if out.exists():
        shutil.rmtree(out)
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True)
        (out / "labels" / split).mkdir(parents=True)

    print(f"Water ({source}) preparation: placeholder — implement actual conversion")
    print(f"  Expected raw: {raw}")
    print(f"  Output: {out}")

    _write_yaml(out, ["water"])


def prepare_levir_cd() -> None:
    """LEVIR-CD → Change detection format (before/after pairs + masks).

    Expected structure after download:
      data/raw/LEVIR-CD/
        train/A/  (before images)
        train/B/  (after images)
        train/label/  (change masks)
        val/A/, val/B/, val/label/
        test/A/, test/B/, test/label/

    This prepares the data for ChangeFormer training which expects
    (before, after, mask) triplets.
    """
    raw = CFG.data_root / "LEVIR-CD"
    if not raw.exists():
        raise FileNotFoundError(f"LEVIR-CD not found at {raw}. Run download_levir_cd first.")

    out = CFG.prepared_root / "levir_cd"
    if out.exists():
        shutil.rmtree(out)

    # Create structure for ChangeFormer training
    for split in ("train", "val", "test"):
        (out / split / "A").mkdir(parents=True)
        (out / split / "B").mkdir(parents=True)
        (out / split / "label").mkdir(parents=True)

    # Copy/link files to prepared structure
    import os
    for split in ("train", "val", "test"):
        split_raw = raw / split
        split_out = out / split
        if not split_raw.exists():
            print(f"  Warning: {split_raw} not found, skipping")
            continue
        for subdir in ("A", "B", "label"):
            src = split_raw / subdir
            dst = split_out / subdir
            if src.exists():
                for f in src.iterdir():
                    if f.suffix in (".png", ".jpg", ".tif", ".tiff"):
                        dst_f = dst / f.name
                        if not dst_f.exists():
                            os.link(f, dst_f)  # Hard link to save space
    print(f"LEVIR-CD preparation complete: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Prepare YOLO / Change Detection datasets")
    p.add_argument("sector", choices=["forestry", "water", "levir_cd"])
    p.add_argument(
        "--source",
        choices=["s1s2_water", "glh_water", "atlantis"],
        default="s1s2_water",
    )
    args = p.parse_args()

    if args.sector == "forestry":
        prepare_forestry()
    elif args.sector == "water":
        prepare_water(args.source)
    elif args.sector == "levir_cd":
        prepare_levir_cd()
    else:
        raise ValueError(f"Unknown sector: {args.sector}")