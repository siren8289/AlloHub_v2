"""LLM 프롬프트 템플릿 생성 모듈."""
from typing import Any, Mapping

from src.core.config import GRADE_NAMES


def make_prompt(company: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    """출자 조합 심사 보조를 위한 한국어 프롬프트 텍스트를 생성합니다."""
    grade_kor = GRADE_NAMES.get(result.get("grade", "stable"), "안정")
    return "\n".join([
        "너는 출자 조합의 자료 정리 도우미다.",
        "아래 공공데이터 요약을 3문장 이내의 쉬운 한국어로 설명해라.",
        "매수·매도·투자 권유는 하지 마라. 숫자는 그대로 인용해라.",
        "",
        f"종목: {company['item_name']} / 법인: {company['corp_name']} / 시장: {company['market']}",
        f"ML 위험점수: {result['ml_score']} / DL 위험점수: {result['dl_score']} / 평균: {result['score']}",
        f"단계: {grade_kor}",
        f"부도 {result['default_count']}건, 영업정지 {result['suspend_count']}건, "
        f"회생 {result['rehab_count']}건, 감자 {result['reduction_count']}건",
        f"최근 현금배당률: {company['dividend_rate']}%",
    ])
