"""
Steg Analyzer – DCT (JSteg) data extractor.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..analyzer import StegAnalyzer
from ..utils import detect_file_type, print_result, print_warning


def extract(analyzer: StegAnalyzer, output_path: Path = Path("extracted_dct.bin")) -> bytes | None:
    if not analyzer.is_jpeg:
        print_warning("DCT extraction only works on JPEG files.")
        return None

    try:
        import jpegio as jio  # type: ignore[import]
    except ImportError:
        print_warning("jpegio not installed. Run: pip install jpegio")
        return None

    try:
        struct = jio.read(str(analyzer.path))
    except Exception as e:
        print_warning(f"Could not parse JPEG DCT: {e}")
        return None

    bits: list[int] = []
    for coef_array in struct.coef_arrays:
        for v in coef_array.flatten():
            vi = int(v)
            if vi != 0 and vi != 1:
                bits.append(vi & 1)

    pad = (8 - len(bits) % 8) % 8
    bits_arr = np.array(bits + [0] * pad, dtype=np.uint8)
    data = np.packbits(bits_arr).tobytes()

    print_result("JSteg bits extracted", str(len(bits)))
    print_result("Packed bytes", str(len(data)))

    ft = detect_file_type(data)
    if ft:
        print_result("Detected type", ft)

    output_path.write_bytes(data)
    return data
