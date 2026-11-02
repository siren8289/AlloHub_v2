"""Write QA records under qa/results/{area}/{feature}/{YYYY-MM-DD}/.

Folder and file names are English snake_case. Report body text is Korean.
Same-day runs append by RUN_ID and never overwrite prior history.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_QA_DIR = Path(__file__).resolve().parent
if str(_QA_DIR) not in sys.path:
    sys.path.insert(0, str(_QA_DIR))

SEOUL = ZoneInfo("Asia/Seoul")

AREA_UNIT = "01_unit_integration"
AREA_WEB = "02_web_api"
AREA_SEC = "03_security_quality"
AREA_INFRA = "04_infra_deploy"

AREA_DIRS = (AREA_UNIT, AREA_WEB, AREA_SEC, AREA_INFRA)

TEST_TYPE_TO_AREA = {
    "unit": AREA_UNIT,
    "integration": AREA_UNIT,
    "api": AREA_WEB,
    "e2e": AREA_WEB,
    "security": AREA_SEC,
    "infra": AREA_INFRA,
    "performance": AREA_INFRA,
}

STATUSES = ("PASS", "FAIL", "BLOCKED", "ERROR", "NOT_RUN", "SKIPPED")

TSV_COLUMNS = (
    "RUN_ID",
    "TC_ID",
    "executed_at",
    "feature",
    "test_type",
    "tool_a",
    "tool_a_result",
    "tool_b",
    "tool_b_result",
    "final_status",
    "git_commit",
    "file",
    "function",
    "line",
    "issue_id",
    "risk_id",
    "detail",
)

_UNSAFE = re.compile(r"[^a-z0-9_]+")


def seoul_now() -> datetime:
    return datetime.now(SEOUL)


def new_run_id(when: datetime | None = None) -> str:
    clock = when or seoul_now()
    return clock.strftime("QA-%Y%m%d-%H%M%S-") + f"{clock.microsecond // 1000:03d}"


def git_commit(root: Path) -> str:
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "-uall"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty = ""
    return rev + ("+dirty" if dirty.strip() else "")


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip() or "-"


def safe_feature_name(feature: str) -> str:
    cleaned = _UNSAFE.sub("_", feature.strip().lower()).strip("_") or "unclassified"
    return cleaned[:80]


def area_of(test_type: str) -> str:
    try:
        return TEST_TYPE_TO_AREA[test_type]
    except KeyError as exc:
        raise ValueError(f"unknown test type: {test_type}") from exc


@dataclass
class Record:
    run_id: str
    tc_id: str
    executed_at: str
    feature: str
    test_type: str
    tool_a: str
    tool_a_result: str
    tool_b: str
    tool_b_result: str
    final_status: str
    git_commit: str
    file: str = "UNKNOWN"
    function: str = "UNKNOWN"
    line: str = "UNKNOWN"
    issue_id: str = "-"
    risk_id: str = "-"
    detail: str = "-"
    purpose: str = "-"
    expected: str = "-"
    actual: str = "-"
    repro: str = "-"
    cause: str = "-"
    error: str = "-"
    input_value: str = "-"
    fix_location: str = "-"
    reverify: str = "-"

    def tsv_row(self) -> list[str]:
        return [
            _cell(self.run_id),
            _cell(self.tc_id),
            _cell(self.executed_at),
            _cell(self.feature),
            _cell(self.test_type),
            _cell(self.tool_a),
            _cell(self.tool_a_result),
            _cell(self.tool_b),
            _cell(self.tool_b_result),
            _cell(self.final_status),
            _cell(self.git_commit),
            _cell(self.file),
            _cell(self.function),
            _cell(self.line),
            _cell(self.issue_id),
            _cell(self.risk_id),
            _cell(self.detail),
        ]


@dataclass
class Risk:
    run_id: str
    risk_id: str
    executed_at: str
    feature: str
    test_type: str
    severity: str
    likelihood: str
    impact: str
    action: str
    status: str
    git_commit: str
    file: str = "UNKNOWN"
    function: str = "UNKNOWN"
    line: str = "UNKNOWN"
    tc_id: str = "-"
    detail: str = "-"


def report_dir(root: Path, test_type: str, feature: str, day: str) -> Path:
    return root / "qa" / "results" / area_of(test_type) / safe_feature_name(feature) / day


def _append_md(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if new_file:
            handle.write(f"# {title}\n\n")
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")


def _append_tsv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    mode = "w" if new_file else "a"
    encoding = "utf-8-sig" if new_file else "utf-8"
    with path.open(mode, encoding=encoding, newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        if new_file:
            writer.writerow(TSV_COLUMNS)
        writer.writerows(rows)


def _record_body(record: Record) -> str:
    lines = [
        f"## {record.run_id} {record.tc_id}",
        "",
        f"- 실행 시각: {record.executed_at}",
        f"- 기능: {record.feature}",
        f"- 영역: {area_of(record.test_type)}",
        f"- 테스트 종류: {record.test_type}",
        f"- 1차 검증: {record.tool_a} / {record.tool_a_result}",
        f"- 2차 검증: {record.tool_b} / {record.tool_b_result}",
        f"- 최종 상태: {record.final_status}",
        f"- Git Commit: {record.git_commit}",
        f"- 파일: {record.file}",
        f"- 함수: {record.function}",
        f"- 줄 번호: {record.line}",
        f"- ISSUE_ID: {record.issue_id}",
        f"- RISK_ID: {record.risk_id}",
        f"- 목적: {record.purpose}",
        f"- 입력값: {record.input_value}",
        f"- 기대 결과: {record.expected}",
        f"- 실제 결과: {record.actual}",
        f"- 오류: {record.error}",
        f"- 재현: {record.repro}",
        f"- 원인: {record.cause}",
        f"- 수정 위치: {record.fix_location}",
        f"- 재검증: {record.reverify}",
        f"- 근거: {record.detail}",
        "",
    ]
    return "\n".join(lines)


def _bucket(status: str) -> str:
    if status == "PASS":
        return "pass.md"
    return "fail.md"


def write_run(
    root: Path,
    day: str,
    records: list[Record],
    risks: list[Risk],
) -> list[Path]:
    """Create folders only for executed area/feature pairs and append results."""
    from sheet_writer import write_feature_sheet, write_master_sheet

    written: list[Path] = []
    by_key: dict[tuple[str, str], list[Record]] = {}
    for record in records:
        key = (record.test_type, record.feature)
        by_key.setdefault(key, []).append(record)
    risk_by_key: dict[tuple[str, str], list[Risk]] = {}
    for risk in risks:
        key = (risk.test_type, risk.feature)
        risk_by_key.setdefault(key, []).append(risk)

    for key in sorted(set(by_key) | set(risk_by_key), key=lambda item: (area_of(item[0]), item[1])):
        test_type, feature = key
        folder = report_dir(root, test_type, feature, day)
        grouped: dict[str, list[Record]] = {"pass.md": [], "fail.md": []}
        for record in by_key.get(key, []):
            grouped[_bucket(record.final_status)].append(record)
        for name, items in grouped.items():
            if not items:
                continue
            path = folder / name
            title = "PASS" if name == "pass.md" else "FAIL"
            _append_md(path, title, "".join(_record_body(item) for item in items))
            written.append(path)
        type_risks = risk_by_key.get(key, [])
        if type_risks:
            chunks = []
            for risk in type_risks:
                chunks.append(
                    "\n".join(
                        [
                            f"## {risk.run_id} {risk.risk_id}",
                            "",
                            f"- 실행 시각: {risk.executed_at}",
                            f"- 기능: {risk.feature}",
                            f"- 영역: {area_of(risk.test_type)}",
                            f"- 테스트 종류: {risk.test_type}",
                            f"- 관련 TC_ID: {risk.tc_id}",
                            f"- 심각도: {risk.severity}",
                            f"- 발생 가능성: {risk.likelihood}",
                            f"- 영향: {risk.impact}",
                            f"- 권장 조치: {risk.action}",
                            f"- 처리 상태: {risk.status}",
                            f"- Git Commit: {risk.git_commit}",
                            f"- 파일: {risk.file}",
                            f"- 함수: {risk.function}",
                            f"- 줄 번호: {risk.line}",
                            f"- 내용: {risk.detail}",
                            "",
                        ]
                    )
                )
            path = folder / "risk.md"
            _append_md(path, "RISK", "".join(chunks))
            written.append(path)
        type_records = by_key.get(key, [])
        if type_records:
            path = folder / "summary.tsv"
            _append_tsv(path, [record.tsv_row() for record in type_records])
            written.append(path)
            written.append(write_feature_sheet(folder, type_records))
        elif not (folder / "summary.tsv").exists():
            path = folder / "summary.tsv"
            _append_tsv(path, [])
            written.append(path)
            written.append(write_feature_sheet(folder, []))
        for name, title in (("pass.md", "PASS"), ("fail.md", "FAIL"), ("risk.md", "RISK")):
            path = folder / name
            if not path.exists() or path.stat().st_size == 0:
                _append_md(path, title, "")
                written.append(path)

    written.append(write_master_sheet(root, records, risks))
    return written


def verify_history_append(root: Path) -> None:
    """Append twice in a temp tree and assert the first RUN_ID remains."""
    day = "2099-01-01"
    first = Record(
        run_id="QA-APPEND-1",
        tc_id="TC-UNIT-QA-001",
        executed_at="2099-01-01T00:00:00+09:00",
        feature="qa_history",
        test_type="unit",
        tool_a="pytest",
        tool_a_result="PASS",
        tool_b="independent_unit.py",
        tool_b_result="PASS",
        final_status="PASS",
        git_commit="abc",
        file="scripts/qa/report_store.py",
        function="verify_history_append",
        line="1",
        detail="first-run-marker",
        purpose="append keeps history",
        expected="both run ids",
        actual="first",
    )
    second = Record(
        run_id="QA-APPEND-2",
        tc_id="TC-UNIT-QA-001",
        executed_at="2099-01-01T00:00:01+09:00",
        feature="qa_history",
        test_type="unit",
        tool_a="pytest",
        tool_a_result="PASS",
        tool_b="independent_unit.py",
        tool_b_result="PASS",
        final_status="PASS",
        git_commit="abc",
        file="scripts/qa/report_store.py",
        function="verify_history_append",
        line="1",
        detail="second-run-marker",
        purpose="append keeps history",
        expected="both run ids",
        actual="second",
    )
    write_run(root, day, [first], [])
    snapshot = (report_dir(root, "unit", "qa_history", day) / "pass.md").read_text(encoding="utf-8")
    write_run(root, day, [second], [])
    folder = report_dir(root, "unit", "qa_history", day)
    pass_md = (folder / "pass.md").read_text(encoding="utf-8")
    tsv = (folder / "summary.tsv").read_text(encoding="utf-8-sig")
    if "QA-APPEND-1" not in pass_md or "first-run-marker" not in pass_md:
        raise AssertionError("first RUN_ID was overwritten")
    if snapshot.split("QA-APPEND-1", 1)[1] not in pass_md:
        raise AssertionError("first section changed")
    if "QA-APPEND-2" not in pass_md or "second-run-marker" not in pass_md:
        raise AssertionError("second RUN_ID missing")
    if tsv.count("TC-UNIT-QA-001") != 2:
        raise AssertionError(f"tsv rows={tsv.count('TC-UNIT-QA-001')}")
    if not tsv.startswith("RUN_ID\t"):
        raise AssertionError("tsv header missing after bom")
    header_count = sum(1 for line in tsv.splitlines() if line.startswith("RUN_ID\t"))
    if header_count != 1:
        raise AssertionError("tsv header rewritten")
    if not (folder / "test_sheet.xlsx").is_file():
        raise AssertionError("feature test_sheet.xlsx missing")
    master = root / "qa" / "master_test_sheet.xlsx"
    if not master.is_file():
        raise AssertionError("master_test_sheet.xlsx missing")
