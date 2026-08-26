#!/usr/bin/env python3
"""Compatibility entry point for the code-anchor profile."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_translate.cli import main


if __name__ == "__main__":
    main()
