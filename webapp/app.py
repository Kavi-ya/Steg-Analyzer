"""
Steg Analyzer Web App - Flask backend
"""
from __future__ import annotations

import base64
import io
import sys
import tempfile
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from PIL import Image
import numpy as np

# Make sure the parent package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from steg_analyzer.analyzer import StegAnalyzer
from steg_analyzer.modules import (
    ela,
    histogram_analysis,
    lsb_analysis,
    metadata,
    structure_analysis,
    strings_extractor,
)

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: {suffix}"}), 400

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        analyzer = StegAnalyzer(tmp_path, verbose=False)
        results: dict = {}

        # ── Metadata ─────────────────────────────────────────────────────────
        try:
            results["metadata"] = metadata.run(analyzer)
        except Exception as e:
            results["metadata"] = {"error": str(e)}

        # ── LSB Analysis ──────────────────────────────────────────────────────
        try:
            results["lsb"] = lsb_analysis.run(analyzer)
        except Exception as e:
            results["lsb"] = {"error": str(e)}

        # ── Histogram / Chi-Square ────────────────────────────────────────────
        try:
            results["histogram"] = histogram_analysis.run(analyzer)
        except Exception as e:
            results["histogram"] = {"error": str(e)}

        # ── Structure Analysis ────────────────────────────────────────────────
        try:
            results["structure"] = structure_analysis.run(analyzer)
        except Exception as e:
            results["structure"] = {"error": str(e)}

        # ── Strings Extraction ────────────────────────────────────────────────
        try:
            results["strings"] = strings_extractor.run(analyzer)
        except Exception as e:
            results["strings"] = {"error": str(e)}

        # ── ELA (Error Level Analysis) ────────────────────────────────────────
        try:
            with tempfile.TemporaryDirectory() as ela_dir:
                ela_results = ela.run(analyzer, Path(ela_dir))
                # Read the generated ELA image & encode to base64
                ela_img_path = Path(ela_results.get("ela_image", ""))
                if ela_img_path.exists():
                    ela_b64 = base64.b64encode(ela_img_path.read_bytes()).decode()
                    ela_results["ela_image_b64"] = f"data:image/png;base64,{ela_b64}"
                    del ela_results["ela_image"]
                results["ela"] = ela_results
        except Exception as e:
            results["ela"] = {"error": str(e)}

        # ── Original image thumbnail ──────────────────────────────────────────
        try:
            img = Image.open(tmp_path)
            img.thumbnail((600, 600))
            buf = io.BytesIO()
            fmt = "PNG" if suffix in (".png", ".bmp", ".gif", ".tiff", ".tif", ".webp") else "JPEG"
            img.save(buf, format=fmt)
            thumb_b64 = base64.b64encode(buf.getvalue()).decode()
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
            results["thumbnail"] = f"data:{mime};base64,{thumb_b64}"
        except Exception:
            results["thumbnail"] = None

        return jsonify(results)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    app.run(debug=True, port=5050)
