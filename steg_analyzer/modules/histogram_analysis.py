"""
Steg Analyzer – Histogram & chi-square steganography detection module.
A chi-square value near 1.0 per pair suggests LSB embedding.
"""

from __future__ import annotations

import numpy as np

from ..analyzer import StegAnalyzer


def run(analyzer: StegAnalyzer) -> dict:
    arr = analyzer.arr_rgb
    results: dict = {}

    for ch_idx, ch_name in enumerate(("R", "G", "B")):
        channel = arr[:, :, ch_idx].flatten()
        chi2, pairs, even_ratio = _chi_square(channel)
        results[f"{ch_name}_chi2_per_pair"] = f"{chi2:.4f}"
        results[f"{ch_name}_lsb_even_ratio"] = f"{even_ratio:.4f}"

    results["chi2_interpretation"] = _interpret(results)

    # Pair analysis histogram
    overall_suspicious = 0
    for ch_name in ("R", "G", "B"):
        chi = float(results[f"{ch_name}_chi2_per_pair"])
        if chi < 5.0:
            overall_suspicious += 1
    results["suspicious_channels"] = overall_suspicious
    results["verdict"] = (
        "HIGH chance of LSB embedding"
        if overall_suspicious >= 2
        else "Low indication of LSB embedding"
    )

    return results


def _chi_square(channel: np.ndarray) -> tuple[float, int, float]:
    """
    Classic pairs-of-values chi-square test.
    For each pair (2k, 2k+1) count observed vs expected (equal) occurrences.
    Returns (chi2_per_pair, n_pairs, even_ratio).
    """
    pairs: dict[int, list[int]] = {}
    for v in channel:
        k = int(v) // 2
        pairs.setdefault(k, [0, 0])
        pairs[k][int(v) % 2] += 1

    chi2 = 0.0
    n_pairs = 0
    for k, (ev, od) in pairs.items():
        total = ev + od
        if total > 0:
            expected = total / 2.0
            chi2 += ((ev - expected) ** 2 + (od - expected) ** 2) / expected
            n_pairs += 1

    chi2_per_pair = chi2 / n_pairs if n_pairs else 0.0
    n_total = len(channel)
    even_ratio = float(np.sum(channel % 2 == 0)) / n_total
    return chi2_per_pair, n_pairs, even_ratio


def _interpret(results: dict) -> str:
    chi_values = [float(results[f"{c}_chi2_per_pair"]) for c in ("R", "G", "B")]
    avg = sum(chi_values) / 3.0
    if avg < 5:
        return "Very low chi2 — strong indicator of LSB steganography"
    if avg < 20:
        return "Moderate chi2 — possible steganography"
    return "High chi2 — no obvious LSB embedding detected"
