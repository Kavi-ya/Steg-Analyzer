"""
Steg Analyzer – File structure analysis.
Searches for appended data, embedded file signatures, and unusual markers.
"""

from __future__ import annotations

import re

from ..analyzer import StegAnalyzer
from ..utils import FILE_SIGNATURES, detect_file_type, find_flag_patterns


def run(analyzer: StegAnalyzer) -> dict:
    data = analyzer.raw_bytes
    results: dict = {}

    # ── Appended data after EOF marker ────────────────────────────────────────
    if analyzer.is_jpeg:
        jpeg_end = data.rfind(b"\xff\xd9")
        if jpeg_end != -1 and jpeg_end < len(data) - 2:
            appended = data[jpeg_end + 2:]
            results["appended_bytes"] = len(appended)
            results["appended_hex_preview"] = appended[:64].hex()
            ft = detect_file_type(appended)
            if ft:
                results["appended_file_type"] = ft
            flags = find_flag_patterns(appended)
            if flags:
                results["flags"] = flags
        else:
            results["appended_bytes"] = 0

    # ── Embedded file signatures ──────────────────────────────────────────────
    embedded: list[str] = []
    for sig, name in FILE_SIGNATURES.items():
        # Skip the first occurrence (the file itself)
        idx = data.find(sig, len(sig))
        while idx != -1:
            embedded.append(f"{name} at offset {idx} (0x{idx:x})")
            idx = data.find(sig, idx + 1)
    if embedded:
        results["embedded_signatures"] = embedded

    # ── Null byte runs (padding / structure) ──────────────────────────────────
    null_count = data.count(b"\x00")
    results["null_bytes"] = null_count
    results["null_ratio"] = f"{null_count / len(data):.3f}"

    # ── Base64 encoded blobs ──────────────────────────────────────────────────
    b64_pattern = re.compile(rb"[A-Za-z0-9+/]{40,}={0,2}")
    b64_matches = b64_pattern.findall(data)
    if b64_matches:
        import base64
        decoded_files: list[str] = []
        for m in b64_matches[:20]:
            try:
                decoded = base64.b64decode(m)
                ft = detect_file_type(decoded)
                if ft:
                    decoded_files.append(ft)
                flags = find_flag_patterns(decoded)
                if flags:
                    results.setdefault("flags", []).extend(flags)
            except Exception:
                pass
        if decoded_files:
            results["base64_embedded"] = decoded_files

    # ── Flag scan in raw bytes ────────────────────────────────────────────────
    if "flags" not in results:
        flags = find_flag_patterns(data)
        if flags:
            results["flags"] = flags

    return results
