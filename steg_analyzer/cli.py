#!/usr/bin/env python3
"""
Steg Analyzer - All-in-One Steganography Analysis Tool
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyzer import StegAnalyzer
from .reporter import Reporter
from .utils import print_banner, print_error, print_info, print_success, print_warning


def build_parser():
    parser = argparse.ArgumentParser(
        prog="steg-analyzer",
        description="Steg Analyzer - All-in-One Steganography Analysis & Extraction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  steg-analyzer analyze image.png
  steg-analyzer analyze image.jpg --all
  steg-analyzer analyze image.png --lsb --ela --metadata
  steg-analyzer extract image.png --method lsb --output secret.bin
  steg-analyzer extract image.jpg --method steghide --password mypass
  steg-analyzer crack image.jpg --wordlist rockyou.txt
  steg-analyzer visual image.png --output ./results/
        """,
    )

    parser.add_argument("--version", action="version", version=f"Steg Analyzer {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-banner", action="store_true", help="Suppress banner")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── analyze ──────────────────────────────────────────────────────────────
    analyze = subparsers.add_parser("analyze", help="Analyze image for hidden data")
    analyze.add_argument("image", help="Path to image file")
    analyze.add_argument("--all", "-a", action="store_true", help="Run all analysis modules")
    analyze.add_argument("--metadata", action="store_true", help="Extract metadata / EXIF")
    analyze.add_argument("--lsb", action="store_true", help="LSB steganography analysis")
    analyze.add_argument("--ela", action="store_true", help="Error Level Analysis (ELA)")
    analyze.add_argument("--histogram", action="store_true", help="Histogram & chi-square analysis")
    analyze.add_argument("--strings", action="store_true", help="Extract printable strings")
    analyze.add_argument("--dct", action="store_true", help="DCT coefficient analysis (JPEG)")
    analyze.add_argument("--bitplanes", action="store_true", help="Bit-plane visualization")
    analyze.add_argument("--structure", action="store_true", help="File structure analysis")
    analyze.add_argument(
        "--output", "-o", default="./steg-analyzer-output", help="Output directory"
    )
    analyze.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Report format"
    )

    # ── extract ──────────────────────────────────────────────────────────────
    extract = subparsers.add_parser("extract", help="Extract hidden data using a specific method")
    extract.add_argument("image", help="Path to image file")
    extract.add_argument(
        "--method",
        "-m",
        choices=["lsb", "steghide", "outguess", "jsteg", "dct", "all"],
        default="lsb",
        help="Extraction method",
    )
    extract.add_argument("--password", "-p", default="", help="Password / passphrase")
    extract.add_argument(
        "--channel",
        "-c",
        choices=["r", "g", "b", "a", "rgb", "all"],
        default="rgb",
        help="Color channel(s)",
    )
    extract.add_argument("--bit", type=int, choices=range(8), default=0, help="Bit plane (0=LSB)")
    extract.add_argument(
        "--output", "-o", default="extracted.bin", help="Output file for extracted data"
    )

    # ── crack ─────────────────────────────────────────────────────────────────
    crack = subparsers.add_parser("crack", help="Brute-force steghide passphrase")
    crack.add_argument("image", help="Path to image file")
    crack.add_argument("--wordlist", "-w", required=True, help="Path to wordlist file")
    crack.add_argument(
        "--method",
        choices=["steghide", "stegseek"],
        default="steghide",
        help="Tool to use for cracking",
    )
    crack.add_argument("--output", "-o", default="cracked.bin", help="Output file on success")
    crack.add_argument("--threads", "-t", type=int, default=4, help="Number of threads")

    # ── visual ────────────────────────────────────────────────────────────────
    visual = subparsers.add_parser("visual", help="Generate visual analysis images")
    visual.add_argument("image", help="Path to image file")
    visual.add_argument("--output", "-o", default="./steg-analyzer-visual", help="Output directory")
    visual.add_argument("--bitplanes", action="store_true", help="All bit plane images")
    visual.add_argument("--channels", action="store_true", help="Channel separation")
    visual.add_argument("--ela", action="store_true", help="ELA image")
    visual.add_argument("--fft", action="store_true", help="FFT magnitude spectrum")
    visual.add_argument("--diff", action="store_true", help="Channel difference images")
    visual.add_argument("--all", "-a", action="store_true", help="Generate all visual outputs")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Validate image path
    if hasattr(args, "image"):
        image_path = Path(args.image)
        if not image_path.exists():
            print_error(f"File not found: {args.image}")
            sys.exit(1)

    if args.command == "analyze":
        run_analyze(args)
    elif args.command == "extract":
        run_extract(args)
    elif args.command == "crack":
        run_crack(args)
    elif args.command == "visual":
        run_visual(args)


