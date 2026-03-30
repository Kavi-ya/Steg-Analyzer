"""
Steg Analyzer - Utility helpers and terminal output.
"""

import re
import sys

# ── ANSI colour helpers ───────────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_WHITE = "\033[97m"
_MAGENTA = "\033[95m"


def _c(text: str, *codes: str) -> str:
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + _RESET


def print_banner():
    banner = r"""
  ____  _             __  __
 / ___|| |_ ___  __ _\ \/ /
 \___ \| __/ _ \/ _` |\  /
  ___) | ||  __/ (_| |/  \
 |____/ \__\___|\__, /_/\_\
                |___/
    """
    tag = "All-in-One Steganography Analysis Tool"
    from steg_analyzer import __version__

    print(_c(banner.rstrip(), _CYAN, _BOLD))
    print(_c(f"  {tag}   v{__version__}", _DIM))
    print(_c("  github.com/your-org/steg-analyzer", _DIM))
    print()


def print_success(msg: str):
    print(_c(f"  [✓] {msg}", _GREEN, _BOLD))


def print_error(msg: str):
    print(_c(f"  [✗] {msg}", _RED, _BOLD), file=sys.stderr)


def print_info(msg: str):
    print(_c(f"  [*] {msg}", _CYAN))


def print_warning(msg: str):
    print(_c(f"  [!] {msg}", _YELLOW))


def print_result(key: str, value: str):
    k = _c(f"  {key:<28}", _WHITE, _BOLD)
    v = _c(value, _YELLOW)
    print(f"{k} {v}")


def print_section(title: str):
    line = "─" * 52
    print()
    print(_c(f"  ┌─ {title} {line[:max(0, 48-len(title))]}", _CYAN, _BOLD))


def print_found(label: str, value: str):
    print(_c(f"  ★  {label}: {value}", _GREEN, _BOLD))


# ── byte / file helpers ───────────────────────────────────────────────────────

FILE_SIGNATURES: dict[bytes, str] = {
    b"\xff\xd8\xff": "JPEG image",
    b"\x89PNG\r\n": "PNG image",
    b"GIF8": "GIF image",
    b"BM": "BMP image",
    b"PK\x03\x04": "ZIP archive",
    b"PK\x05\x06": "ZIP archive (empty)",
    b"\x1f\x8b": "GZIP archive",
    b"Rar!": "RAR archive",
    b"7z\xbc\xaf": "7-Zip archive",
    b"\x00\x00\x00\x18ftypmp4": "MP4 video",
    b"%PDF": "PDF document",
    b"ID3": "MP3 audio",
    b"OggS": "OGG audio",
    b"fLaC": "FLAC audio",
    b"RIFF": "RIFF (WAV/AVI)",
    b"MZ": "Windows PE executable",
    b"\x7fELF": "ELF executable",
}


def detect_file_type(data: bytes) -> str | None:
    for sig, name in FILE_SIGNATURES.items():
        if data[: len(sig)] == sig:
            return name
    return None


def find_flag_patterns(data: bytes) -> list[str]:
    """Search bytes for common CTF flag formats."""
    patterns = [
        rb"[A-Za-z0-9_]{2,20}\{[A-Za-z0-9_\-!@#$%^&*+=:;.,?/ ]{3,120}\}",
        rb"flag\{[^\}]{3,120}\}",
        rb"FLAG\{[^\}]{3,120}\}",
        rb"ctf\{[^\}]{3,120}\}",
        rb"CTF\{[^\}]{3,120}\}",
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, data, re.IGNORECASE):
            try:
                found.add(m.group(0).decode("utf-8", errors="replace"))
            except Exception:
                pass
    return list(found)


def extract_printable_strings(data: bytes, min_len: int = 8) -> list[str]:
    """Return printable ASCII strings of at least min_len characters."""
    pattern = re.compile(rb"[ -~]{" + str(min_len).encode() + rb",}")
    results = []
    for m in pattern.finditer(data):
        try:
            results.append(m.group(0).decode("ascii"))
        except Exception:
            pass
    return results


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
