"""LLM(Gemini) 또는 기본 규칙을 이용한 진단 결과 설명 생성 모듈."""
from typing import Any, Mapping, Tuple

from src.core.config import (
    GEMINI_TIMEOUT_MS,
    GRADE_NAMES,
    get_gemini_api_key,
    get_gemini_model,
)
from src.llm.prompts import make_prompt


def basic_explanation(company: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    """GEMINI_API_KEY가 없거나 호출 실패 시 사용하는 기본 템플릿 설명."""
    grade_kor = GRADE_NAMES.get(result.get("grade", "stable"), "안정")
    alerts = []
    if result.get("default_count"):
        alerts.append(f"부도 공시 {result['default_count']}건")
    if result.get("suspend_count"):
        alerts.append(f"영업정지 공시 {result['suspend_count']}건")
    if result.get("rehab_count"):
        alerts.append(f"회생 공시 {result['rehab_count']}건")
    if result.get("reduction_count"):
        alerts.append(f"감자 공시 {result['reduction_count']}건")

    if alerts:
        alert_text = "공개된 공시에는 " + ", ".join(alerts) + "이 있습니다."
    else:
        alert_text = "수집한 공시에서는 부도·영업정지·회생·감자가 보이지 않습니다."

    return (
        f"{company['item_name']}({company['market']})의 참고 위험 점수는 "
        f"{result['score']}점으로 '{grade_kor}' 단계입니다. "
        f"머신러닝 {result['ml_score']}점, 딥러닝 {result['dl_score']}점입니다. "
        f"{alert_text} "
        "이 점수는 출자 여부를 대신 정해 주지 않으며, 공시와 상장 정보를 요약한 참고값입니다."
    )


def explain(company: Mapping[str, Any], result: Mapping[str, Any]) -> Tuple[str, str]:
    """(설명 문장, 출처)를 반환합니다. 출처는 'gemini' 또는 'basic'입니다."""
    api_key = get_gemini_api_key()
    if not api_key:
        return basic_explanation(company, result), "basic"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
        response = client.models.generate_content(
            model=get_gemini_model(),
            contents=make_prompt(company, result),
        )
        if response.text:
            return response.text.strip(), "gemini"
    except Exception as error:
        print("Gemini 호출 실패, 기본 설명을 사용합니다:", type(error).__name__)

    return basic_explanation(company, result), "basic"
