#!/usr/bin/env python3
"""Albumentations pipelines for field-condition augmentation.

Both forestry and water use the same base augmentations; sector-specific
tweaks are in the config.
"""

from __future__ import annotations

import albumentations as A
import cv2
from albumentations.pytorch import ToTensorV2


def get_train_augs(imgsz: int, sector: str) -> A.Compose:
    """Training augmentations with sector-specific probability weights."""
    common = [
        A.LongestMaxSize(max_size=imgsz, interpolation=cv2.INTER_LINEAR),
        A.PadIfNeeded(min_height=imgsz, min_width=imgsz, border_mode=cv2.BORDER_CONSTANT, value=0),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.3),
        A.GaussNoise(var_limit=(10, 50), p=0.2),
        A.MotionBlur(blur_limit=5, p=0.1),
        A.OneOf([
            A.ElasticTransform(alpha=1, sigma=50, p=0.5),
            A.GridDistortion(p=0.5),
            A.OpticalDistortion(distort_limit=0.05, p=0.5),
        ], p=0.2),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]

    if sector == "forestry":
        # Forestry: more green/vegetation shifts
        common.insert(-3, A.ChannelShuffle(p=0.05))
    elif sector == "water":
        # Water: blue/cyan shifts, stronger blur for water surface
        common.insert(-3, A.RandomGamma(gamma_limit=(80, 120), p=0.3))
        common.insert(-3, A.Blur(blur_limit=7, p=0.2))

    return A.Compose(common, bbox_params=A.BboxParams(format="yolo", label_fields=["class_labels"]))


def get_val_augs(imgsz: int) -> A.Compose:
    """Validation augmentations (resize + normalize only)."""
    return A.Compose([
        A.LongestMaxSize(max_size=imgsz, interpolation=cv2.INTER_LINEAR),
        A.PadIfNeeded(min_height=imgsz, min_width=imgsz, border_mode=cv2.BORDER_CONSTANT, value=0),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ], bbox_params=A.BboxParams(format="yolo", label_fields=["class_labels"]))


# Need cv2 for interpolation constants