"""
Steg Analyzer – Bit-plane image generator.
Saves one PNG per bit per channel (24 images total for RGB).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ..analyzer import StegAnalyzer


def run(analyzer: StegAnalyzer, output_dir: Path) -> dict:
    bp_dir = output_dir / "bitplanes"
    bp_dir.mkdir(parents=True, exist_ok=True)

    arr = analyzer.arr_rgb
    saved: list[str] = []

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        channel = arr[:, :, ch_idx]
        for bit in range(8):
            plane = ((channel >> bit) & 1) * 255
            img = Image.fromarray(plane.astype(np.uint8), "L")
            fname = f"{ch_name}_bit{bit}.png"
            img.save(bp_dir / fname)
            saved.append(fname)

    return {
        "bitplane_images_saved": len(saved),
        "output_directory": str(bp_dir),
        "files": saved,
    }
