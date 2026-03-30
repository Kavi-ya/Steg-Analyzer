"""
Steg Analyzer – Test suite.
Run with: pytest tests/ -v
"""

import io
import json
import sys
import numpy as np
import pytest
from pathlib import Path
from PIL import Image

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_png(width=64, height=64, mode="RGB") -> Path:
    """Create a solid-colour PNG in /tmp and return its path."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    path = Path("/tmp/steg_analyzer_test.png")
    img.save(path, "PNG")
    return path


def _make_jpeg(width=64, height=64) -> Path:
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    path = Path("/tmp/steg_analyzer_test.jpg")
    img.save(path, "JPEG", quality=85)
    return path


def _make_lsb_image(message: bytes, width=256, height=256) -> Path:
    """Embed a message in the LSB of a PNG (R channel, row-major)."""
    arr = np.random.randint(100, 200, (height, width, 3), dtype=np.uint8)
    bits = np.unpackbits(np.frombuffer(message, dtype=np.uint8))
    flat_r = arr[:, :, 0].flatten()
    flat_r[: len(bits)] = (flat_r[: len(bits)] & 0xFE) | bits
    arr[:, :, 0] = flat_r.reshape(height, width)
    img = Image.fromarray(arr, "RGB")
    path = Path("/tmp/steg_analyzer_lsb_test.png")
    img.save(path, "PNG")
    return path


# ── StegAnalyzer ──────────────────────────────────────────────────────────────


class TestStegAnalyzer:
    def test_load_png(self):
        from steg_analyzer.analyzer import StegAnalyzer

        path = _make_png()
        a = StegAnalyzer(path)
        assert a.width == 64
        assert a.height == 64
        assert a.arr_rgb.shape == (64, 64, 3)

    def test_load_jpeg(self):
        from steg_analyzer.analyzer import StegAnalyzer

        path = _make_jpeg()
        a = StegAnalyzer(path)
        assert a.is_jpeg
        assert a.width == 64

    def test_unsupported_extension(self):
        from steg_analyzer.analyzer import StegAnalyzer

        with pytest.raises(ValueError, match="Unsupported"):
            StegAnalyzer(Path("/tmp/fake.xyz"))

    def test_channel_extraction(self):
        from steg_analyzer.analyzer import StegAnalyzer

        path = _make_png()
        a = StegAnalyzer(path)
        assert a.channel("r").shape == (64, 64)
        assert a.channel("g").shape == (64, 64)

    def test_extract_lsb_bits(self):
        from steg_analyzer.analyzer import StegAnalyzer

        path = _make_png()
        a = StegAnalyzer(path)
        data = a.extract_lsb_bits(["r", "g", "b"], bit_position=0)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_file_size(self):
        from steg_analyzer.analyzer import StegAnalyzer

        path = _make_png()
        a = StegAnalyzer(path)
        assert a.file_size == path.stat().st_size


# ── utils ─────────────────────────────────────────────────────────────────────


class TestUtils:
    def test_detect_file_type_jpeg(self):
        from steg_analyzer.utils import detect_file_type

        assert detect_file_type(b"\xff\xd8\xff") == "JPEG image"

    def test_detect_file_type_png(self):
        from steg_analyzer.utils import detect_file_type

        assert detect_file_type(b"\x89PNG\r\n") == "PNG image"

    def test_detect_file_type_zip(self):
        from steg_analyzer.utils import detect_file_type

        assert detect_file_type(b"PK\x03\x04abc") == "ZIP archive"

    def test_detect_file_type_unknown(self):
        from steg_analyzer.utils import detect_file_type

        assert detect_file_type(b"\x00\x00\x00\x00") is None

    def test_find_flag_patterns(self):
        from steg_analyzer.utils import find_flag_patterns

        data = b"nothing here flag{s3cr3t_v4lu3} and more"
        flags = find_flag_patterns(data)
        assert any("flag{s3cr3t_v4lu3}" in f for f in flags)

    def test_find_flag_no_match(self):
        from steg_analyzer.utils import find_flag_patterns

        assert find_flag_patterns(b"no flags here") == []

    def test_extract_printable_strings(self):
        from steg_analyzer.utils import extract_printable_strings

        data = b"\x00\x00hello world\x00\x00another string\x00"
        strings = extract_printable_strings(data, min_len=5)
        assert "hello world" in strings
        assert "another string" in strings

    def test_human_size(self):
        from steg_analyzer.utils import human_size

        assert "B" in human_size(500)
        assert "KB" in human_size(2048)
        assert "MB" in human_size(2 * 1024 * 1024)


# ── metadata module ───────────────────────────────────────────────────────────


class TestMetadata:
    def test_basic_png(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import metadata

        path = _make_png()
        a = StegAnalyzer(path)
        result = metadata.run(a)
        assert result["file_name"] == "steg_analyzer_test.png"
        assert "×" in result["dimensions"]
        assert "file_size" in result

    def test_basic_jpeg(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import metadata

        path = _make_jpeg()
        a = StegAnalyzer(path)
        result = metadata.run(a)
        assert "JPEG" in result.get("format", "") or "file_name" in result


# ── LSB analysis ──────────────────────────────────────────────────────────────


class TestLSBAnalysis:
    def test_runs_clean_image(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import lsb_analysis

        path = _make_png()
        a = StegAnalyzer(path)
        result = lsb_analysis.run(a)
        assert "lsb_even_ratio" in result
        assert "R" in result["lsb_even_ratio"]

    def test_detects_flag_in_lsb(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import lsb_analysis

        message = b"flag{steg_analyzer_works_perfectly}"
        path = _make_lsb_image(message)
        a = StegAnalyzer(path)
        result = lsb_analysis.run(a)
        flags = result.get("flags", [])
        assert any(
            "flag{steg_analyzer_works_perfectly}" in f for f in flags
        ), f"Flag not found in LSB result. flags={flags}"


# ── ELA module ────────────────────────────────────────────────────────────────


class TestELA:
    def test_ela_creates_image(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import ela

        path = _make_jpeg()
        a = StegAnalyzer(path)
        result = ela.run(a, tmp_path)
        assert "ela_image" in result
        ela_path = Path(result["ela_image"])
        assert ela_path.exists()
        assert ela_path.stat().st_size > 0

    def test_ela_returns_stats(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import ela

        path = _make_jpeg()
        a = StegAnalyzer(path)
        result = ela.run(a, tmp_path)
        assert "max_diff" in result
        assert "mean_diff" in result
        assert "verdict" in result


# ── Histogram / chi-square ────────────────────────────────────────────────────


class TestHistogram:
    def test_returns_chi2(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import histogram_analysis

        path = _make_png()
        a = StegAnalyzer(path)
        result = histogram_analysis.run(a)
        assert "R_chi2_per_pair" in result
        assert "verdict" in result

    def test_chi2_values_are_floats(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import histogram_analysis

        path = _make_png()
        a = StegAnalyzer(path)
        result = histogram_analysis.run(a)
        for ch in ("R", "G", "B"):
            val = float(result[f"{ch}_chi2_per_pair"])
            assert val >= 0


# ── Structure analysis ────────────────────────────────────────────────────────


class TestStructure:
    def test_no_appended_data(self):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import structure_analysis

        path = _make_jpeg()
        a = StegAnalyzer(path)
        result = structure_analysis.run(a)
        assert result.get("appended_bytes", 0) == 0

    def test_detects_appended_zip(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import structure_analysis

        # Build a JPEG with a fake ZIP appended
        jpeg_path = _make_jpeg()
        jpeg_bytes = jpeg_path.read_bytes()
        fake_zip = b"PK\x03\x04" + b"\x00" * 20
        combined = jpeg_bytes + fake_zip
        test_path = tmp_path / "test_appended.jpg"
        test_path.write_bytes(combined)

        a = StegAnalyzer(test_path)
        result = structure_analysis.run(a)
        assert result.get("appended_bytes", 0) == len(fake_zip)
        assert "ZIP" in result.get("appended_file_type", "")

    def test_flag_in_raw_bytes(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import structure_analysis

        jpeg_bytes = _make_jpeg().read_bytes()
        flag_bytes = b"flag{hidden_in_appended_data}"
        test_path = tmp_path / "test_flag.jpg"
        test_path.write_bytes(jpeg_bytes + flag_bytes)

        a = StegAnalyzer(test_path)
        result = structure_analysis.run(a)
        assert any("flag{hidden_in_appended_data}" in f for f in result.get("flags", []))


# ── Bit planes ────────────────────────────────────────────────────────────────


class TestBitplanes:
    def test_creates_24_images(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import bitplane_analysis

        path = _make_png()
        a = StegAnalyzer(path)
        result = bitplane_analysis.run(a, tmp_path)
        assert result["bitplane_images_saved"] == 24
        bp_dir = tmp_path / "bitplanes"
        assert len(list(bp_dir.glob("*.png"))) == 24


# ── Reporter ──────────────────────────────────────────────────────────────────


class TestReporter:
    def test_json_report(self, tmp_path):
        from steg_analyzer.reporter import Reporter

        r = Reporter(tmp_path, fmt="json")
        results = {"metadata": {"file_name": "test.png", "flags": ["flag{test}"]}}
        r.render(results, Path("test.png"))
        report = json.loads((tmp_path / "report.json").read_text())
        assert report["tool"] == "Steg Analyzer"
        assert "metadata" in report["results"]

    def test_html_report(self, tmp_path):
        from steg_analyzer.reporter import Reporter

        r = Reporter(tmp_path, fmt="html")
        results = {"metadata": {"file_name": "test.png"}}
        r.render(results, Path("test.png"))
        html = (tmp_path / "report.html").read_text()
        assert "Steg Analyzer" in html
        assert "test.png" in html


# ── LSB extractor ─────────────────────────────────────────────────────────────


class TestLSBExtractor:
    def test_extracts_bytes(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import lsb_extractor

        path = _make_png()
        a = StegAnalyzer(path)
        out = tmp_path / "out.bin"
        data = lsb_extractor.extract(a, channel="rgb", bit=0, output_path=out)
        assert data is not None
        assert out.exists()
        assert len(data) > 0

    def test_recovers_embedded_message(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import lsb_extractor

        message = b"flag{recovered}"
        path = _make_lsb_image(message, width=256, height=256)
        a = StegAnalyzer(path)
        out = tmp_path / "recovered.bin"
        data = lsb_extractor.extract(a, channel="r", bit=0, output_path=out)
        assert data is not None
        assert message in data


# ── Visual generator ──────────────────────────────────────────────────────────


class TestVisualGenerator:
    def test_ela_output(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import visual_generator

        path = _make_jpeg()
        a = StegAnalyzer(path)
        visual_generator.run(a, tmp_path, ela=True)
        assert (tmp_path / "ela.png").exists()

    def test_fft_output(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import visual_generator

        path = _make_png()
        a = StegAnalyzer(path)
        visual_generator.run(a, tmp_path, fft=True)
        assert (tmp_path / "fft_spectrum.png").exists()

    def test_diff_output(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import visual_generator

        path = _make_png()
        a = StegAnalyzer(path)
        visual_generator.run(a, tmp_path, diff=True)
        diff_dir = tmp_path / "diffs"
        assert diff_dir.exists()
        assert len(list(diff_dir.glob("*.png"))) >= 3

    def test_channels_output(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import visual_generator

        path = _make_png()
        a = StegAnalyzer(path)
        visual_generator.run(a, tmp_path, channels=True)
        ch_dir = tmp_path / "channels"
        assert ch_dir.exists()
        pngs = list(ch_dir.glob("*.png"))
        assert len(pngs) == 6

    def test_bitplanes_output(self, tmp_path):
        from steg_analyzer.analyzer import StegAnalyzer
        from steg_analyzer.modules import visual_generator

        path = _make_png()
        a = StegAnalyzer(path)
        visual_generator.run(a, tmp_path, bitplanes=True)
        bp_dir = tmp_path / "bitplanes"
        assert len(list(bp_dir.glob("*.png"))) == 24
