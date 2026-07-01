#!/usr/bin/env python3
"""Read and summarize a visual validation report for generic agent checks."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--report", default="artifacts/visual-report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = pathlib.Path(args.project_root).resolve()
    report_path = pathlib.Path(args.report)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    if not report_path.exists():
        print(f"Missing visual report: {report_path}", file=sys.stderr)
        return 1

    report = json.loads(report_path.read_text(encoding="utf-8"))
    passed = bool(report.get("pass")) or str(report.get("status", "")).lower() in {"pass", "passed", "success", "ok"}
    score = report.get("score", "n/a")
    threshold = report.get("threshold", "n/a")
    print(f"Visual report: {'PASS' if passed else 'FAIL'} score={score} threshold={threshold}")
    if report.get("issues"):
        print("Issues:")
        for issue in report["issues"][:10]:
            print(f"- {issue}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
