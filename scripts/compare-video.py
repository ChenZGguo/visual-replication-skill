#!/usr/bin/env python3
"""Compare two videos frame-by-frame and write a JSON report."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    print("opencv-python and numpy are required. Install with: python3 -m pip install opencv-python numpy", file=sys.stderr)
    raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--output-dir", default="artifacts/diff")
    parser.add_argument("--report", default="artifacts/visual-report.json")
    parser.add_argument("--threshold", type=float, default=0.965)
    parser.add_argument("--max-frames", type=int, default=240)
    return parser.parse_args()


def read_frame(capture: cv2.VideoCapture):
    ok, frame = capture.read()
    if not ok:
        return None
    return frame


def main() -> int:
    args = parse_args()
    output_dir = pathlib.Path(args.output_dir)
    report_path = pathlib.Path(args.report)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    reference = cv2.VideoCapture(args.reference)
    actual = cv2.VideoCapture(args.actual)
    frame_scores: list[float] = []
    issues: list[str] = []
    worst_frame = -1
    worst_score = 1.0

    for frame_index in range(args.max_frames):
        reference_frame = read_frame(reference)
        actual_frame = read_frame(actual)
        if reference_frame is None or actual_frame is None:
            break
        if reference_frame.shape != actual_frame.shape:
            actual_frame = cv2.resize(actual_frame, (reference_frame.shape[1], reference_frame.shape[0]))
        diff = cv2.absdiff(reference_frame, actual_frame)
        score = 1.0 - float(np.mean(diff) / 255.0)
        frame_scores.append(score)
        if score < worst_score:
            worst_score = score
            worst_frame = frame_index
            cv2.imwrite(str(output_dir / "worst-frame-diff.png"), diff)

    if not frame_scores:
        issues.append("No comparable frames were found.")
        score = 0.0
    else:
        score = float(sum(frame_scores) / len(frame_scores))

    passed = score >= args.threshold
    if not passed:
        issues.append(f"Average frame similarity {score:.4f} is below threshold {args.threshold:.4f}")
        if worst_frame >= 0:
            issues.append(f"Worst frame index: {worst_frame}, score={worst_score:.4f}")

    report = {
        "pass": passed,
        "status": "pass" if passed else "fail",
        "score": score,
        "threshold": args.threshold,
        "reference": args.reference,
        "actual": args.actual,
        "diff": str(output_dir),
        "comparedFrames": len(frame_scores),
        "worstFrame": worst_frame,
        "worstFrameScore": worst_score,
        "issues": issues,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
