"""
Steg Analyzer – Visual analysis image generator.
Produces: bit-planes, channel separations, ELA, FFT spectrum, channel diffs.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image

from ..analyzer import StegAnalyzer
from ..utils import print_result


def run(
    analyzer: StegAnalyzer,
    output_dir: Path,
    bitplanes: bool = False,
    channels: bool = False,
    ela: bool = False,
    fft: bool = False,
    diff: bool = False,
):
    arr = analyzer.arr_rgb
    h, w = arr.shape[:2]
    saved: list[str] = []

    # ── Bit planes ────────────────────────────────────────────────────────────
    if bitplanes:
        bp_dir = output_dir / "bitplanes"
        bp_dir.mkdir(exist_ok=True)
        for ci, ch_name in enumerate(("R", "G", "B")):
            for bit in range(8):
                plane = ((arr[:, :, ci] >> bit) & 1) * 255
                img = Image.fromarray(plane.astype(np.uint8), "L")
                path = bp_dir / f"{ch_name}_bit{bit}.png"
                img.save(path)
                saved.append(str(path))
        print_result("Bit-plane images", "24 saved")

    # ── Channel separation ────────────────────────────────────────────────────
    if channels:
        ch_dir = output_dir / "channels"
        ch_dir.mkdir(exist_ok=True)
        for ci, ch_name in enumerate(("R", "G", "B")):
            ch_img = np.zeros_like(arr)
            ch_img[:, :, ci] = arr[:, :, ci]
            path = ch_dir / f"channel_{ch_name}.png"
            Image.fromarray(ch_img).save(path)
            saved.append(str(path))

        # Grayscale per channel
        for ci, ch_name in enumerate(("R", "G", "B")):
            path = ch_dir / f"gray_{ch_name}.png"
            Image.fromarray(arr[:, :, ci], "L").save(path)
            saved.append(str(path))
        print_result("Channel images", "6 saved")

    # ── ELA ───────────────────────────────────────────────────────────────────
    if ela:
        img_rgb = Image.fromarray(arr)
        buf = io.BytesIO()
        img_rgb.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        recomp = np.array(Image.open(buf).convert("RGB"), dtype=np.float32)
        diff_arr = np.abs(arr.astype(np.float32) - recomp)
        amplified = np.clip(diff_arr * 15, 0, 255).astype(np.uint8)
        path = output_dir / "ela.png"
        Image.fromarray(amplified).save(path)
        saved.append(str(path))
        print_result("ELA image", str(path))

    # ── FFT spectrum ──────────────────────────────────────────────────────────
    if fft:
        gray = np.array(Image.fromarray(arr).convert("L"), dtype=np.float64)
        fft2 = np.fft.fftshift(np.fft.fft2(gray))
        magnitude = 20 * np.log10(np.abs(fft2) + 1)
        mag_norm = (
            (magnitude - magnitude.min()) / (magnitude.max() - magnitude.min()) * 255
        ).astype(np.uint8)
        path = output_dir / "fft_spectrum.png"
        Image.fromarray(mag_norm, "L").save(path)
        saved.append(str(path))
        print_result("FFT spectrum", str(path))

    # ── Channel differences ───────────────────────────────────────────────────
    if diff:
        diff_dir = output_dir / "diffs"
        diff_dir.mkdir(exist_ok=True)
        r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)

        for c1, c2, name in [(r, g, "R-G"), (g, b, "G-B"), (r, b, "R-B")]:
            amp = np.clip(np.abs(c1 - c2) * 5, 0, 255).astype(np.uint8)
            path = diff_dir / f"diff_{name.replace('-','_')}.png"
            Image.fromarray(amp, "L").save(path)
            saved.append(str(path))

        # XOR channels
        for c1, c2, name in [
            (arr[:, :, 0], arr[:, :, 1], "R_XOR_G"),
            (arr[:, :, 1], arr[:, :, 2], "G_XOR_B"),
        ]:
            xor = c1.astype(np.uint8) ^ c2.astype(np.uint8)
            path = diff_dir / f"{name}.png"
            Image.fromarray(xor, "L").save(path)
            saved.append(str(path))

        print_result("Diff images", f"{len(saved)} saved")

    print_result("Total visual outputs", str(len(saved)))
