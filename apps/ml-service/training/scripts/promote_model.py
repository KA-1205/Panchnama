#!/usr/bin/env python3
"""Promote trained weights to model_registry — flips the row to real weights.

Run AFTER:
  1. Training complete (weights in weights/)
  2. Weights uploaded to private bucket (s3://bucket/weights/...)
  3. WEIGHTS_DIR populated in service container

Usage:
  python -m training.scripts.promote_model forestry --version v1.0
  python -m training.scripts.promote_model water --version v1.0 --source s1s2_water

Requires env vars (from ~/.config/impact-platform/env-secrets.local.txt):
  SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from training.config import CFG


def load_secrets() -> dict:
    """Load secrets from the standard location."""
    secrets_path = Path.home() / ".config" / "impact-platform" / "env-secrets.local.txt"
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets not found at {secrets_path}")

    secrets = {}
    for line in secrets_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
        elif ":" in line:
            k, v = line.split(":", 1)
        else:
            continue
        secrets[k.strip()] = v.strip().strip('"\'')
    return secrets


def get_supabase_client():
    """Create Supabase client with service role."""
    from supabase import create_client

    secrets = load_secrets()
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be in secrets file")
    return create_client(url, key)


def promote_forestry(version: str, eval_path: Path | None = None) -> None:
    """Update forestry model_registry row with real weights."""
    sb = get_supabase_client()
    cfg = CFG.forestry

    # Load eval metrics if provided
    metrics = {}
    if eval_path and eval_path.exists():
        metrics = json.loads(eval_path.read_text())
        print(f"Loaded eval metrics: {json.dumps(metrics, indent=2)}")

    # Verify weights exist locally
    weights_dir = CFG.weights_dir
    required = [
        weights_dir / cfg.sapling_output_name,
        weights_dir / cfg.change_output_name,
        weights_dir / "yolov8n.pt",  # COCO base
    ]
    for w in required:
        if not w.exists():
            raise FileNotFoundError(f"Required weight missing: {w}")

    # Construct weights_uri (private bucket path)
    weights_uri = f"s3://impact-weights/forestry/{version}/"

    print(f"Promoting forestry to version {version}")
    print(f"  weights_uri: {weights_uri}")
    print(f"  metrics: {json.dumps(metrics)}")

    # Update model_registry
    result = sb.table("model_registry").update({
        "version": version,
        "weights_uri": weights_uri,
        "status": "trained",
        "metrics": metrics,
    }).eq("key", "forestry").eq("version", "v1-placeholder").execute()

    if not result.data:
        raise RuntimeError("No row updated — check key/version match (must be v1-placeholder)")

    print(f"✓ Updated model_registry: {result.data}")


def promote_water(version: str, source: str, eval_path: Path | None = None) -> None:
    """Update water model_registry row with real weights."""
    sb = get_supabase_client()
    cfg = CFG.water

    metrics = {}
    if eval_path and eval_path.exists():
        metrics = json.loads(eval_path.read_text())
        print(f"Loaded eval metrics: {json.dumps(metrics, indent=2)}")

    weights_dir = CFG.weights_dir
    required = [
        weights_dir / cfg.water_output_name,
        weights_dir / cfg.water_change_output_name,
        weights_dir / "yolov8n.pt",
    ]
    for w in required:
        if not w.exists():
            raise FileNotFoundError(f"Required weight missing: {w}")

    weights_uri = f"s3://impact-weights/water/{version}/{source}/"

    print(f"Promoting water ({source}) to version {version}")
    print(f"  weights_uri: {weights_uri}")
    print(f"  metrics: {json.dumps(metrics)}")

    # Water row currently has version 'v0' and status 'unsupported'
    # We insert a NEW row with the trained version (never mutate old)
    result = sb.table("model_registry").insert({
        "key": "water",
        "version": version,
        "sector": "water",
        "weights_uri": weights_uri,
        "status": "trained",
        "metrics": metrics,
    }).execute()

    if not result.data:
        raise RuntimeError("Insert failed")

    print(f"✓ Inserted new model_registry row: {result.data}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Promote trained weights to model_registry")
    p.add_argument("sector", choices=["forestry", "water"])
    p.add_argument("--version", required=True, help="New version string (e.g., v1.0)")
    p.add_argument("--source", choices=["s1s2_water", "glh_water", "atlantis"], default="s1s2_water")
    p.add_argument("--eval", type=Path, help="Path to evaluation JSON")
    args = p.parse_args()

    try:
        if args.sector == "forestry":
            promote_forestry(args.version, args.eval)
        else:
            promote_water(args.version, args.source, args.eval)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)