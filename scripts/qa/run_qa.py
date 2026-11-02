"""QA·Security 실행기.

필수 TC는 서로 다른 도구 두 개가 모두 PASS일 때만 PASS다.
NOT_RUN, ERROR, SKIPPED는 PASS로 기록하지 않는다.
결과는 qa/{영역}/{기능}/{날짜}/ 에 기록한다. 실행하지 않은 기능 폴더는 만들지 않는다.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "qa") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "qa"))

from fingerprint import source_fingerprint  # noqa: E402
from report_store import Record, Risk, area_of, git_commit, new_run_id, seoul_now, write_run  # noqa: E402

PY_MAP = {
    "test_TC_UNIT_001_danger_on_default": "TC-UNIT-001",
    "test_TC_UNIT_002_stable_when_clean": "TC-UNIT-002",
    "test_TC_UNIT_003_warning_at_threshold": "TC-UNIT-003",
    "test_TC_UNIT_004_warning_on_reduction_only": "TC-UNIT-004",
    "test_TC_UNIT_005_normalize_strips_company_marks": "TC-UNIT-005",
    "test_TC_UNIT_006_find_samsung": "TC-UNIT-006",
    "test_TC_UNIT_007_missing_company_is_404": "TC-UNIT-007",
    "test_TC_UNIT_008_empty_company_is_422": "TC-UNIT-008",
    "test_to_number": "TC-UNIT-009",
    "test_count_by_crno_skips_empty_number": "TC-UNIT-010",
    "test_as_list_and_shorten": "TC-UNIT-011",
    "test_build_companies_joins_disclosure_and_label": "TC-UNIT-012",
    "test_TC_UNIT_QA_001_append_preserves_history": "TC-UNIT-QA-001",
}

JAVA_MAP = {
    "com.allohub.allocation.AllocationCalculatorTest.lastInvestorTakesRemainder": "TC-UNIT-J-001",
    "com.allohub.allocation.AllocationCalculatorTest.evenSplit": "TC-UNIT-J-002",
    "com.allohub.screen.ScreenControllerTest.blankNameReturns400": "TC-API-001",
    "com.allohub.allocation.AllocationControllerTest.ratioMustSumTo100": "TC-API-002",
    "com.allohub.global.HealthControllerTest.healthOk": "TC-API-003",
}

UNIT_FEATURES = {
    "TC-UNIT-001": "risk_grade",
    "TC-UNIT-002": "risk_grade",
    "TC-UNIT-003": "risk_grade",
    "TC-UNIT-004": "risk_grade",
    "TC-UNIT-005": "company_name_normalize",
    "TC-UNIT-006": "company_search",
    "TC-UNIT-007": "company_search",
    "TC-UNIT-008": "company_search",
    "TC-UNIT-009": "number_convert",
    "TC-UNIT-010": "disclosure_count",
    "TC-UNIT-011": "fetch_row_normalize",
    "TC-UNIT-012": "company_table_join",
    "TC-UNIT-QA-001": "qa_history",
    "TC-UNIT-J-001": "allocation_calc",
    "TC-UNIT-J-002": "allocation_calc",
}

API_FEATURES = {
    "TC-API-001": "company_screen_api",
    "TC-API-002": "allocation_api",
    "TC-API-003": "health_check",
}

SEC_FEATURES = {
    "TC-SEC-001": "secrets",
    "TC-SEC-002": "swallowed_exception",
    "TC-SEC-003": "code_execution",
}

INFRA_FEATURES = {
    "TC-INFRA-001": "docker_deploy",
    "TC-INFRA-002": "github_actions_ci",
}

COMPOSE_CMD = "docker compose -f compose.yaml config --quiet"
COMPOSE_CHECK_CMD = "python scripts/qa/tools/compose_cross_check.py"
CI_FILE_CMD = "python scripts/qa/tools/ci_workflow_check.py --tool a"
CI_CROSS_CMD = "python scripts/qa/tools/ci_workflow_check.py --tool b"

PLACE = {
    "TC-UNIT-001": ("ai/src/scoring/rules.py", "grade_of", "def grade_of"),
    "TC-UNIT-002": ("ai/src/scoring/rules.py", "grade_of", "def grade_of"),
    "TC-UNIT-003": ("ai/src/scoring/rules.py", "grade_of", "def grade_of"),
    "TC-UNIT-004": ("ai/src/scoring/rules.py", "grade_of", "def grade_of"),
    "TC-UNIT-005": ("ai/src/scoring/company.py", "normalize_name", "def normalize_name"),
    "TC-UNIT-006": ("ai/src/scoring/company.py", "find_company", "def find_company"),
    "TC-UNIT-007": ("ai/src/scoring/company.py", "find_company", "def find_company"),
    "TC-UNIT-008": ("ai/src/scoring/company.py", "find_company", "def find_company"),
    "TC-UNIT-009": ("data/etl/transform.py", "to_number", "def to_number"),
    "TC-UNIT-010": ("data/etl/transform.py", "count_by_crno", "def count_by_crno"),
    "TC-UNIT-011": ("data/etl/fetch.py", "as_list", "def as_list"),
    "TC-UNIT-012": ("data/etl/transform.py", "build_companies", "def build_companies"),
    "TC-UNIT-QA-001": ("scripts/qa/report_store.py", "verify_history_append", "def verify_history_append"),
    "TC-UNIT-J-001": (
        "back/src/main/java/com/allohub/allocation/AllocationCalculator.java",
        "split",
        "List<Long> split",
    ),
    "TC-UNIT-J-002": (
        "back/src/main/java/com/allohub/allocation/AllocationCalculator.java",
        "split",
        "List<Long> split",
    ),
    "TC-API-001": (
        "back/src/main/java/com/allohub/screen/controller/ScreenController.java",
        "create",
        "public CompanyScreen create",
    ),
    "TC-API-002": (
        "back/src/main/java/com/allohub/allocation/service/AllocationService.java",
        "allocate",
        "public Allocation allocate",
    ),
    "TC-API-003": ("back/src/main/java/com/allohub/global/HealthController.java", "health", "Map<String, String> health"),
    "TC-SEC-001": ("UNKNOWN", "UNKNOWN", ""),
    "TC-SEC-002": (
        "ai/src/features/disclosure_rag_001/disclosure_search/service.py",
        "query_pgvector_if_available",
        "def query_pgvector_if_available",
    ),
    "TC-SEC-003": ("UNKNOWN", "UNKNOWN", ""),
    "TC-INFRA-001": ("compose.yaml", "services", "services:"),
    "TC-INFRA-002": (".github/workflows/ci.yml", "jobs", "jobs:"),
}

PYTEST_CMD = "python -m pytest qa/contract/test_contracts.py data/tests --junitxml"
INDEPENDENT_CMD = "python scripts/qa/tools/independent_unit.py"
GRADLE_CMD = "./gradlew test"
JAVA_CMD = "java AllocationCrossCheck"
BOOT_CMD = "./gradlew --no-daemon bootRun --args=--server.port=18080"
SCAN_CMD = "python scripts/qa/tools/security_scan.py"
BANDIT_CMD = "python -m bandit -r ai/src data -f json"
API_PORT = 18080


def python_bin() -> str:
    """venv의 실행 파일 경로를 쓴다. 실제 바이너리로 resolve하면 site-packages를 잃는다."""
    venv_python = ROOT / ".qa-venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def run_cmd(
    command: list[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )


def find_line(relative: str, signature: str) -> str:
    if not relative or relative == "UNKNOWN" or not signature:
        return "UNKNOWN"
    path = ROOT / relative
    if not path.is_file():
        return "UNKNOWN"
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if signature in line:
            return str(number)
    return "UNKNOWN"


def place_of(tc_id: str, override: dict | None = None) -> tuple[str, str, str]:
    if override:
        return (
            str(override.get("file") or "UNKNOWN"),
            str(override.get("function") or "UNKNOWN"),
            str(override.get("line") or "UNKNOWN"),
        )
    relative, function, signature = PLACE.get(tc_id, ("UNKNOWN", "UNKNOWN", ""))
    return relative, function, find_line(relative, signature)


def combine(left: str, right: str) -> str:
    if left == "FAIL" or right == "FAIL":
        return "FAIL"
    if left == "ERROR" or right == "ERROR":
        return "ERROR"
    if left == "BLOCKED" or right == "BLOCKED":
        return "BLOCKED"
    if left == "NOT_RUN" or right == "NOT_RUN":
        return "NOT_RUN"
    if left == "SKIPPED" or right == "SKIPPED":
        return "SKIPPED"
    if left == "PASS" and right == "PASS":
        return "PASS"
    return "ERROR"


def parse_junit(directory: Path) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    if not directory.is_dir():
        return found
    for path in directory.glob("TEST-*.xml"):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        for case in tree.findall(".//testcase"):
            name = case.get("name") or ""
            if name.endswith("()"):
                name = name[:-2]
            key = f"{case.get('classname')}.{name}"
            failure = case.find("failure")
            error = case.find("error")
            if failure is not None:
                found[key] = ("FAIL", (failure.get("message") or failure.text or "failure")[:400])
            elif error is not None:
                found[key] = ("ERROR", (error.get("message") or error.text or "error")[:400])
            else:
                found[key] = ("PASS", "junit")
    return found


def parse_pytest_xml(path: Path) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    if not path.is_file():
        return found
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return found
    for case in tree.findall(".//testcase"):
        name = case.get("name") or ""
        if name.endswith("()"):
            name = name[:-2]
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        if failure is not None:
            status, detail = "FAIL", (failure.get("message") or "failure")[:400]
        elif error is not None:
            status, detail = "ERROR", (error.get("message") or "error")[:400]
        elif skipped is not None:
            status, detail = "SKIPPED", (skipped.get("message") or "skipped")[:400]
        else:
            status, detail = "PASS", "pytest"
        found[name] = (status, detail)
    return found


def tool_pair(
    tc_id: str,
    feature: str,
    test_type: str,
    tool_a: str,
    a_status: str,
    a_detail: str,
    tool_b: str,
    b_status: str,
    b_detail: str,
    stamp: str,
    run_id: str,
    commit: str,
    override: dict | None = None,
    risk_id: str = "-",
    purpose: str = "",
    expected: str = "",
    actual: str = "",
    repro: str = "",
    cause: str = "",
    error: str = "",
    input_value: str = "",
) -> Record:
    final = combine(a_status, b_status)
    file_name, function, line = place_of(tc_id, override if override and override.get("file") else None)
    if final == "FAIL" and not cause:
        cause = a_detail if a_status == "FAIL" else b_detail
    if final != "PASS" and not error:
        error = " | ".join(part for part in (a_detail if a_status != "PASS" else "", b_detail if b_status != "PASS" else "") if part)
    return Record(
        run_id=run_id,
        tc_id=tc_id,
        executed_at=stamp,
        feature=feature,
        test_type=test_type,
        tool_a=tool_a,
        tool_a_result=a_status,
        tool_b=tool_b,
        tool_b_result=b_status,
        final_status=final,
        git_commit=commit,
        file=file_name,
        function=function,
        line=line,
        risk_id=risk_id,
        detail=f"A[{a_status}] {a_detail} || B[{b_status}] {b_detail}",
        purpose=purpose or feature,
        expected=expected or "두 도구 모두 PASS",
        actual=final,
        repro=repro or f"{tool_a} ; {tool_b}",
        cause=cause or "-",
        error=error or "-",
        input_value=input_value or "-",
        fix_location="수정하지 않음" if final in ("FAIL", "ERROR", "BLOCKED") else "-",
        reverify="이번 실행이 현재 검증" if final != "PASS" else "두 도구 일치",
    )


def run_python_unit(stamp: str, run_id: str, commit: str) -> list[Record]:
    xml_path = Path("/tmp/allohub-qa-pytest.xml")
    if xml_path.exists():
        xml_path.unlink()
    log("pytest (tool A)")
    pytest = run_cmd(
        [
            python_bin(),
            "-m",
            "pytest",
            "qa/contract/test_contracts.py",
            "data/tests",
            "-q",
            f"--junitxml={xml_path}",
        ],
        ROOT,
        timeout=300,
    )
    parsed = parse_pytest_xml(xml_path)
    if not parsed and pytest.returncode != 0:
        log(pytest.stdout[-500:] + pytest.stderr[-500:])
    log("independent_unit.py (tool B)")
    independent = run_cmd([python_bin(), "scripts/qa/tools/independent_unit.py"], ROOT, timeout=180)
    by_id: dict[str, dict] = {}
    try:
        payload = json.loads(independent.stdout)
        if isinstance(payload, list):
            by_id = {item["tc_id"]: item for item in payload}
    except json.JSONDecodeError:
        by_id = {}
    records = []
    for tc_id, feature in UNIT_FEATURES.items():
        if tc_id.startswith("TC-UNIT-J"):
            continue
        pytest_name = next((name for name, mapped in PY_MAP.items() if mapped == tc_id), "")
        if pytest_name in parsed:
            a_status, a_detail = parsed[pytest_name]
        elif not parsed:
            a_status, a_detail = "ERROR", (pytest.stderr or pytest.stdout or "pytest produced no results")[-300:]
        else:
            a_status, a_detail = "NOT_RUN", "pytest 결과에 해당 TC가 없음"
        item = by_id.get(tc_id)
        if item:
            b_status, b_detail = item.get("status", "ERROR"), str(item.get("detail", ""))[:300]
            override = item
        elif independent.returncode != 0 or not by_id:
            b_status, b_detail = "ERROR", (independent.stderr or independent.stdout or "independent_unit 실패")[-300:]
            override = None
        else:
            b_status, b_detail = "NOT_RUN", "independent_unit 결과에 해당 TC가 없음"
            override = None
        records.append(
            tool_pair(
                tc_id,
                feature,
                "unit",
                PYTEST_CMD,
                a_status,
                a_detail,
                INDEPENDENT_CMD,
                b_status,
                b_detail,
                stamp,
                run_id,
                commit,
                override=override,
                purpose="계약 조건을 두 실행기로 확인",
            )
        )
    for name, (status, detail) in parsed.items():
        if name in PY_MAP or status == "PASS":
            continue
        records.append(
            tool_pair(
                "TC-PYTEST-" + name[:40],
                "pytest_extra_fail",
                "unit",
                PYTEST_CMD,
                status,
                detail,
                INDEPENDENT_CMD,
                "NOT_RUN",
                "매핑된 독립 검사가 없음",
                stamp,
                run_id,
                commit,
                purpose="pytest에서만 실패한 검사",
            )
        )
    return records


def run_java_unit(stamp: str, run_id: str, commit: str, junit: dict[str, tuple[str, str]]) -> list[Record]:
    log("AllocationCrossCheck.java (tool B)")
    classes = ROOT / "back" / "build" / "classes" / "java" / "main"
    out = Path("/tmp/allohub-qa-java")
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT / "scripts" / "qa" / "tools" / "AllocationCrossCheck.java"
    compiled = run_cmd(
        ["javac", "-encoding", "UTF-8", "-cp", str(classes), "-d", str(out), str(source)],
        ROOT,
        timeout=120,
    )
    java_results: dict[str, tuple[str, str]] = {}
    if compiled.returncode != 0:
        message = (compiled.stderr or compiled.stdout or "javac failed")[-400:]
        for tc_id in ("TC-UNIT-J-001", "TC-UNIT-J-002"):
            java_results[tc_id] = ("ERROR", message)
    else:
        ran = run_cmd(
            ["java", "-cp", str(out) + os.pathsep + str(classes), "AllocationCrossCheck"],
            ROOT,
            timeout=60,
        )
        if ran.returncode != 0 and not ran.stdout.strip():
            message = (ran.stderr or "java failed")[-400:]
            for tc_id in ("TC-UNIT-J-001", "TC-UNIT-J-002"):
                java_results[tc_id] = ("ERROR", message)
        else:
            for line in ran.stdout.splitlines():
                parts = line.split(" ", 2)
                if len(parts) >= 2 and parts[0].startswith("TC-"):
                    java_results[parts[0]] = (parts[1], line[:300])
    records = []
    for key, tc_id in JAVA_MAP.items():
        if not tc_id.startswith("TC-UNIT-J"):
            continue
        if not junit:
            a_status, a_detail = "ERROR", "Gradle 테스트 결과 XML이 없음"
        elif key in junit:
            a_status, a_detail = junit[key]
        else:
            a_status, a_detail = "NOT_RUN", "JUnit 결과에 해당 메서드가 없음"
        b_status, b_detail = java_results.get(tc_id, ("NOT_RUN", "독립 자바 결과에 없음"))
        records.append(
            tool_pair(
                tc_id,
                UNIT_FEATURES[tc_id],
                "unit",
                GRADLE_CMD,
                a_status,
                a_detail,
                JAVA_CMD,
                b_status,
                b_detail,
                stamp,
                run_id,
                commit,
                purpose="원 단위 배분을 JUnit과 독립 main으로 확인",
                expected="TC-UNIT-J-001=[33,33,34], TC-UNIT-J-002=[60000,40000]",
            )
        )
    for key, (status, detail) in junit.items():
        if key in JAVA_MAP or status == "PASS":
            continue
        records.append(
            tool_pair(
                "TC-GRADLE-" + key.split(".")[-1][:40],
                "gradle_extra_fail",
                "unit",
                GRADLE_CMD,
                status,
                detail,
                JAVA_CMD,
                "NOT_RUN",
                "독립 도구에 대응 검사가 없음",
                stamp,
                run_id,
                commit,
                purpose="Gradle에서만 실패한 검사",
            )
        )
    return records


def _http(method: str, url: str, body: dict | None = None) -> tuple[str, int | None, dict | str]:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode()
            payload: dict | str = json.loads(raw) if raw else {}
            return "PASS", response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = raw[:300]
        return "HTTP", exc.code, payload
    except Exception as exc:  # 연결 실패는 검사 통과가 아니다.
        return "ERROR", None, f"{type(exc).__name__}: {exc}"


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _stop_group(proc: subprocess.Popen[str] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=10)
    deadline = time.time() + 15
    while time.time() < deadline and _port_open(API_PORT):
        time.sleep(0.5)


def run_api(stamp: str, run_id: str, commit: str, junit: dict[str, tuple[str, str]]) -> list[Record]:
    live: dict[str, tuple[str, str]] = {}
    if _port_open(API_PORT):
        message = f"127.0.0.1:{API_PORT} 이 이미 사용 중이라 독립 API 검사를 시작하지 않음"
        for tc_id in API_FEATURES:
            live[tc_id] = ("ERROR", message)
        proc = None
    else:
        log("bootRun (tool B)")
        log_path = Path("/tmp/allohub-boot.log")
        handle = log_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            ["./gradlew", "--no-daemon", "bootRun", f"--args=--server.port={API_PORT}"],
            cwd=ROOT / "back",
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
        deadline = time.time() + 180
        up = False
        try:
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                kind, status, _payload = _http("GET", f"http://127.0.0.1:{API_PORT}/api/health")
                if kind == "PASS" and status == 200:
                    up = True
                    break
                time.sleep(2)
            if not up:
                tail = log_path.read_text(encoding="utf-8", errors="replace")[-500:]
                message = "bootRun이 180초 안에 /api/health를 열지 못함 " + tail
                for tc_id in API_FEATURES:
                    live[tc_id] = ("ERROR", message)
            else:
                kind, status, payload = _http("GET", f"http://127.0.0.1:{API_PORT}/api/health")
                ok = kind == "PASS" and status == 200 and isinstance(payload, dict) and payload.get("status") == "ok"
                live["TC-API-003"] = ("PASS" if ok else "FAIL", f"status={status} body={payload}")
                kind, status, payload = _http(
                    "POST",
                    f"http://127.0.0.1:{API_PORT}/api/screens",
                    {"companyName": ""},
                )
                code = payload.get("errorCode") if isinstance(payload, dict) else ""
                ok = status == 400 and code == "VALIDATION_ERROR"
                live["TC-API-001"] = ("PASS" if ok else "FAIL", f"status={status} body={payload}")
                kind, status, payload = _http(
                    "POST",
                    f"http://127.0.0.1:{API_PORT}/api/allocations",
                    {
                        "companyName": "삼성전자",
                        "totalAmount": 100000,
                        "investors": [
                            {"name": "김출자", "ratio": 60},
                            {"name": "이출자", "ratio": 30},
                        ],
                    },
                )
                code = payload.get("errorCode") if isinstance(payload, dict) else ""
                ok = status == 400 and code == "BAD_REQUEST"
                live["TC-API-002"] = ("PASS" if ok else "FAIL", f"status={status} body={payload}")
        finally:
            _stop_group(proc)
            handle.close()
    records = []
    expectations = {
        "TC-API-001": 'POST /api/screens {"companyName":""} -> 400 VALIDATION_ERROR',
        "TC-API-002": "POST /api/allocations ratio 60+30 -> 400 BAD_REQUEST",
        "TC-API-003": "GET /api/health -> 200 status=ok",
    }
    junit_keys = {tc: key for key, tc in JAVA_MAP.items() if tc.startswith("TC-API")}
    for tc_id, feature in API_FEATURES.items():
        key = junit_keys[tc_id]
        if not junit:
            a_status, a_detail = "ERROR", "Gradle 테스트 결과 XML이 없음"
        elif key in junit:
            a_status, a_detail = junit[key]
        else:
            a_status, a_detail = "NOT_RUN", "JUnit 결과에 해당 메서드가 없음"
        b_status, b_detail = live.get(tc_id, ("NOT_RUN", "독립 HTTP 결과 없음"))
        records.append(
            tool_pair(
                tc_id,
                feature,
                "api",
                GRADLE_CMD,
                a_status,
                a_detail,
                BOOT_CMD,
                b_status,
                b_detail,
                stamp,
                run_id,
                commit,
                purpose="MockMvc와 기동한 서버를 교차 확인",
                expected=expectations[tc_id],
                input_value=expectations[tc_id],
            )
        )
    return records


def run_gradle() -> dict[str, tuple[str, str]]:
    log("gradlew test (tool A)")
    result = run_cmd(["./gradlew", "test"], ROOT / "back", timeout=600)
    junit = parse_junit(ROOT / "back" / "build" / "test-results" / "test")
    if not junit and result.returncode != 0:
        log((result.stdout + result.stderr)[-800:])
    return junit


def run_security(stamp: str, run_id: str, commit: str) -> tuple[list[Record], list[Risk]]:
    log("security_scan.py (tool A)")
    scanned = run_cmd([python_bin(), "scripts/qa/tools/security_scan.py"], ROOT, timeout=180)
    try:
        payload = json.loads(scanned.stdout)
    except json.JSONDecodeError:
        payload = {}
    log("bandit (tool B)")
    bandit = run_cmd(
        [python_bin(), "-m", "bandit", "-r", "ai/src", "data", "-f", "json", "-q"],
        ROOT,
        timeout=180,
    )
    try:
        bandit_payload = json.loads(bandit.stdout or "")
    except json.JSONDecodeError:
        bandit_payload = None
    if not isinstance(bandit_payload, dict) or "results" not in bandit_payload:
        bandit_error = (bandit.stderr or bandit.stdout or "bandit이 JSON 결과를 내지 않음")[-300:]
        bandit_results = []
    else:
        bandit_error = ""
        bandit_results = bandit_payload.get("results", [])

    def bandit_hits(test_ids: set[str]) -> list[dict]:
        return [item for item in bandit_results if item.get("test_id") in test_ids]

    records = []
    groups = {
        "TC-SEC-001": bandit_hits({"B105", "B106", "B107"}),
        "TC-SEC-002": bandit_hits({"B110", "B112"}),
        "TC-SEC-003": bandit_hits({"B307", "B608"}),
    }
    for tc_id, feature in SEC_FEATURES.items():
        section = payload.get(tc_id, {}) if payload else {}
        if not payload:
            a_status, a_detail = "ERROR", (scanned.stderr or scanned.stdout or "scanner failed")[-300:]
            findings = []
        else:
            a_status = section.get("status", "ERROR")
            findings = section.get("findings", [])
            a_detail = f"findings={len(findings)}"
            if findings:
                first = findings[0]
                a_detail = f"{first.get('file')}:{first.get('line')} {first.get('text', '')}"[:300]
        if bandit_error:
            b_status, b_detail = "ERROR", bandit_error
        else:
            hits = groups[tc_id]
            if hits:
                hit = hits[0]
                b_status = "FAIL"
                b_detail = f"{hit.get('test_id')} {hit.get('filename')}:{hit.get('line_number')} {hit.get('issue_text', '')}"[:300]
            else:
                b_status, b_detail = "PASS", "bandit 해당 규칙 없음"
        override = None
        risk_id = "-"
        if tc_id == "TC-SEC-002" and findings:
            risk_id = "RISK-SEC-001"
            override = {
                "file": findings[0].get("file", "UNKNOWN"),
                "function": findings[0].get("function", "UNKNOWN"),
                "line": findings[0].get("line", "UNKNOWN"),
            }
        records.append(
            tool_pair(
                tc_id,
                feature,
                "security",
                SCAN_CMD,
                a_status,
                a_detail,
                BANDIT_CMD,
                b_status,
                b_detail,
                stamp,
                run_id,
                commit,
                override=override,
                risk_id=risk_id,
                purpose="시크릿, 예외 삼킴, 위험한 실행 패턴",
                cause=a_detail if a_status == "FAIL" else "-",
            )
        )
    risks = []
    for item in payload.get("risks", []) if payload else []:
        risks.append(
            Risk(
                run_id=run_id,
                risk_id=str(item.get("risk_id", "RISK-SEC")),
                executed_at=stamp,
                feature=str(item.get("feature", "security")),
                test_type="security",
                severity=str(item.get("severity", "MEDIUM")),
                likelihood=str(item.get("likelihood", "중간")),
                impact=str(item.get("impact", "-")),
                action=str(item.get("action", "-")),
                status="OPEN",
                git_commit=commit,
                file=str(item.get("file", "UNKNOWN")),
                function=str(item.get("function", "UNKNOWN")),
                line=str(item.get("line", "UNKNOWN")),
                tc_id=str(item.get("tc_id", "-")),
                detail=str(item.get("detail", "-")),
            )
        )
    for item in bandit_results:
        severity = str(item.get("issue_severity", "")).upper()
        if severity not in ("HIGH", "CRITICAL"):
            continue
        if item.get("test_id") in {"B105", "B106", "B107", "B110", "B112", "B307", "B608"}:
            continue
        risks.append(
            Risk(
                run_id=run_id,
                risk_id=f"RISK-BANDIT-{item.get('test_id')}-{item.get('line_number')}",
                executed_at=stamp,
                feature="bandit",
                test_type="security",
                severity=severity,
                likelihood=str(item.get("issue_confidence", "UNKNOWN")),
                impact=str(item.get("issue_text", "-"))[:300],
                action="bandit 경고를 재현하고 고칠 것",
                status="OPEN",
                git_commit=commit,
                file=str(item.get("filename", "UNKNOWN")),
                function="UNKNOWN",
                line=str(item.get("line_number", "UNKNOWN")),
                tc_id="-",
                detail=str(item.get("code", ""))[:300],
            )
        )
    return records, risks


def run_ai_suite(stamp: str, run_id: str, commit: str, ci: bool) -> list[Record]:
    probe = run_cmd([python_bin(), "-c", "import torch"], ROOT, timeout=120)
    if probe.returncode != 0:
        status = "ERROR" if ci else "SKIPPED"
        detail = "torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED)."
        return [
            tool_pair(
                "TC-UNIT-AI-SUITE",
                "ai_full_suite",
                "unit",
                "python -m pytest ai/tests",
                status,
                detail,
                "python -c import torch",
                status,
                (probe.stderr or probe.stdout or detail)[-200:],
                stamp,
                run_id,
                commit,
                purpose="선택 검사. torch가 있을 때만 pytest를 실행",
            )
        ]
    log("ai pytest (optional tool A)")
    ran = run_cmd([python_bin(), "-m", "pytest", "tests", "-q"], ROOT / "ai", timeout=600)
    a_status = "PASS" if ran.returncode == 0 else "FAIL"
    detail = (ran.stdout or ran.stderr or "")[-300:]
    return [
        tool_pair(
            "TC-UNIT-AI-SUITE",
            "ai_full_suite",
            "unit",
            "python -m pytest ai/tests",
            a_status,
            detail or a_status,
            "python -c import torch",
            "PASS",
            "torch import ok",
            stamp,
            run_id,
            commit,
            purpose="선택 검사. pytest와 torch import로 교차 확인",
            expected="ai/tests PASS + torch import PASS",
        )
    ]


def run_infra(stamp: str, run_id: str, commit: str) -> list[Record]:
    log("docker compose config (tool A)")
    compose_env = os.environ.copy()
    if not compose_env.get("DB_PASSWORD"):
        compose_env["DB_PASSWORD"] = "qa-check"
    compose_a = run_cmd(
        ["docker", "compose", "-f", "compose.yaml", "config", "--quiet"],
        ROOT,
        timeout=60,
        env=compose_env,
    )
    if compose_a.returncode == 0:
        a1_status, a1_detail = "PASS", "compose config ok"
    else:
        a1_status, a1_detail = "FAIL", (compose_a.stderr or compose_a.stdout or "compose config failed")[-300:]

    log("compose_cross_check.py (tool B)")
    compose_b = run_cmd([python_bin(), "scripts/qa/tools/compose_cross_check.py"], ROOT, timeout=60)
    try:
        compose_payload = json.loads(compose_b.stdout or "")
        b1_status = str(compose_payload.get("status", "ERROR"))
        b1_detail = str(compose_payload.get("detail", ""))[:300]
    except json.JSONDecodeError:
        b1_status = "ERROR"
        b1_detail = (compose_b.stderr or compose_b.stdout or "compose_cross_check JSON 없음")[-300:]

    log("ci_workflow_check tool A")
    ci_a = run_cmd([python_bin(), "scripts/qa/tools/ci_workflow_check.py", "--tool", "a"], ROOT, timeout=60)
    try:
        ci_a_payload = json.loads(ci_a.stdout or "")
        a2_status = str(ci_a_payload.get("status", "ERROR"))
        a2_detail = str(ci_a_payload.get("detail", ""))[:300]
    except json.JSONDecodeError:
        a2_status = "ERROR"
        a2_detail = (ci_a.stderr or ci_a.stdout or "ci_workflow_check A JSON 없음")[-300:]

    log("ci_workflow_check tool B")
    ci_b = run_cmd([python_bin(), "scripts/qa/tools/ci_workflow_check.py", "--tool", "b"], ROOT, timeout=60)
    try:
        ci_b_payload = json.loads(ci_b.stdout or "")
        b2_status = str(ci_b_payload.get("status", "ERROR"))
        b2_detail = str(ci_b_payload.get("detail", ""))[:300]
    except json.JSONDecodeError:
        b2_status = "ERROR"
        b2_detail = (ci_b.stderr or ci_b.stdout or "ci_workflow_check B JSON 없음")[-300:]

    return [
        tool_pair(
            "TC-INFRA-001",
            INFRA_FEATURES["TC-INFRA-001"],
            "infra",
            COMPOSE_CMD,
            a1_status,
            a1_detail,
            COMPOSE_CHECK_CMD,
            b1_status,
            b1_detail,
            stamp,
            run_id,
            commit,
            purpose="compose.yaml 유효성과 필수 서비스 교차 확인",
            expected="config 성공 + back/ai/front/db 서비스 존재",
        ),
        tool_pair(
            "TC-INFRA-002",
            INFRA_FEATURES["TC-INFRA-002"],
            "infra",
            CI_FILE_CMD,
            a2_status,
            a2_detail,
            CI_CROSS_CMD,
            b2_status,
            b2_detail,
            stamp,
            run_id,
            commit,
            purpose="CI 워크플로 존재와 qa 잡 교차 확인",
            expected="ci.yml에 qa 잡과 python3 scripts/qa/run_qa.py 포함",
        ),
    ]


def front_gap(stamp: str, run_id: str, commit: str, test_type: str) -> Risk | None:
    package = ROOT / "front" / "package.json"
    if not package.is_file():
        return None
    try:
        scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
    except json.JSONDecodeError:
        scripts = {}
    if "test" in scripts and (ROOT / "front" / "node_modules").exists():
        return None
    return Risk(
        run_id=run_id,
        risk_id="RISK-UNIT-001",
        executed_at=stamp,
        feature="front_validation",
        test_type=test_type,
        severity="MEDIUM",
        likelihood="중간",
        impact="프론트 단위 테스트 스크립트 또는 node_modules가 없어 화면 계약을 실행하지 못했다.",
        action="프론트 러너를 추가한 뒤 같은 TC를 두 도구로 실행할 것.",
        status="OPEN",
        git_commit=commit,
        file="front/package.json",
        function="UNKNOWN",
        line=find_line("front/package.json", '"scripts"'),
        tc_id="-",
        detail="실행하지 않은 프론트 검사는 PASS로 기록하지 않음",
    )


def execute(ci: bool) -> tuple[list[Record], list[Risk], str, str]:
    when = seoul_now()
    run_id = new_run_id(when)
    stamp = when.isoformat(timespec="seconds")
    commit = git_commit(ROOT)
    junit = run_gradle()
    records = run_python_unit(stamp, run_id, commit)
    records.extend(run_java_unit(stamp, run_id, commit, junit))
    records.extend(run_api(stamp, run_id, commit, junit))
    security_records, risks = run_security(stamp, run_id, commit)
    records.extend(security_records)
    records.extend(run_infra(stamp, run_id, commit))
    records.extend(run_ai_suite(stamp, run_id, commit, ci))
    gap = front_gap(stamp, run_id, commit, "unit")
    if gap:
        risks.append(gap)
    return records, risks, run_id, stamp


def mark_regression(records: list[Record], risks: list[Risk]) -> tuple[list[Record], list[Risk]]:
    """회귀 재실행은 같은 영역·기능에 누적하고, detail에 회귀 표시만 붙인다."""
    for record in records:
        record.detail = "regression-rerun. " + record.detail
    return records, risks


def _blocks_exit(record: Record, ci: bool) -> bool:
    optional = record.tc_id == "TC-UNIT-AI-SUITE"
    if optional and record.final_status in ("SKIPPED", "NOT_RUN") and not ci:
        return False
    return record.final_status in ("FAIL", "BLOCKED", "NOT_RUN", "ERROR")


def exit_code(records: list[Record], risks: list[Risk], ci: bool) -> int:
    """FAIL·BLOCKED·필수 NOT_RUN·미해결 HIGH/CRITICAL은 1, 도구 ERROR만 있으면 2."""
    high = any(risk.severity in ("HIGH", "CRITICAL") and risk.status == "OPEN" for risk in risks)
    blocking = [record for record in records if _blocks_exit(record, ci)]
    if high or any(record.final_status in ("FAIL", "BLOCKED", "NOT_RUN") for record in blocking):
        return 1
    if any(record.final_status == "ERROR" for record in blocking):
        return 2
    return 0


def summarize(records: list[Record], risks: list[Risk], code: int) -> None:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.final_status] = counts.get(record.final_status, 0) + 1
    high = [risk for risk in risks if risk.severity in ("HIGH", "CRITICAL") and risk.status == "OPEN"]
    print(f"exit={code} counts={counts} open_high={len(high)}")
    for risk in high:
        print(f"HIGH {risk.risk_id} {risk.file}:{risk.line} {risk.function} {risk.impact}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AlloHub QA cross-check")
    parser.add_argument("--ci", action="store_true", help="torch 부재와 미실행 필수 검사를 실패로 본다")
    parser.add_argument(
        "--with-regression",
        action="store_true",
        help="전체 회귀: 같은 검사를 다시 실행해 동일 영역·기능 날짜 폴더에 누적",
    )
    args = parser.parse_args()
    day = seoul_now().strftime("%Y-%m-%d")
    records, risks, run_id, _stamp = execute(args.ci)
    write_run(ROOT, day, records, risks)
    log(f"recorded {run_id}")
    if args.with_regression:
        again, again_risks, regression_id, _stamp = execute(args.ci)
        again, again_risks = mark_regression(again, again_risks)
        write_run(ROOT, day, again, again_risks)
        records.extend(again)
        risks.extend(again_risks)
        log(f"recorded {regression_id}")
    code = exit_code(records, risks, args.ci)
    latest = {
        "run_id": run_id,
        "finished_at": seoul_now().isoformat(timespec="seconds"),
        "exit_code": code,
        "high_open": any(risk.severity in ("HIGH", "CRITICAL") and risk.status == "OPEN" for risk in risks),
        "source_fingerprint": source_fingerprint(ROOT),
        "test_types": sorted({record.test_type for record in records}),
        "areas": sorted({area_of(record.test_type) for record in records}),
    }
    latest_path = ROOT / "scripts" / "qa" / "latest.json"
    latest_path.write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summarize(records, risks, code)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired as exc:
        print(f"exit=2 timeout {exc.cmd}", file=sys.stderr)
        raise SystemExit(2)
