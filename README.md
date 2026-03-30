# 🔍 Steg Analyzer

**All-in-One Steganography Analysis & Extraction Tool**

[![CI](https://github.com/Kavi-ya/Steg-Analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Kavi-ya/Steg-Analyzer/actions)
[![PyPI](https://img.shields.io/pypi/v/steg-analyzer?color=blue)](https://pypi.org/project/steg-analyzer/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/steg-analyzer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Steg Analyzer is a comprehensive steganography toolkit for CTF challenges, digital forensics, and security research. It bundles every major analysis technique into a single, clean CLI.

---

## ✨ Features

| Module | What it does |
|---|---|
| **Metadata** | Full EXIF / JPEG marker extraction via Pillow + exiftool |
| **LSB Analysis** | Brute-forces all channel × bit × order combinations |
| **ELA** | Error Level Analysis — reveals hidden manipulated regions |
| **Chi-Square** | Statistical test for LSB embedding probability |
| **DCT / JSteg** | JPEG DCT coefficient LSB extraction (JSteg-compatible) |
| **Bit Planes** | Generates 24 bit-plane visualisation images |
| **Strings** | Extracts printable ASCII + CTF flag patterns |
| **Structure** | Finds appended files, embedded signatures, base64 blobs |
| **Visual** | FFT spectrum, channel XOR/diff, colour channel separation |
| **Extract** | LSB, Steghide, DCT extraction with one command |
| **Crack** | Multi-threaded steghide brute-force + stegseek support |

---

## 📦 Installation

### From PyPI (recommended)
```bash
pip install steg-analyzer

# With all optional extras (OpenCV, JPEG DCT support, etc.)
pip install "steg-analyzer[full]"
```

### From source
```bash
git clone https://github.com/your-org/steg-analyzer.git
cd steg_analyzer
pip install -e ".[full]"
```

### System dependencies (optional but useful)
```bash
# Debian / Ubuntu
sudo apt install steghide stegseek exiftool zbar-tools

# macOS
brew install steghide exiftool zbar
```

---

## 🚀 Quick Start

```bash
# Full analysis — runs ALL modules
steg-analyzer analyze suspicious.jpg --all

# Targeted analysis
steg-analyzer analyze image.png --lsb --ela --metadata

# Extract hidden data
steg-analyzer extract image.png --method lsb --channel rgb --bit 0 --output secret.bin
steg-analyzer extract image.jpg --method steghide --password "mypass" --output data.bin

# Crack steghide password
steg-analyzer crack image.jpg --wordlist rockyou.txt --threads 8

# Generate all visual analysis images
steg-analyzer visual image.png --all --output ./visuals/

# Save report as JSON or HTML
steg-analyzer analyze image.jpg --all --format json --output ./report/
steg-analyzer analyze image.jpg --all --format html --output ./report/
```

---

## 📖 Command Reference

### `steg-analyzer analyze`

```
steg-analyzer analyze <image> [options]

Options:
  --all, -a          Run every analysis module
  --metadata         EXIF and file metadata
  --lsb              LSB bit-plane analysis
  --ela              Error Level Analysis
  --histogram        Chi-square steganography test
  --strings          Printable string extraction
  --dct              JPEG DCT coefficient analysis
  --bitplanes        Save all 24 bit-plane images
  --structure        File structure (appended data, embedded files)
  --output, -o DIR   Output directory (default: ./steg_analyzer_output)
  --format FMT       Output format: text | json | html (default: text)
```

### `steg-analyzer extract`

```
steg-analyzer extract <image> [options]

Options:
  --method, -m       lsb | steghide | dct | all (default: lsb)
  --channel, -c      r | g | b | a | rgb | all  (default: rgb)
  --bit, -b          Bit plane 0-7               (default: 0=LSB)
  --password, -p     Passphrase for steghide
  --output, -o FILE  Output file                 (default: extracted.bin)
```

### `steg-analyzer crack`

```
steg-analyzer crack <image> --wordlist <wordlist> [options]

Options:
  --wordlist, -w FILE  Path to password list (required)
  --method             steghide | stegseek    (default: steghide)
  --threads, -t N      Worker threads         (default: 4)
  --output, -o FILE    Save extracted data on success
```

### `steg-analyzer visual`

```
steg-analyzer visual <image> [options]

Options:
  --all, -a        Generate every visual output type
  --bitplanes      24 bit-plane PNGs (R/G/B × bits 0-7)
  --channels       RGB channel separation images
  --ela            Error Level Analysis image
  --fft            FFT magnitude spectrum
  --diff           Channel difference & XOR images
  --output, -o DIR Output directory (default: ./steg_analyzer_visual)
```

---

## 🐍 Python API

Steg Analyzer can also be used as a library:

```python
from pathlib import Path
from steg_analyzer.analyzer import StegAnalyzer
from steg_analyzer.modules import metadata, lsb_analysis, ela, structure_analysis

analyzer = StegAnalyzer(Path("suspicious.jpg"))

# Run specific modules
meta   = metadata.run(analyzer)
lsb    = lsb_analysis.run(analyzer)
struct = structure_analysis.run(analyzer)

# Check for flags
for module_result in [meta, lsb, struct]:
    if "flags" in module_result:
        print("FLAGS FOUND:", module_result["flags"])

# Extract LSB bytes directly
raw_bits = analyzer.extract_lsb_bits(["r", "g", "b"], bit_position=0)
print(raw_bits[:64])

# ELA
from steg_analyzer.modules import ela as ela_mod
ela_result = ela_mod.run(analyzer, output_dir=Path("./output"))
print(ela_result["verdict"])
```

---

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run full test suite
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=steg_analyzer --cov-report=term-missing

# Run a specific test class
pytest tests/ -v -k "TestLSBAnalysis"
```

---

## 🗂️ Project Structure

```
steg_analyzer/
├── steg_analyzer/
│   ├── __init__.py              # Version info
│   ├── cli.py                   # CLI entry point (argparse)
│   ├── analyzer.py              # Core image loader + helpers
│   ├── reporter.py              # text / JSON / HTML reporter
│   ├── utils.py                 # Colors, file detection, flag finder
│   └── modules/
│       ├── metadata.py          # EXIF + JPEG marker analysis
│       ├── lsb_analysis.py      # Comprehensive LSB brute-force
│       ├── ela.py               # Error Level Analysis
│       ├── histogram_analysis.py# Chi-square statistical test
│       ├── strings_extractor.py # Printable strings + flag hunt
│       ├── dct_analysis.py      # JPEG DCT / JSteg analysis
│       ├── bitplane_analysis.py # Bit-plane image generator
│       ├── structure_analysis.py# File structure + embedded data
│       ├── lsb_extractor.py     # LSB data extractor
│       ├── steghide_extractor.py# Steghide wrapper
│       ├── dct_extractor.py     # JSteg DCT extractor
│       ├── cracker.py           # Multi-threaded password cracker
│       └── visual_generator.py  # Visual analysis image generator
├── tests/
│   └── test_steg_analyzer.py            # Full test suite (pytest)
├── .github/workflows/ci.yml     # GitHub Actions CI + PyPI publish
├── pyproject.toml               # Modern packaging config
├── requirements.txt             # Runtime dependencies
├── LICENSE                      # MIT
└── README.md
```

---

## 🤝 Contributing

1. Fork the repo and create a feature branch
2. Write tests for your changes
3. Run `pytest` and `ruff check steg_analyzer/` to make sure everything passes
4. Open a pull request — all contributions welcome!

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.

---

## ⚠️ Disclaimer

Steg Analyzer is built for **legal, ethical use only** — CTF competitions, academic research, and analysing your own files. Never use it against systems or files you do not have permission to analyse.