#!/usr/bin/env python3
"""Compare two videos frame-by-frame and write a JSON report."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--output-dir", default="artifacts/diff")
    parser.add_argument("--report", default="artifacts/visual-report.json")
    parser.add_argument("--threshold", type=float, default=0.965)
    parser.add_argument("--motion-threshold", type=float, default=0.93)
    parser.add_argument("--max-frames", type=int, default=240)
    return parser.parse_args()


def read_frame(capture: cv2.VideoCapture):
    ok, frame = capture.read()
    if not ok:
        return None
    return frame


def main() -> int:
    args = parse_args()
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("opencv-python and numpy are required. Install with: python3 -m pip install opencv-python numpy", file=sys.stderr)
        return 2

    output_dir = pathlib.Path(args.output_dir)
    report_path = pathlib.Path(args.report)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    reference = cv2.VideoCapture(args.reference)
    actual = cv2.VideoCapture(args.actual)
    frame_scores: list[float] = []
    motion_scores: list[float] = []
    issues: list[str] = []
    blocking_issues: list[str] = []
    worst_frame = -1
    worst_score = 1.0
    worst_motion_frame = -1
    worst_motion_score = 1.0
    previous_reference_frame = None
    previous_actual_frame = None

    if not reference.isOpened():
        blocking_issues.append(f"Reference video could not be opened: {args.reference}")
    if not actual.isOpened():
        blocking_issues.append(f"Actual video could not be opened: {args.actual}")

    reference_frame_count = int(reference.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    actual_frame_count = int(actual.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    reference_fps = float(reference.get(cv2.CAP_PROP_FPS) or 0.0)
    actual_fps = float(actual.get(cv2.CAP_PROP_FPS) or 0.0)

    if reference_fps and actual_fps and abs(reference_fps - actual_fps) > 0.01:
        blocking_issues.append(f"FPS differs: reference={reference_fps:.3f}, actual={actual_fps:.3f}")

    if reference_frame_count and actual_frame_count and abs(reference_frame_count - actual_frame_count) > 1:
        blocking_issues.append(f"Frame count differs: reference={reference_frame_count}, actual={actual_frame_count}")

    if reference_fps and actual_fps and reference_frame_count and actual_frame_count:
        reference_duration = reference_frame_count / reference_fps
        actual_duration = actual_frame_count / actual_fps
        if abs(reference_duration - actual_duration) > 0.05:
            blocking_issues.append(f"Duration differs: reference={reference_duration:.3f}s, actual={actual_duration:.3f}s")

    for frame_index in range(args.max_frames):
        reference_frame = read_frame(reference)
        actual_frame = read_frame(actual)
        if reference_frame is None and actual_frame is None:
            break
        if reference_frame is None or actual_frame is None:
            blocking_issues.append(f"One video ended early at frame {frame_index}.")
            break
        if reference_frame.shape != actual_frame.shape:
            blocking_issues.append(
                f"Frame size differs at frame {frame_index}: reference={reference_frame.shape}, actual={actual_frame.shape}"
            )
            actual_frame = cv2.resize(actual_frame, (reference_frame.shape[1], reference_frame.shape[0]))
        diff = cv2.absdiff(reference_frame, actual_frame)
        score = 1.0 - float(np.mean(diff) / 255.0)
        frame_scores.append(score)
        if score < worst_score:
            worst_score = score
            worst_frame = frame_index
            cv2.imwrite(str(output_dir / "worst-frame-diff.png"), diff)

        if previous_reference_frame is not None and previous_actual_frame is not None:
            reference_motion = cv2.absdiff(reference_frame, previous_reference_frame)
            actual_motion = cv2.absdiff(actual_frame, previous_actual_frame)
            motion_diff = cv2.absdiff(reference_motion, actual_motion)
            motion_score = 1.0 - float(np.mean(motion_diff) / 255.0)
            motion_scores.append(motion_score)
            if motion_score < worst_motion_score:
                worst_motion_score = motion_score
                worst_motion_frame = frame_index
                cv2.imwrite(str(output_dir / "worst-motion-diff.png"), motion_diff)

        previous_reference_frame = reference_frame
        previous_actual_frame = actual_frame

    if not frame_scores:
        blocking_issues.append("No comparable frames were found.")
        score = 0.0
    else:
        score = float(sum(frame_scores) / len(frame_scores))

    if motion_scores:
        motion_score = float(sum(motion_scores) / len(motion_scores))
    else:
        motion_score = 0.0 if len(frame_scores) > 1 else 1.0

    issues.extend(blocking_issues)
    passed = score >= args.threshold and motion_score >= args.motion_threshold and not blocking_issues
    if not passed:
        if score < args.threshold:
            issues.append(f"Average frame similarity {score:.4f} is below threshold {args.threshold:.4f}")
        if motion_score < args.motion_threshold:
            issues.append(f"Average frame-to-frame motion similarity {motion_score:.4f} is below threshold {args.motion_threshold:.4f}")
        if worst_frame >= 0:
            issues.append(f"Worst frame index: {worst_frame}, score={worst_score:.4f}")
        if worst_motion_frame >= 0:
            issues.append(f"Worst motion frame index: {worst_motion_frame}, score={worst_motion_score:.4f}")

    report = {
        "pass": passed,
        "status": "pass" if passed else "fail",
        "score": score,
        "threshold": args.threshold,
        "motionScore": motion_score,
        "motionThreshold": args.motion_threshold,
        "reference": args.reference,
        "actual": args.actual,
        "diff": str(output_dir),
        "comparedFrames": len(frame_scores),
        "comparedMotionFrames": len(motion_scores),
        "worstFrame": worst_frame,
        "worstFrameScore": worst_score,
        "worstMotionFrame": worst_motion_frame,
        "worstMotionFrameScore": worst_motion_score,
        "issues": issues,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
