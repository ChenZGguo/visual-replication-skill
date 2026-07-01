#!/usr/bin/env python3
"""Generic finish-time check for visual reproduction validation."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from typing import Any


DEFAULT_CONFIG = {
    "enabled": True,
    "mode": "auto",
    "validationCommand": 'python3 scripts/generate-report.py --project-root "$PWD" --report artifacts/visual-report.json',
    "reportPath": "artifacts/visual-report.json",
    "diffPath": "artifacts/diff",
    "referencePaths": [
        "references",
        "reference",
        "design",
        "figma",
        "screenshots/reference",
        "artifacts/reference",
    ],
    "triggerKeywords": [
        "screenshot",
        "design",
        "figma",
        "animation",
        "video",
        "visual",
        "reproduce",
        "replicate",
        "pixel",
        "截图",
        "设计稿",
        "复刻",
        "还原",
        "动画",
        "视频",
        "视觉",
        "像素",
    ],
}


def skill_root() -> pathlib.Path:
    """Return the directory containing this script, which is the skill root."""
    return pathlib.Path(__file__).resolve().parent.parent


def emit_block(reason: str) -> None:
    print(json.dumps({"status": "blocked", "decision": "block", "reason": reason}, ensure_ascii=False))
    raise SystemExit(1)


def load_json(path: pathlib.Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        emit_block(f"视觉验证配置无法读取: {path}: {exc}")
    merged = dict(default)
    merged.update(data)
    return merged


def has_reference_asset(root: pathlib.Path, paths: list[str]) -> bool:
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm"}
    for rel in paths:
        candidate = root / rel
        if candidate.is_file() and candidate.suffix.lower() in extensions:
            return True
        if candidate.is_dir():
            for item in candidate.rglob("*"):
                if item.is_file() and item.suffix.lower() in extensions:
                    return True
    return False


def contains_keywords(text: str, keywords: list[str]) -> bool:
    haystack = text.lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def report_passed(report: dict[str, Any]) -> bool:
    if isinstance(report.get("pass"), bool):
        return bool(report["pass"])
    status = str(report.get("status", "")).lower()
    if status in {"pass", "passed", "success", "ok"}:
        return True
    if status in {"fail", "failed", "error"}:
        return False
    score = report.get("score")
    threshold = report.get("threshold", 0.98)
    if isinstance(score, (int, float)) and isinstance(threshold, (int, float)):
        return score >= threshold
    return False


def main() -> int:
    root = pathlib.Path(os.environ.get("AGENT_PROJECT_ROOT", os.getcwd())).resolve()
    skill = skill_root()
    config_path = skill / "config.json"
    config = load_json(config_path, DEFAULT_CONFIG)

    if not config.get("enabled", True):
        print(json.dumps({"status": "skipped", "reason": "visual replication check disabled"}, ensure_ascii=False))
        return 0

    stdin_text = sys.stdin.read()
    mode = str(config.get("mode", "auto")).lower()
    report_path = root / str(config.get("reportPath", DEFAULT_CONFIG["reportPath"]))
    reference_paths = [str(item) for item in config.get("referencePaths", [])]
    keywords = [str(item) for item in config.get("triggerKeywords", [])]

    relevant = mode == "always"
    if mode == "auto":
        relevant = (
            report_path.exists()
            or has_reference_asset(root, reference_paths)
            or contains_keywords(stdin_text, keywords)
            or os.environ.get("VISUAL_REPLICATION_REQUIRED") == "1"
        )

    if not relevant:
        print(json.dumps({"status": "skipped", "reason": "not a visual replication task"}, ensure_ascii=False))
        return 0

    command = str(config.get("validationCommand", DEFAULT_CONFIG["validationCommand"]))
    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(root)
    env["PWD"] = str(root)
    env["VISUAL_REPLICATION_SKILL_ROOT"] = str(skill)

    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=int(config.get("timeoutSeconds", 300)),
    )

    report: dict[str, Any] | None = None
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            emit_block(f"视觉验证报告无法读取: {report_path}: {exc}")

    if completed.returncode != 0 and report is None:
        output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
        if len(output) > 1800:
            output = output[-1800:]
        emit_block(
            "视觉验证未通过，且未生成报告。请运行视觉捕获和比对脚本，生成 "
            f"{report_path.relative_to(root)} 后继续。\n\n{output}"
        )

    if report is None:
        emit_block(f"视觉验证未生成报告: {report_path.relative_to(root)}")

    if report_passed(report):
        print(json.dumps({"status": "passed", "report": str(report_path.relative_to(root))}, ensure_ascii=False))
        return 0

    diff_path = root / str(config.get("diffPath", DEFAULT_CONFIG["diffPath"]))
    issues = report.get("issues") or report.get("differences") or []
    issue_text = ""
    if isinstance(issues, list) and issues:
        issue_text = "\n主要差异:\n" + "\n".join(f"- {item}" for item in issues[:5])

    emit_block(
        "视觉验证未通过。请读取 "
        f"{report_path.relative_to(root)} 和 {diff_path.relative_to(root)}/，"
        "修复差异最大的三项，然后重新渲染并再次验证。"
        f"{issue_text}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
