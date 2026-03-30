"""
Steg Analyzer – LSB steganography analysis module.
Checks all channel / bit-plane / bit-order combinations for hidden data.
"""

from __future__ import annotations

import numpy as np

from ..analyzer import StegAnalyzer
from ..utils import detect_file_type, extract_printable_strings, find_flag_patterns

CHANNEL_COMBOS = [
    (["r"], "R"),
    (["g"], "G"),
    (["b"], "B"),
    (["a"], "A"),
    (["r", "g", "b"], "RGB"),
    (["r", "g"], "RG"),
    (["g", "b"], "GB"),
    (["r", "b"], "RB"),
    (["r", "g", "b", "a"], "RGBA"),
]

CHANNEL_ORDERS_ALL = [
    (["r", "g", "b"], "rgb"),
    (["r", "b", "g"], "rbg"),
    (["g", "r", "b"], "grb"),
    (["g", "b", "r"], "gbr"),
    (["b", "r", "g"], "brg"),
    (["b", "g", "r"], "bgr"),
]


def run(analyzer: StegAnalyzer) -> dict:
    results: dict = {
        "lsb_even_ratio": {},
        "suspicious_combos": [],
        "flags": [],
        "strings": [],
        "embedded_files": [],
    }

    arr = analyzer.arr_rgba
    h, w = arr.shape[:2]
    n = h * w

    # ── 1. Basic LSB distribution (chi-square proxy) ─────────────────────────
    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        channel = arr[:, :, ch_idx].flatten()
        even_ratio = float(np.sum(channel % 2 == 0)) / n
        results["lsb_even_ratio"][ch_name] = f"{even_ratio:.4f}"

    # ── 2. Brute-force all combos ─────────────────────────────────────────────
    for bit in range(4):  # bits 0-3 (LSB to bit-3)
        for channels, label in CHANNEL_COMBOS:
            try:
                data = analyzer.extract_lsb_bits(channels, bit_position=bit)
            except Exception:
                continue

            _check_data(data, f"bit{bit}_{label}", results)

    # ── 3. All 6 channel orderings for bit-0 ─────────────────────────────────
    for channels, label in CHANNEL_ORDERS_ALL:
        try:
            data = analyzer.extract_lsb_bits(channels, bit_position=0)
        except Exception:
            continue
        _check_data(data, f"order_{label}", results)

    # ── 4. Column-major scan ─────────────────────────────────────────────────
    for ch_idx, ch_name in enumerate(("r", "g", "b")):
        plane = (arr[:, :, ch_idx].T >> 0) & 1  # transpose = column-major
        flat = plane.flatten()
        pad = (8 - len(flat) % 8) % 8
        if pad:
            flat = np.pad(flat, (0, pad))
        data = np.packbits(flat).tobytes()
        _check_data(data, f"col_major_{ch_name}", results)

    # Clean up empty lists
    for key in ("flags", "strings", "embedded_files", "suspicious_combos"):
        if not results[key]:
            del results[key]

    return results


def _check_data(data: bytes, label: str, results: dict):
    # Flag patterns
    flags = find_flag_patterns(data[:500_000])
    for f in flags:
        if f not in results["flags"]:
            results["flags"].append(f)
            results["suspicious_combos"].append(f"FLAG in {label}")

    # Known file type
    ft = detect_file_type(data)
    if ft:
        results["embedded_files"].append(f"{label}: {ft}")
        results["suspicious_combos"].append(f"File header ({ft}) in {label}")

    # Long printable strings
    strings = extract_printable_strings(data[:200_000], min_len=12)
    for s in strings:
        if s not in results["strings"]:
            results["strings"].append(s)
