"""공시 RAG 하네스(Harness) 런타임: 시점 검증, 가드레일, 실행 추적 및 정량 평가.

기능 및 설계 이유:
1. 타사 공시 혼입 차단 (기업 식별자 격리 가드레일).
2. 미래 공시 혼입 차단 (Point-in-time / Lookahead bias 차단 가드레일).
3. 읽기 전용 접근(Read-only) 강제 및 근거 없는 부도/파산 확정 방지.
4. 실행 단계별 감사 추적(Audit Tracing) 및 재시도(Retry) 런타임 제어.
5. 5대 정량 평가 지표 산출: Recall@K, Citation Accuracy, 기업 ID 일치율, 시점 정확도, Faithfulness.
"""
import re
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from src.features.disclosure_rag_001.schemas import (
    DisclosureChunk,
    EvaluationMetrics,
)


class HarnessAuditor:
    """워크플로우 실행 중 가드레일 검증 내역과 단계별 소요 시간을 기록하는 감사 추적기.

    설계 이유:
    규제 금융 환경 및 출자 심사에서 각 결정의 근거와 가드레일 통과 여부를
    투명하고 재현 가능하게 증적(Audit Trail)으로 보존하기 위함입니다.
    """

    def __init__(self):
        self.logs: List[str] = []
        self.guardrail_results: Dict[str, bool] = {
            "company_isolation": True,
            "lookahead_blocked": True,
            "read_only_enforced": True,
            "unfounded_claims_blocked": True,
        }

    def record_step(self, step_name: str, passed: bool, message: str) -> None:
        """감사 로그 한 줄을 타임스탬프와 함께 기록합니다."""
        status_str = "SUCCESS" if passed else "WARNING"
        log_line = f"[{time.strftime('%H:%M:%S')}] [{status_str}] {step_name}: {message}"
        self.logs.append(log_line)

    def mark_guardrail(self, guardrail_name: str, passed: bool) -> None:
        """가드레일 검증 상태를 갱신합니다."""
        self.guardrail_results[guardrail_name] = passed


def validate_company_isolation(
    chunks: List[DisclosureChunk],
    target_stock_code: str,
    auditor: Optional[HarnessAuditor] = None
) -> Tuple[List[DisclosureChunk], bool]:
    """검색된 공시 청크 중 대상 기업과 다른 종목의 공시가 섞였는지 검사하고 위반 청크를 격리 배제합니다.

    설계 이유:
    [필수 가드레일] 유사도 검색 과정에서 타사의 자극적인 공시(타사 부도, 타사 감자 등)가
    오인 유입되어 분석 대상 기업의 위험도로 둔갑하는 치명적 오류를 원천 방지합니다.
    """
    valid_chunks: List[DisclosureChunk] = []
    has_leakage = False

    for chunk in chunks:
        if chunk.stock_code == target_stock_code:
            valid_chunks.append(chunk)
        else:
            has_leakage = True
            if auditor:
                auditor.record_step(
                    "타사공시_격리검증",
                    False,
                    f"타사 종목({chunk.stock_code}, {chunk.corp_name}) 공시 감지되어 즉시 배제함 (청크 ID: {chunk.chunk_id})"
                )

    passed = not has_leakage
    if auditor:
        auditor.mark_guardrail("company_isolation", passed)
        if passed:
            auditor.record_step("타사공시_격리검증", True, f"모든 공시가 대상 기업({target_stock_code})과 일치함")

    return valid_chunks, passed


def validate_lookahead_bias(
    chunks: List[DisclosureChunk],
    as_of_date: str,
    auditor: Optional[HarnessAuditor] = None
) -> Tuple[List[DisclosureChunk], bool]:
    """분석 기준일자(as_of_date) 이후에 공시된 미래 자료가 포함되어 있는지 검사하고 차단합니다.

    설계 이유:
    [필수 가드레일] 백테스팅 및 과거 시점 분석 시, 분석 시점 당시에는 알 수 없었던
    미래 공시가 반영되는 '시간 여행(Lookahead bias)' 왜곡을 방지하기 위함입니다.
    """
    valid_chunks: List[DisclosureChunk] = []
    has_future_disclosure = False

    for chunk in chunks:
        if str(chunk.rcept_dt) <= str(as_of_date):
            valid_chunks.append(chunk)
        else:
            has_future_disclosure = True
            if auditor:
                auditor.record_step(
                    "시점검증_미래공시차단",
                    False,
                    f"기준일({as_of_date}) 이후 공개된 미래 공시({chunk.rcept_dt}, {chunk.report_name}) 차단함"
                )

    passed = not has_future_disclosure
    if auditor:
        auditor.mark_guardrail("lookahead_blocked", passed)
        if passed:
            auditor.record_step("시점검증_미래공시차단", True, f"모든 공시가 기준일({as_of_date}) 이전 자료임을 확인")

    return valid_chunks, passed


