"""
Steg Analyzer – Steghide passphrase brute-forcer with multi-threading.
"""

from __future__ import annotations
import subprocess
import threading
from pathlib import Path
from queue import Queue, Empty
from ..utils import print_info, print_result


def run(
    image_path: Path,
    wordlist_path: Path,
    method: str = "steghide",
    output_path: Path = Path("cracked.bin"),
    threads: int = 4,
) -> str | None:

    # Try stegseek first if requested (much faster)
    if method == "stegseek":
        return _run_stegseek(image_path, wordlist_path, output_path)

    # Multi-threaded steghide brute-force
    return _run_steghide_brute(image_path, wordlist_path, output_path, threads)


def _run_stegseek(image_path: Path, wordlist_path: Path, output_path: Path) -> str | None:
    try:
        r = subprocess.run(
            ["stegseek", str(image_path), str(wordlist_path), str(output_path)],
            capture_output=True, text=True, timeout=300,
        )
        # Parse password from stegseek output
        for line in r.stdout.splitlines() + r.stderr.splitlines():
            if "passphrase" in line.lower() or "found" in line.lower():
                print_info(line.strip())
        if output_path.exists() and output_path.stat().st_size > 0:
            return "found (see stegseek output)"
    except FileNotFoundError:
        print_info("stegseek not found, falling back to steghide brute-force")
        return _run_steghide_brute(image_path, wordlist_path, output_path, threads=4)
    except subprocess.TimeoutExpired:
        print_info("stegseek timed out")
    return None


def _run_steghide_brute(
    image_path: Path,
    wordlist_path: Path,
    output_path: Path,
    threads: int,
) -> str | None:
    passwords = wordlist_path.read_text(errors="replace").splitlines()
    total = len(passwords)
    print_info(f"Loaded {total} passwords — using {threads} threads")

    q: Queue[str] = Queue()
    for p in passwords:
        q.put(p.strip())

    found: list[str] = []
    lock = threading.Lock()
    checked = [0]

    def worker():
        while not found:
            try:
                pwd = q.get_nowait()
            except Empty:
                return
            try:
                r = subprocess.run(
                    [
                        "steghide", "extract",
                        "-sf", str(image_path),
                        "-p", pwd,
                        "-xf", str(output_path),
                        "-f",
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                with lock:
                    checked[0] += 1
                    if checked[0] % 200 == 0:
                        print_info(f"  Tried {checked[0]}/{total}...")
                if r.returncode == 0:
                    with lock:
                        if not found:
                            found.append(pwd)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                with lock:
                    checked[0] += 1

    thread_list = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()

    if found:
        print_result("Password found", repr(found[0]))
        print_result("Attempts", str(checked[0]))
        return found[0]

    print_result("Attempts", str(checked[0]))
    return None
