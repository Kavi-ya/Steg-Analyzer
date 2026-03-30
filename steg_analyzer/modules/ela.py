"""
Steg Analyzer – Error Level Analysis (ELA) module.
Highlights regions of the image that differ from a re-compressed version,
indicating possible manipulation or hidden data insertion.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image

from ..analyzer import StegAnalyzer


def run(analyzer: StegAnalyzer, output_dir: Path, quality: int = 95) -> dict:
    results: dict = {"ela_quality": quality}

    img = analyzer.pil_image.convert("RGB")

    # Re-save at known quality into memory
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    original_arr = np.array(img, dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)

    diff = np.abs(original_arr - recomp_arr)

    results["max_diff"] = float(diff.max())
    results["mean_diff"] = float(diff.mean())

    # Amplified ELA image (×15 for visibility)
    amplified = np.clip(diff * 15, 0, 255).astype(np.uint8)
    ela_img = Image.fromarray(amplified)

    ela_path = output_dir / "ela.png"
    ela_img.save(ela_path)
    results["ela_image"] = str(ela_path)

    # Find top suspicious 50×50 blocks
    gray_diff = diff.mean(axis=2)
    block_size = 50
    h, w = gray_diff.shape
    suspicious: list[tuple[float, int, int]] = []

    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block_mean = float(gray_diff[y : y + block_size, x : x + block_size].mean())
            suspicious.append((block_mean, x, y))

    suspicious.sort(reverse=True)
    top = suspicious[:5]
    results["top_suspicious_regions"] = [f"({x},{y}) score={s:.2f}" for s, x, y in top]

    # Heuristic verdict
    if results["max_diff"] < 5:
        results["verdict"] = "No obvious manipulation detected"
    elif results["max_diff"] < 15:
        results["verdict"] = "Minor differences — possible light editing"
    else:
        results["verdict"] = "Significant differences — possible hidden content or editing"

    return results
