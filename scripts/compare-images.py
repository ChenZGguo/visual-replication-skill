#!/usr/bin/env python3
"""Compare a reference image with an actual image and write a JSON report."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    print("Pillow is required. Install with: python3 -m pip install pillow", file=sys.stderr)
    raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--output-dir", default="artifacts/diff")
    parser.add_argument("--report", default="artifacts/visual-report.json")
    parser.add_argument("--threshold", type=float, default=0.985, help="Minimum similarity score required to pass.")
    parser.add_argument("--pixel-threshold", type=int, default=24, help="Per-channel diff threshold for changed pixels.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_path = pathlib.Path(args.reference)
    actual_path = pathlib.Path(args.actual)
    output_dir = pathlib.Path(args.output_dir)
    report_path = pathlib.Path(args.report)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    reference = Image.open(reference_path).convert("RGB")
    actual = Image.open(actual_path).convert("RGB")

    issues: list[str] = []
    if reference.size != actual.size:
        issues.append(f"Image size differs: reference={reference.size}, actual={actual.size}")
        actual = actual.resize(reference.size)

    diff = ImageChops.difference(reference, actual)
    diff_path = output_dir / "diff.png"
    diff.save(diff_path)

    histogram = diff.convert("L").histogram()
    total_pixels = reference.size[0] * reference.size[1]
    changed_pixels = sum(count for value, count in enumerate(histogram) if value > args.pixel_threshold)
    changed_ratio = changed_pixels / total_pixels if total_pixels else 1.0
    similarity = max(0.0, 1.0 - changed_ratio)
    passed = similarity >= args.threshold

    if not passed:
        issues.append(f"Similarity {similarity:.4f} is below threshold {args.threshold:.4f}")
        issues.append(f"Changed pixel ratio: {changed_ratio:.4%}")

    report = {
        "pass": passed,
        "status": "pass" if passed else "fail",
        "score": similarity,
        "threshold": args.threshold,
        "reference": str(reference_path),
        "actual": str(actual_path),
        "diff": str(diff_path),
        "changedPixels": changed_pixels,
        "totalPixels": total_pixels,
        "changedRatio": changed_ratio,
        "issues": issues,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
