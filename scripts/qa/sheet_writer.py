"""Write per-feature test_sheet.xlsx and qa/master_test_sheet.xlsx without AI."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from report_store import AREA_DIRS, Record, Risk, TSV_COLUMNS, area_of

HISTORY_COLUMNS = (
    "RUN_ID",
    "area",
    "feature",
    "TC_ID",
    "final_status",
    "tool_a_result",
    "tool_b_result",
    "executed_at",
    "git_commit",
    "detail",
)

OVERVIEW_COLUMNS = (
    "area",
    "feature",
    "PASS",
    "FAIL",
    "ERROR",
    "BLOCKED",
    "NOT_RUN",
    "SKIPPED",
    "OPEN_HIGH_CRITICAL",
    "last_run_id",
    "last_executed_at",
)


def _ensure_header(sheet: Worksheet, columns: tuple[str, ...]) -> None:
    if sheet.max_row == 1 and all(cell.value is None for cell in sheet[1]):
        sheet.append(list(columns))
        return
    if sheet.max_row == 0:
        sheet.append(list(columns))
        return
    existing = [cell.value for cell in sheet[1]]
    if existing != list(columns):
        if sheet.max_row == 1 and not any(existing):
            for index, name in enumerate(columns, start=1):
                sheet.cell(1, index, name)


def _append_rows(path: Path, sheet_name: str, columns: tuple[str, ...], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        book = load_workbook(path)
        if sheet_name in book.sheetnames:
            sheet = book[sheet_name]
        else:
            sheet = book.create_sheet(sheet_name)
    else:
        book = Workbook()
        sheet = book.active
        sheet.title = sheet_name
    _ensure_header(sheet, columns)
    for row in rows:
        sheet.append(row)
    book.save(path)


def write_feature_sheet(folder: Path, records: list[Record]) -> Path:
    path = folder / "test_sheet.xlsx"
    rows = [record.tsv_row() for record in records]
    _append_rows(path, "TC", TSV_COLUMNS, rows)
    return path


def _status_counts(records: list[Record]) -> dict[str, int]:
    counts = {name: 0 for name in ("PASS", "FAIL", "ERROR", "BLOCKED", "NOT_RUN", "SKIPPED")}
    for record in records:
        if record.final_status in counts:
            counts[record.final_status] += 1
    return counts


def write_master_sheet(root: Path, records: list[Record], risks: list[Risk]) -> Path:
    """Single top-level master workbook. Do not create a second overview Excel."""
    path = root / "qa" / "master_test_sheet.xlsx"
    history_rows: list[list[object]] = []
    for record in records:
        history_rows.append(
            [
                record.run_id,
                area_of(record.test_type),
                record.feature,
                record.tc_id,
                record.final_status,
                record.tool_a_result,
                record.tool_b_result,
                record.executed_at,
                record.git_commit,
                record.detail,
            ]
        )
    _append_rows(path, "history", HISTORY_COLUMNS, history_rows)

    by_key: dict[tuple[str, str], list[Record]] = {}
    for record in records:
        by_key.setdefault((area_of(record.test_type), record.feature), []).append(record)
    risk_by_key: dict[tuple[str, str], list[Risk]] = {}
    for risk in risks:
        risk_by_key.setdefault((area_of(risk.test_type), risk.feature), []).append(risk)

    overview_rows: list[list[object]] = []
    for area in AREA_DIRS:
        features = sorted({feature for (area_name, feature) in by_key if area_name == area})
        if not features:
            overview_rows.append([area, "-", 0, 0, 0, 0, 0, 0, 0, "-", "-"])
            continue
        for feature in features:
            group = by_key[(area, feature)]
            counts = _status_counts(group)
            high = sum(
                1
                for risk in risk_by_key.get((area, feature), [])
                if risk.severity in ("HIGH", "CRITICAL") and risk.status == "OPEN"
            )
            last = max(group, key=lambda item: item.executed_at)
            overview_rows.append(
                [
                    area,
                    feature,
                    counts["PASS"],
                    counts["FAIL"],
                    counts["ERROR"],
                    counts["BLOCKED"],
                    counts["NOT_RUN"],
                    counts["SKIPPED"],
                    high,
                    last.run_id,
                    last.executed_at,
                ]
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        book = load_workbook(path)
    else:
        book = Workbook()
        book.active.title = "history"
    if "overview" in book.sheetnames:
        del book["overview"]
    sheet = book.create_sheet("overview", 0)
    sheet.append(list(OVERVIEW_COLUMNS))
    for row in overview_rows:
        sheet.append(row)
    if "history" not in book.sheetnames:
        book.create_sheet("history")
    book.save(path)
    return path
