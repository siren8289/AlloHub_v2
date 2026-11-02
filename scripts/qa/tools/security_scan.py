"""도구 A. 시크릿 리터럴, 삼켜진 예외, eval·innerHTML·SQL 이어붙이기를 본다."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

SKIP_DIRS = {
    ".git",
    ".qa-venv",
    ".venv",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".gradle",
    "qa",
    "models",
}
SCAN_SUFFIXES = {
    ".py",
    ".java",
    ".ts",
    ".tsx",
    ".js",
    ".yml",
    ".yaml",
    ".gradle",
    ".conf",
    ".sh",
    ".html",
}

SECRET_RES = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"""(?i)(?:api_key|secret_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"""),
)
EVAL_RE = re.compile(r"(?<![\w.])eval\s*\(")
INNER_RE = re.compile(r"\.innerHTML\s*=")
SQL_RES = (
    re.compile(r"""execute\s*\(\s*f['\"]"""),
    re.compile(r"""execute\s*\(\s*[^)]*\+"""),
)
EXCEPT_RE = re.compile(r"^\s*except Exception\s*:")
PASS_RE = re.compile(r"^\s*pass\s*(#.*)?$")
DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _iter_files() -> list[Path]:
    found = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.stat().st_size > 1_000_000:
            continue
        found.append(path)
    return found


def _function_at(lines: list[str], index: int) -> str:
    for cursor in range(index, -1, -1):
        match = DEF_RE.match(lines[cursor])
        if match:
            return match.group(1)
    return "UNKNOWN"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _finding(path: Path, line_no: int, function: str, text: str) -> dict:
    return {
        "file": _rel(path),
        "line": str(line_no),
        "function": function,
        "text": text.strip()[:240],
    }


def scan() -> dict:
    secrets = []
    swallowed = []
    dangerous = []
    for path in _iter_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for index, line in enumerate(lines):
            function = _function_at(lines, index)
            if any(pattern.search(line) for pattern in SECRET_RES):
                secrets.append(_finding(path, index + 1, function, line))
            if EVAL_RE.search(line) or INNER_RE.search(line) or any(
                pattern.search(line) for pattern in SQL_RES
            ):
                dangerous.append(_finding(path, index + 1, function, line))
            if EXCEPT_RE.match(line):
                window = lines[index + 1 : index + 6]
                for offset, follow in enumerate(window, start=1):
                    if follow.strip() and not follow.strip().startswith("#"):
                        if PASS_RE.match(follow):
                            swallowed.append(
                                _finding(path, index + 1, function, line + " / pass")
                            )
                        break
                    if PASS_RE.match(follow) and offset:
                        swallowed.append(_finding(path, index + 1, function, line + " / pass"))
                        break

    compose = ROOT / "compose.yaml"
    compose_line = "UNKNOWN"
    image = ""
    if compose.is_file():
        for number, line in enumerate(compose.read_text(encoding="utf-8").splitlines(), start=1):
            if "postgres:16-alpine" in line:
                compose_line = str(number)
                image = line.strip()
                break

    risks = []
    for item in swallowed:
        high = item["function"] == "query_pgvector_if_available"
        risks.append(
            {
                "risk_id": "RISK-SEC-001" if high else f"RISK-SEC-PASS-{item['file'].replace('/', '-')}-{item['line']}",
                "severity": "HIGH" if high else "MEDIUM",
                "likelihood": "높음" if high else "중간",
                "feature": "disclosure_search" if high else "exception_handling",
                "function": item["function"],
                "file": item["file"],
                "line": item["line"],
                "tc_id": "TC-SEC-002",
                "impact": (
                    "DB 또는 pgvector 실패가 버려지고 메모리 검색 결과만 반환된다. "
                    f"compose 이미지는 {image or 'UNKNOWN'} (compose.yaml:{compose_line})."
                    if high
                    else "예외를 삼키고 폴백으로 넘어가 실패가 호출자에게 전달되지 않는다."
                ),
                "action": "예외를 기록하고 실패를 구분할 것. pgvector가 필요하면 이미지에 확장을 넣을 것."
                if high
                else "삼킨 예외를 로그에 남기고, 폴백인지 실패인지 응답에 드러낼 것.",
                "detail": item["text"],
            }
        )
    gradle = ROOT / "back" / "build.gradle"
    if gradle.is_file() and "spring-boot-starter-security" not in gradle.read_text(encoding="utf-8"):
        gradle_line = "UNKNOWN"
        for number, text in enumerate(gradle.read_text(encoding="utf-8").splitlines(), start=1):
            if "dependencies" in text:
                gradle_line = str(number)
                break
        risks.append(
            {
                "risk_id": "RISK-SEC-004",
                "severity": "MEDIUM",
                "likelihood": "중간",
                "feature": "authentication",
                "function": "UNKNOWN",
                "file": "back/build.gradle",
                "line": gradle_line,
                "tc_id": "-",
                "impact": "출자자 이름이 인증 없이 저장될 수 있다. 인증 요구사항은 명시되어 있지 않다.",
                "action": "인증 요구가 확정되면 Spring Security와 인가 규칙을 추가할 것.",
                "detail": "build.gradle에 spring-boot-starter-security가 없다.",
            }
        )

    def status(items: list[dict]) -> str:
        return "FAIL" if items else "PASS"

    return {
        "TC-SEC-001": {"status": status(secrets), "findings": secrets, "feature": "secrets"},
        "TC-SEC-002": {"status": status(swallowed), "findings": swallowed, "feature": "swallowed_exception"},
        "TC-SEC-003": {"status": status(dangerous), "findings": dangerous, "feature": "code_execution"},
        "risks": risks,
    }


def main() -> int:
    json.dump(scan(), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
