"""
Steg Analyzer – Metadata / EXIF extraction module.
"""

from __future__ import annotations

from ..analyzer import StegAnalyzer
from ..utils import find_flag_patterns, human_size


def run(analyzer: StegAnalyzer) -> dict:
    results: dict = {}

    # Basic file info
    results["file_name"] = analyzer.path.name
    results["file_size"] = human_size(analyzer.file_size)
    results["dimensions"] = f"{analyzer.width} × {analyzer.height}"
    results["color_mode"] = analyzer.mode
    results["format"] = analyzer.pil_image.format or "Unknown"

    # PIL image info dict
    info = analyzer.pil_image.info or {}
    if "dpi" in info:
        results["dpi"] = str(info["dpi"])
    if "comment" in info:
        results["comment"] = str(info["comment"])
        flags = find_flag_patterns(str(info["comment"]).encode())
        if flags:
            results["flags"] = flags

    # EXIF via Pillow
    try:
        from PIL.ExifTags import TAGS
        exif_raw = analyzer.pil_image._getexif()  # type: ignore[attr-defined]
        if exif_raw:
            exif: dict[str, str] = {}
            for tag_id, value in exif_raw.items():
                tag = TAGS.get(tag_id, str(tag_id))
                exif[tag] = str(value)[:200]
            results["exif"] = exif

            # Scan all EXIF values for flags
            all_exif_text = " ".join(exif.values()).encode()
            flags = find_flag_patterns(all_exif_text)
            if flags:
                results["flags"] = flags
    except Exception:
        pass

    # Try exiftool if installed
    try:
        import subprocess
        r = subprocess.run(
            ["exiftool", "-j", str(analyzer.path)],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            import json
            exif_data = json.loads(r.stdout)[0]
            # Filter out boring keys
            skip = {"ExifToolVersion", "FileName", "Directory", "FileSize",
                    "FileModifyDate", "FileAccessDate", "FileInodeChangeDate",
                    "FilePermissions"}
            for k, v in exif_data.items():
                if k not in skip:
                    results[f"exiftool_{k}"] = str(v)[:200]
            # Scan for flags
            flags = find_flag_patterns(r.stdout.encode())
            if flags and "flags" not in results:
                results["flags"] = flags
    except (FileNotFoundError, Exception):
        pass

    # JPEG-specific: scan APP markers
    if analyzer.is_jpeg:
        results.update(_scan_jpeg_markers(analyzer.raw_bytes))

    # Flags in raw bytes
    if "flags" not in results:
        flags = find_flag_patterns(analyzer.raw_bytes)
        if flags:
            results["flags"] = flags

    return results


def _scan_jpeg_markers(data: bytes) -> dict:
    extra: dict = {}
    i = 0
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0xD9):
            i += 2
            continue
        if marker >= 0xD0 and marker <= 0xD7:
            i += 2
            continue
        if i + 3 >= len(data):
            break
        length = (data[i + 2] << 8) | data[i + 3]
        segment_data = data[i + 4: i + 2 + length]

        if marker == 0xFE:  # COM – JPEG comment
            try:
                extra["jpeg_comment"] = segment_data.decode("utf-8", errors="replace")
            except Exception:
                pass

        if 0xE1 <= marker <= 0xEF and marker != 0xE0:
            name = segment_data[:12].decode("latin-1", errors="replace").rstrip("\x00")
            extra[f"APP{marker - 0xE0}_identifier"] = name

        flags = find_flag_patterns(segment_data)
        if flags:
            extra.setdefault("flags", []).extend(flags)

        i += 2 + length

    return extra
