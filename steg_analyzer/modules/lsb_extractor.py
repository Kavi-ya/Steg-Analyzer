"""
Steg Analyzer – LSB data extractor.
"""

from __future__ import annotations

from pathlib import Path

from ..analyzer import StegAnalyzer
from ..utils import detect_file_type, print_result

CHANNEL_MAP = {
    "r": ["r"], "g": ["g"], "b": ["b"], "a": ["a"],
    "rgb": ["r", "g", "b"],
    "all": ["r", "g", "b", "a"],
}


def extract(
    analyzer: StegAnalyzer,
    channel: str = "rgb",
    bit: int = 0,
    output_path: Path = Path("extracted.bin"),
) -> bytes | None:
    channels = CHANNEL_MAP.get(channel.lower(), ["r", "g", "b"])
    data = analyzer.extract_lsb_bits(channels, bit_position=bit)

    print_result("Channels", str(channels))
    print_result("Bit position", str(bit))
    print_result("Extracted bytes", str(len(data)))

    ft = detect_file_type(data)
    if ft:
        print_result("Detected type", ft)

    output_path.write_bytes(data)
    return data
