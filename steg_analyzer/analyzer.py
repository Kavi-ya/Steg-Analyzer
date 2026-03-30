"""
Steg Analyzer - Core image analyzer / loader.
"""

from pathlib import Path

import numpy as np
from PIL import Image


class StegAnalyzer:
    """
    Loads and pre-processes an image file for steganography analysis.
    All analysis modules receive an instance of this class.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

    def __init__(self, image_path: Path, verbose: bool = False):
        self.path = Path(image_path)
        self.verbose = verbose

        if self.path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {self.path.suffix}")

        self._raw_bytes: bytes | None = None
        self._pil_image: Image.Image | None = None
        self._arr_rgb: np.ndarray | None = None
        self._arr_rgba: np.ndarray | None = None

    # ── lazy loaders ─────────────────────────────────────────────────────────

    @property
    def raw_bytes(self) -> bytes:
        if self._raw_bytes is None:
            self._raw_bytes = self.path.read_bytes()
        return self._raw_bytes

    @property
    def pil_image(self) -> Image.Image:
        if self._pil_image is None:
            self._pil_image = Image.open(self.path)
        return self._pil_image

    @property
    def arr_rgb(self) -> np.ndarray:
        """(H, W, 3) uint8 RGB array."""
        if self._arr_rgb is None:
            self._arr_rgb = np.array(self.pil_image.convert("RGB"))
        return self._arr_rgb

    @property
    def arr_rgba(self) -> np.ndarray:
        """(H, W, 4) uint8 RGBA array."""
        if self._arr_rgba is None:
            self._arr_rgba = np.array(self.pil_image.convert("RGBA"))
        return self._arr_rgba

    # ── convenience ──────────────────────────────────────────────────────────

    @property
    def width(self) -> int:
        return self.pil_image.width

    @property
    def height(self) -> int:
        return self.pil_image.height

    @property
    def mode(self) -> str:
        return self.pil_image.mode

    @property
    def is_jpeg(self) -> bool:
        return self.path.suffix.lower() in (".jpg", ".jpeg")

    @property
    def file_size(self) -> int:
        return self.path.stat().st_size

    def channel(self, name: str) -> np.ndarray:
        """Return a single (H, W) channel array by name: r/g/b/a."""
        mapping = {"r": 0, "g": 1, "b": 2, "a": 3}
        idx = mapping.get(name.lower())
        if idx is None:
            raise ValueError(f"Unknown channel: {name}")
        if idx < 3:
            return self.arr_rgb[:, :, idx]
        return self.arr_rgba[:, :, 3]

    def extract_lsb_bits(
        self,
        channels: list[str],
        bit_position: int = 0,
    ) -> bytes:
        """
        Extract the specified bit from each listed channel,
        interleaved pixel-by-pixel, and pack into bytes.
        """
        bit_arrays = []
        for ch in channels:
            plane = (self.channel(ch) >> bit_position) & 1
            bit_arrays.append(plane.flatten())

        h, w = self.arr_rgb.shape[:2]
        n_pixels = h * w
        bpp = len(bit_arrays)
        combined = np.zeros(n_pixels * bpp, dtype=np.uint8)
        for idx, ba in enumerate(bit_arrays):
            combined[idx::bpp] = ba

        pad = (8 - len(combined) % 8) % 8
        if pad:
            combined = np.pad(combined, (0, pad))
        return np.packbits(combined).tobytes()
