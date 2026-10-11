"""위험 등급 판정 규칙.

1. 부도·영업정지·회생 공시가 1건이라도 있으면 모델 점수와 무관하게 '위험(danger)' 단계로 승격합니다.
2. 감자 공시가 있거나 모델 점수가 40점 이상이면 '주의(warning)' 단계입니다.
3. 그 외의 경우 '안정(stable)' 단계입니다.
"""
from typing import Any, Mapping

from src.core.config import SCORE_THRESHOLD_WARNING


def grade_of(score: float, company: Mapping[str, Any]) -> str:
    """공시 이력 사실을 우선하여 위험 등급('danger', 'warning', 'stable')을 반환합니다."""
    if int(company.get("default_count", 0)) > 0 or \
       int(company.get("suspend_count", 0)) > 0 or \
       int(company.get("rehab_count", 0)) > 0:
        return "danger"

    if score >= SCORE_THRESHOLD_WARNING or int(company.get("reduction_count", 0)) > 0:
        return "warning"

    return "stable"