def run_analyze(args):
    from .modules import (
        bitplane_analysis,
        dct_analysis,
        ela,
        histogram_analysis,
        lsb_analysis,
        metadata,
        strings_extractor,
        structure_analysis,
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_path = Path(args.image)
    analyzer = StegAnalyzer(image_path, verbose=args.verbose)
    reporter = Reporter(output_dir, fmt=args.format)

    run_all = args.all

    print_info(f"Analyzing: {image_path.name}")
    print()

    results = {}

    if run_all or args.metadata:
        print_info("Running metadata analysis...")
        results["metadata"] = metadata.run(analyzer)

    if run_all or args.structure:
        print_info("Running file structure analysis...")
        results["structure"] = structure_analysis.run(analyzer)

    if run_all or args.strings:
        print_info("Extracting strings...")
        results["strings"] = strings_extractor.run(analyzer)

    if run_all or args.lsb:
        print_info("Running LSB analysis...")
        results["lsb"] = lsb_analysis.run(analyzer)

    if run_all or args.ela:
        print_info("Running Error Level Analysis...")
        results["ela"] = ela.run(analyzer, output_dir)

    if run_all or args.histogram:
        print_info("Running histogram / chi-square analysis...")
        results["histogram"] = histogram_analysis.run(analyzer)

    if run_all or args.dct:
        if image_path.suffix.lower() in (".jpg", ".jpeg"):
            print_info("Running DCT coefficient analysis...")
            results["dct"] = dct_analysis.run(analyzer)
        else:
            print_warning("DCT analysis only applies to JPEG files — skipped.")

    if run_all or args.bitplanes:
        print_info("Generating bit-plane images...")
        results["bitplanes"] = bitplane_analysis.run(analyzer, output_dir)

    print()
    reporter.render(results, image_path)
    print_success(f"Analysis complete. Results saved to: {output_dir}")


def run_extract(args):
    from .modules import dct_extractor, lsb_extractor, steghide_extractor

    image_path = Path(args.image)
    analyzer = StegAnalyzer(image_path, verbose=args.verbose)

    print_info(f"Extracting from: {image_path.name} using method={args.method}")

    output_path = Path(args.output)
    extracted = None

    if args.method in ("lsb", "all"):
        extracted = lsb_extractor.extract(
            analyzer,
            channel=args.channel,
            bit=args.bit,
            output_path=output_path,
        )

    if args.method in ("steghide", "all"):
        extracted = steghide_extractor.extract(
            analyzer,
            password=args.password,
            output_path=output_path,
        )

    if args.method in ("dct", "all"):
        extracted = dct_extractor.extract(analyzer, output_path=output_path)

    if extracted:
        print_success(f"Data extracted → {output_path}")
    else:
        print_warning("No data could be extracted with the given parameters.")


def run_crack(args):
    from .modules import cracker

    image_path = Path(args.image)
    wordlist_path = Path(args.wordlist)

    if not wordlist_path.exists():
        print_error(f"Wordlist not found: {args.wordlist}")
        sys.exit(1)

    print_info(f"Cracking: {image_path.name}")
    print_info(f"Wordlist: {wordlist_path.name}")
    print_info(f"Threads:  {args.threads}")
    print()

    result = cracker.run(
        image_path,
        wordlist_path,
        method=args.method,
        output_path=Path(args.output),
        threads=args.threads,
    )

    if result:
        print_success(f"Password found: '{result}'")
        print_success(f"Extracted data saved to: {args.output}")
    else:
        print_warning("Password not found in wordlist.")


def run_visual(args):
    from .modules import visual_generator

    image_path = Path(args.image)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = StegAnalyzer(image_path, verbose=args.verbose)
    run_all = args.all

    print_info(f"Generating visual analysis for: {image_path.name}")
    print_info(f"Output directory: {output_dir}")
    print()

    visual_generator.run(
        analyzer,
        output_dir,
        bitplanes=run_all or args.bitplanes,
        channels=run_all or args.channels,
        ela=run_all or args.ela,
        fft=run_all or args.fft,
        diff=run_all or args.diff,
    )

    print_success(f"Visual outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
