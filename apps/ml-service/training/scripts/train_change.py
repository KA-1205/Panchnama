#!/usr/bin/env python3
"""Train ChangeFormer for forestry or water change detection.

Run:
  python -m training.scripts.train_change forestry
  python -m training.scripts.train_change water --source s1s2_water
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from training.config import CFG


# Minimal ChangeFormer implementation (adapt from your preferred repo)
# This is a skeleton — plug in your actual ChangeFormer architecture
class ChangeFormer(nn.Module):
    def __init__(self, in_channels: int = 3) -> None:
        super().__init__()
        # Placeholder: replace with actual ChangeFormer architecture
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels * 2, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 2, 1),  # binary change: no-change / change
        )

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x = torch.cat([x1, x2], dim=1)
        feat = self.encoder(x)
        return self.decoder(feat)


class ChangeDataset(torch.utils.data.Dataset):
    def __init__(self, root: Path, split: str, imgsz: int, sector: str):
        self.root = root
        self.split = split
        self.imgsz = imgsz
        self.sector = sector
        self.pairs = self._find_pairs()

    def _find_pairs(self) -> list[tuple[Path, Path, Path]]:
        """Return list of (before, after, mask) paths."""
        # Implement based on your dataset structure
        # LEVIR-CD: A/ before, B/ after, label/ mask
        # S1S2-Water: before/after + water mask
        # This is a placeholder
        return []

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        before_p, after_p, mask_p = self.pairs[idx]
        # Load and preprocess
        # Return tensors: before, after, mask
        pass


def train_forestry() -> Path:
    cfg = CFG.forestry
    device = torch.device(CFG.device)

    print("Training forestry ChangeFormer...")
    model = ChangeFormer().to(device)
    _ = torch.optim.AdamW(model.parameters(), lr=cfg.change_lr)

    # TODO: Create DataLoader from LEVIR-CD
    # train_ds = ChangeDataset(
    #     CFG.data_root / "LEVIR-CD", "train", cfg.change_imgsz, "forestry"
    # )
    # train_loader = DataLoader(
    #     train_ds, batch_size=cfg.change_batch, shuffle=True, num_workers=CFG.num_workers
    # )

    # Placeholder training loop
    for epoch in range(cfg.change_epochs):
        print(f"  Epoch {epoch + 1}/{cfg.change_epochs}")
        # for before, after, mask in train_loader:
        #     before, after, mask = before.to(device), after.to(device), mask.to(device)
        #     logits = model(before, after)
        #     loss = nn.CrossEntropyLoss()(logits, mask)
        #     optimizer.zero_grad()
        #     loss.backward()
        #     optimizer.step()

    out = CFG.weights_dir / cfg.change_output_name
    torch.save(model.state_dict(), out)
    print(f"Saved ChangeFormer weights to {out}")
    return out


def train_water(source: str) -> Path:
    cfg = CFG.water
    device = torch.device(CFG.device)

    print(f"Training water ChangeFormer ({source})...")
    model = ChangeFormer().to(device)
    _ = torch.optim.AdamW(model.parameters(), lr=cfg.water_change_lr)

    # TODO: Create DataLoader from water dataset
    # train_ds = ChangeDataset(
    #     CFG.data_root / source, "train", cfg.water_change_imgsz, "water"
    # )
    # train_loader = DataLoader(
    #     train_ds, batch_size=cfg.water_change_batch, shuffle=True, num_workers=CFG.num_workers
    # )

    for epoch in range(cfg.water_change_epochs):
        print(f"  Epoch {epoch + 1}/{cfg.water_change_epochs}")

    out = CFG.weights_dir / cfg.water_change_output_name
    torch.save(model.state_dict(), out)
    print(f"Saved water ChangeFormer weights to {out}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Train ChangeFormer")
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