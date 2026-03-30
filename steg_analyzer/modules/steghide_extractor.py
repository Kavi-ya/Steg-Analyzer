"""
Steg Analyzer – Steghide extraction wrapper.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..analyzer import StegAnalyzer
from ..utils import print_result, print_warning


def extract(
    analyzer: StegAnalyzer,
    password: str = "",
    output_path: Path = Path("extracted.bin"),
) -> bytes | None:
    try:
        result = subprocess.run(
            [
                "steghide", "extract",
                "-sf", str(analyzer.path),
                "-p", password,
                "-xf", str(output_path),
                "-f",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print_warning("steghide not found. Install: apt install steghide")
        return None
    except subprocess.TimeoutExpired:
        print_warning("steghide timed out.")
        return None

    if result.returncode == 0 and output_path.exists():
        data = output_path.read_bytes()
        print_result("Steghide status", "Success")
        print_result("Extracted bytes", str(len(data)))
        return data

    print_warning(f"Steghide: {result.stderr.strip()}")
    return None
