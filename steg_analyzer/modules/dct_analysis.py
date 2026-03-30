"""
Steg Analyzer – DCT coefficient analysis for JPEG steganography detection.
Checks for JSteg-style embedding in DCT AC coefficient LSBs.
"""

from __future__ import annotations

import numpy as np

from ..analyzer import StegAnalyzer
from ..utils import detect_file_type, extract_printable_strings, find_flag_patterns


def run(analyzer: StegAnalyzer) -> dict:
    results: dict = {}

    try:
        import jpegio as jio  # type: ignore[import]
    except ImportError:
        results["error"] = "jpegio not installed. Run: pip install jpegio"
        return results

    try:
        struct = jio.read(str(analyzer.path))
    except Exception as e:
        results["error"] = str(e)
        return results

    coef_info = []
    all_jsteg_bits: list[int] = []

    for idx, coef_array in enumerate(struct.coef_arrays):
        flat = coef_array.flatten()
        nonzero = int(np.count_nonzero(flat))
        coef_info.append(f"array[{idx}] shape={coef_array.shape} nonzero={nonzero}")

        # JSteg: embed in LSB of non-zero, non-one AC coefficients
        for v in flat:
            vi = int(v)
            if vi != 0 and vi != 1:
                all_jsteg_bits.append(vi & 1)

    results["dct_arrays"] = coef_info

    # Quantization tables
    qt_info = []
    for i, qt in enumerate(struct.quant_tables):
        qt_info.append(f"table[{i}]: min={qt.min()} max={qt.max()} mean={qt.mean():.1f}")
    results["quant_tables"] = qt_info

    results["total_jsteg_bits"] = len(all_jsteg_bits)

    if all_jsteg_bits:
        # Pack into bytes
        bits = all_jsteg_bits
        pad = (8 - len(bits) % 8) % 8
        bits_arr = np.array(bits + [0] * pad, dtype=np.uint8)
        data = np.packbits(bits_arr).tobytes()

        flags = find_flag_patterns(data[:200_000])
        if flags:
            results["flags"] = flags

        ft = detect_file_type(data)
        if ft:
            results["jsteg_embedded_file"] = ft

        strings = extract_printable_strings(data[:200_000], min_len=10)
        if strings:
            results["jsteg_strings"] = strings[:20]

        # Even/odd distribution of non-zero DCT coefficients
        arr = np.array(all_jsteg_bits)
        results["dct_lsb_even_ratio"] = f"{float((arr == 0).sum()) / len(arr):.4f}"

    return results
