"""소스 지문. QA 기록과 생성물은 제외해서 기록 생성이 다음 검사를 다시 요구하지 않게 한다."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

WATCH_FILES = (
    "front/nginx.conf",
    "front/package.json",
    "front/vite.config.ts",
    "back/build.gradle",
    "compose.yaml",
    "AGENTS.md",
    "qa-policy.md",
    "qa/requirements.txt",
    "qa/input/testcases.tsv",
    "ai/requirements.txt",
    "ai/requirements-dev.txt",
)

WATCH_DIRS = (
    "front/src",
    "back/src",
    "ai/src",
    "ai/tests",
    "data/etl",
    "data/tests",
    ".github",
    "scripts",
    ".grok",
    "qa/contract",
)

SKIP_DIR_NAMES = {
    ".git",
    ".qa-venv",
    ".venv",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".gradle",
}

SKIP_PREFIXES = (
    "qa/results/",
    "qa/master_test_sheet.xlsx",
    "scripts/qa/latest.json",
    "ai/models/",
    "data/processed/",
    "data/raw/",
)


def _skipped(relative: str) -> bool:
    posix = relative.replace("\\", "/")
    if any(posix == prefix.rstrip("/") or posix.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    parts = set(posix.split("/"))
    return bool(parts & SKIP_DIR_NAMES)


def _iter_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for relative in WATCH_FILES:
        path = root / relative
        if path.is_file() and not _skipped(relative):
            found.append(path)
    for relative in WATCH_DIRS:
        directory = root / relative
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if _skipped(rel):
                continue
            found.append(path)
    return sorted(set(found))


def _porcelain(root: Path) -> str:
    try:
        raw = subprocess.check_output(
            ["git", "status", "--porcelain", "-uall"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    kept = []
    for line in raw.splitlines():
        path = line[3:] if len(line) > 3 else line
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _skipped(path.strip()):
            continue
        kept.append(line)
    return "\n".join(kept)


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(_porcelain(root).encode("utf-8"))
    digest.update(b"\0")
    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
