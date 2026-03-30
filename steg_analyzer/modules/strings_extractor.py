"""
Steg Analyzer – Printable string extractor.
Finds human-readable strings and CTF flag patterns in raw image bytes.
"""

from __future__ import annotations
from ..analyzer import StegAnalyzer
from ..utils import extract_printable_strings, find_flag_patterns


def run(analyzer: StegAnalyzer, min_len: int = 8) -> dict:
    data = analyzer.raw_bytes
    strings = extract_printable_strings(data, min_len=min_len)
    flags = find_flag_patterns(data)

    results: dict = {
        "total_strings": len(strings),
        "strings": strings[:100],  # cap at 100 for display
    }
    if flags:
        results["flags"] = flags

    return results
