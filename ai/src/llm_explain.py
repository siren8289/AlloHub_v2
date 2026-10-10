"""LLM(Gemini)으로 진단 결과를 쉬운 문장으로 설명한다.

GEMINI_API_KEY 가 없거나 호출에 실패하면 미리 정한 기본 문장을 쓴다.
투자 권유 문장은 만들지 않는다. 공공데이터로 본 참고 설명만 한다.
"""
import os

GRADE_NAMES = {"stable": "안정", "warning": "주의", "danger": "위험"}


def basic_explanation(company, result):
    """LLM 없이 만드는 기본 설명"""
    grade = GRADE_NAMES[result["grade"]]
    alerts = []
    if result["default_count"]:
        alerts.append(f"부도 공시 {result['default_count']}건")
    if result["suspend_count"]:
        alerts.append(f"영업정지 공시 {result['suspend_count']}건")
    if result["rehab_count"]:
        alerts.append(f"회생 공시 {result['rehab_count']}건")
    if result["reduction_count"]:
        alerts.append(f"감자 공시 {result['reduction_count']}건")

    if alerts:
        alert_text = "공개된 공시에는 " + ", ".join(alerts) + "이 있습니다."
    else:
        alert_text = "수집한 공시에서는 부도·영업정지·회생·감자가 보이지 않습니다."

    return (
        f"{company['item_name']}({company['market']})의 참고 위험 점수는 "
        f"{result['score']}점으로 '{grade}' 단계입니다. "
        f"머신러닝 {result['ml_score']}점, 딥러닝 {result['dl_score']}점입니다. "
        f"{alert_text} "
        "이 점수는 출자 여부를 대신 정해 주지 않으며, 공시와 상장 정보를 요약한 참고값입니다."
    )


def make_prompt(company, result):
    return "\n".join([
        "너는 출자 조합의 자료 정리 도우미다.",
        "아래 공공데이터 요약을 3문장 이내의 쉬운 한국어로 설명해라.",
        "매수·매도·투자 권유는 하지 마라. 숫자는 그대로 인용해라.",
        "",
        f"종목: {company['item_name']} / 법인: {company['corp_name']} / 시장: {company['market']}",
        f"ML 위험점수: {result['ml_score']} / DL 위험점수: {result['dl_score']} / 평균: {result['score']}",
        f"단계: {GRADE_NAMES[result['grade']]}",
        f"부도 {result['default_count']}건, 영업정지 {result['suspend_count']}건, "
        f"회생 {result['rehab_count']}건, 감자 {result['reduction_count']}건",
        f"최근 현금배당률: {company['dividend_rate']}%",
    ])


def explain(company, result):
    """(설명 문장, 출처) 를 돌려준다. 출처는 "gemini" 또는 "basic"."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return basic_explanation(company, result), "basic"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=15000),  # 15초
        )
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            contents=make_prompt(company, result),
        )
        if response.text:
            return response.text.strip(), "gemini"
    except Exception as error:
        print("Gemini 호출 실패, 기본 설명을 사용합니다:", type(error).__name__)

    return basic_explanation(company, result), "basic"
