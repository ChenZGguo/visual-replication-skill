#!/usr/bin/env python3
"""Generic finish-time check for visual reproduction validation."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
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
    "maxReportAgeSeconds": 86400,
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


def resolve_report_path(root: pathlib.Path, value: Any) -> pathlib.Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = pathlib.Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def display_path(root: pathlib.Path, path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def newest_mtime(paths: list[pathlib.Path]) -> float | None:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    return max(mtimes) if mtimes else None


def reference_assets(root: pathlib.Path, paths: list[str]) -> list[pathlib.Path]:
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm"}
    assets: list[pathlib.Path] = []
    for rel in paths:
        candidate = root / rel
        if candidate.is_file() and candidate.suffix.lower() in extensions:
            assets.append(candidate)
        elif candidate.is_dir():
            assets.extend(item for item in candidate.rglob("*") if item.is_file() and item.suffix.lower() in extensions)
    return assets


def tracked_source_files(root: pathlib.Path) -> list[pathlib.Path]:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return []
    if completed.returncode != 0:
        return []

    excluded_prefixes = ("artifacts/", "references/", "reference/", "design/", "figma/", "screenshots/reference/")
    excluded_parts = {"node_modules", "dist", "build", ".next", ".git"}
    source_suffixes = {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".html",
        ".vue",
        ".svelte",
        ".astro",
        ".json",
    }
    files: list[pathlib.Path] = []
    for line in completed.stdout.splitlines():
        if not line or line.startswith(excluded_prefixes):
            continue
        path = root / line
        if path.is_file() and path.suffix.lower() in source_suffixes and not any(part in excluded_parts for part in path.parts):
            files.append(path)
    return files


def validate_evidence(root: pathlib.Path, config: dict[str, Any], report_path: pathlib.Path, report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    report_mtime = report_path.stat().st_mtime
    max_age = int(config.get("maxReportAgeSeconds", DEFAULT_CONFIG["maxReportAgeSeconds"]))
    if max_age > 0 and time.time() - report_mtime > max_age:
        issues.append(f"视觉验证报告过旧，超过 {max_age} 秒: {display_path(root, report_path)}")

    actual_path = resolve_report_path(root, report.get("actual"))
    if actual_path is not None and not actual_path.exists():
        issues.append(f"actual 捕获产物不存在: {display_path(root, actual_path)}")

    diff_path = resolve_report_path(root, report.get("diff"))
    if diff_path is not None:
        if not diff_path.exists():
            issues.append(f"diff 产物不存在: {display_path(root, diff_path)}")
        elif diff_path.is_dir() and not any(diff_path.iterdir()):
            issues.append(f"diff 目录为空: {display_path(root, diff_path)}")

    reference_mtime = newest_mtime(reference_assets(root, [str(item) for item in config.get("referencePaths", [])]))
    if reference_mtime and report_mtime < reference_mtime:
        issues.append("视觉验证报告早于参考资源，请重新捕获并比较。")

    source_mtime = newest_mtime(tracked_source_files(root))
    if source_mtime and report_mtime < source_mtime:
        issues.append("视觉验证报告早于项目源码最新修改，请重新捕获并比较。")

    if actual_path is not None and actual_path.exists() and report_mtime < actual_path.stat().st_mtime:
        issues.append("视觉验证报告早于 actual 捕获产物，请重新运行比较脚本。")

    return issues


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

    evidence_issues = validate_evidence(root, config, report_path, report)
    if evidence_issues:
        emit_block("视觉验证证据不完整或已过期。\n" + "\n".join(f"- {issue}" for issue in evidence_issues))

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