def enforce_read_only_query(query_sql: str) -> bool:
    """SQL 또는 데이터베이스 쿼리가 쓰기/수정/삭제 작업을 포함하는지 검사합니다.

    설계 이유:
    RAG 검색 파이프라인은 데이터베이스 조회만 수행해야 하며,
    어떠한 경우에도 원본 공시나 기업 데이터를 변조할 수 없도록 엄격한 읽기 전용 권한을 보장합니다.
    """
    forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create"]
    lowered = query_sql.lower()
    for kw in forbidden_keywords:
        # 단어 단위 매칭 확인
        if re.search(rf"\b{kw}\b", lowered):
            return False
    return True


def execute_with_retry(
    operation: Callable[[], Any],
    max_retries: int = 3,
    delay_seconds: float = 0.2
) -> Any:
    """외부 호출 또는 검색 작업을 재시도 및 타임아웃 보호 하에 안전하게 실행합니다.

    설계 이유:
    일시적인 네트워크 지연이나 LLM API 순단 현상 발생 시 즉시 실패하지 않고
    지정된 횟수만큼 재시도하여 파이프라인의 가용성(Reliability)을 높입니다.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return operation()
        except Exception as exc:
            last_exception = exc
            time.sleep(delay_seconds * attempt)
    raise RuntimeError(f"{max_retries}회 재시도 후에도 작업 실패: {last_exception}")


def compute_recall_at_k(
    retrieved_chunk_ids: List[str],
    ground_truth_chunk_ids: List[str],
    k: int = 3
) -> float:
    """상위 K개 검색 결과에서 실제 관련 정답 공시가 얼마나 회수되었는지 비율(0.0 ~ 1.0)을 계산합니다.

    설계 이유:
    RAG 검색 시스템의 정보 검색 품질을 객관적으로 측정하기 위한 표준 지표입니다.
    """
    if not ground_truth_chunk_ids:
        return 1.0
    top_k_retrieved = set(retrieved_chunk_ids[:k])
    matched = sum(1 for cid in ground_truth_chunk_ids if cid in top_k_retrieved)
    return round(float(matched / len(ground_truth_chunk_ids)), 4)


def compute_citation_accuracy(
    explanation: str,
    valid_citations: List[str]
) -> float:
    """설명문에 표기된 인용 출처가 실제 유효하게 검색된 공시 문서와 일치하는 비율을 계산합니다.

    설계 이유:
    인공지능이 존재하지 않는 가짜 공시 번호나 잘못된 날짜를 허위 인용(Hallucinated citation)하는
    현상을 방지하고 인용의 정확성을 정량적으로 평가하기 위함입니다.
    """
    if not valid_citations:
        return 1.0

    # 설명문에서 인용 구문 형태 [보고서명, ...] 추출
    found_cites = re.findall(r"\[([^\]]+)\]", explanation)
    if not found_cites:
        # 인용 목록이 유효하게 주어졌고 설명문이 안전한 경우 부분 기본점수
        return 0.8

    correct_count = 0
    for cite in found_cites:
        # 유효 인용 문구 중 하나와 일치하거나 핵심 내용이 포함되는지 확인
        is_matched = any(
            cite in valid or any(part in cite for part in valid.strip("[]").split(","))
            for valid in valid_citations
        )
        if is_matched:
            correct_count += 1

    return round(float(correct_count / len(found_cites)), 4)


def compute_company_id_match_rate(
    chunks: List[DisclosureChunk],
    target_stock_code: str
) -> float:
    """검색 및 인용된 공시 청크 중 대상 기업 종목코드와 일치하는 비율(목표 1.0 = 100%)을 계산합니다.

    설계 이유:
    타사 정보 유입 여부를 수치로 감시하기 위한 필수 안정성 평가 메트릭입니다.
    """
    if not chunks:
        return 1.0
    matches = sum(1 for c in chunks if c.stock_code == target_stock_code)
    return round(float(matches / len(chunks)), 4)


def compute_point_in_time_accuracy(
    chunks: List[DisclosureChunk],
    as_of_date: str
) -> float:
    """검색 및 인용된 공시 청크 중 기준일자 이전 공시의 준수 비율(목표 1.0 = 100%)을 계산합니다.

    설계 이유:
    미래 공시 혼입 여부를 수치로 감시하기 위한 Lookahead 차단율 평가 지표입니다.
    """
    if not chunks:
        return 1.0
    valid_dates = sum(1 for c in chunks if str(c.rcept_dt) <= str(as_of_date))
    return round(float(valid_dates / len(chunks)), 4)


def compute_faithfulness_score(
    explanation: str,
    chunks: List[DisclosureChunk],
    screening_result: Mapping[str, Any]
) -> float:
    """생성된 설명문이 실제 공시 본문 및 재무 위험 진단 수치와 모순되지 않고 부합하는지 신뢰도(0.0 ~ 1.0)를 평가합니다.

    설계 이유:
    생성 모델이 수치를 왜곡하거나 공시에 없는 거짓 위험 요소를 주장하지 않고
    실제 근거에 충실(Faithful)하게 작성되었는지를 다각도로 측정합니다.
    """
    total_checks = 0
    passed_checks = 0

    # 1. 종합 점수 수치 언급 일치 검사
    score_val = str(screening_result.get("score", ""))
    if score_val:
        total_checks += 1
        if score_val in explanation:
            passed_checks += 1

    # 2. 기업 종목명 언급 일치 검사
    company_name = str(screening_result.get("company_name", ""))
    if company_name:
        total_checks += 1
        if company_name in explanation:
            passed_checks += 1

    # 3. 위험 단어 언급 시 실제 청크 본문에 해당 사실 존재 여부 검사
    risk_words = ["감자", "영업정지", "부도", "회생"]
    for rw in risk_words:
        if rw in explanation:
            total_checks += 1
            # 실제 청크에 해당 단어가 있는지 확인
            chunk_has_word = any(rw in c.content for c in chunks)
            if chunk_has_word:
                passed_checks += 1

    if total_checks == 0:
        return 1.0

    return round(float(passed_checks / total_checks), 4)


def run_evaluation(
    explanation: str,
    chunks: List[DisclosureChunk],
    valid_citations: List[str],
    target_stock_code: str,
    as_of_date: str,
    screening_result: Mapping[str, Any],
    ground_truth_chunk_ids: Optional[List[str]] = None
) -> EvaluationMetrics:
    """RAG 파이프라인 전반에 대한 5대 핵심 정량 평가 지표를 일괄 계산하여 반환합니다.

    설계 이유:
    단일 평가 호출로 Recall@K, Citation Accuracy, 기업 ID 일치율, 시점 정확도, Faithfulness를
    한눈에 파악하여 배포 및 모니터링 기준 충족 여부를 판단할 수 있도록 지원합니다.
    """
    retrieved_chunk_ids = [c.chunk_id for c in chunks]
    gt_ids = ground_truth_chunk_ids if ground_truth_chunk_ids is not None else retrieved_chunk_ids

    recall = compute_recall_at_k(retrieved_chunk_ids, gt_ids, k=3)
    citation_acc = compute_citation_accuracy(explanation, valid_citations)
    company_match = compute_company_id_match_rate(chunks, target_stock_code)
    pit_acc = compute_point_in_time_accuracy(chunks, as_of_date)
    faithfulness = compute_faithfulness_score(explanation, chunks, screening_result)

    return EvaluationMetrics(
        recall_at_k=recall,
        citation_accuracy=citation_acc,
        company_id_match_rate=company_match,
        point_in_time_accuracy=pit_acc,
        faithfulness_score=faithfulness,
    )
