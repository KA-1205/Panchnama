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
    """ForestNet → YOLO (single class: sapling)."""
    raw = CFG.data_root / "forestnet"
    if not raw.exists():
        raise FileNotFoundError(f"ForestNet not found at {raw}. Run download_forestnet first.")

    out = CFG.prepared_root / "forestry_yolo"
    if out.exists():
        shutil.rmtree(out)
    (out / "images" / "train").mkdir(parents=True)
    (out / "images" / "val").mkdir(parents=True)
    (out / "images" / "test").mkdir(parents=True)
    (out / "labels" / "train").mkdir(parents=True)
    (out / "labels" / "val").mkdir(parents=True)
    (out / "labels" / "test").mkdir(parents=True)

    # ForestNet structure: patches/ with images and masks
    # This is a placeholder — actual structure depends on ForestNet release
    print("ForestNet preparation: implement based on actual directory structure")
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

    print(f"Water ({source}) preparation: implement based on actual directory structure")
    print(f"  Expected raw: {raw}")
    print(f"  Output: {out}")

    _write_yaml(out, ["water"])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Prepare YOLO datasets")
    p.add_argument("sector", choices=["forestry", "water"])
    p.add_argument(
        "--source",
        choices=["s1s2_water", "glh_water", "atlantis"],
        default="s1s2_water",
    )
    args = p.parse_args()

    if args.sector == "forestry":
        prepare_forestry()
    else:
        prepare_water(args.source)