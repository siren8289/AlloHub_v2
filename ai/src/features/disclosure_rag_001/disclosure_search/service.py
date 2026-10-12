"""공시 검색 서비스 모듈: 기업·공시일 필터 검색, Hybrid Search 및 Reranking.

기능 및 설계 이유:
1. 기업 식별자(stock_code) 필터를 적용하여 다른 회사의 공시가 섞이는 문제를 100% 원천 차단합니다.
2. 기준일자(as_of_date) 필터를 적용하여 분석 시점 이후의 미래 공시(Lookahead bias)가 검색되는 것을 원천 차단합니다.
3. Dense(벡터 코사인 유사도)와 Sparse(키워드 빈도)를 결합한 Hybrid Search를 수행하고,
   핵심 재무 위험 단어 및 최신성 기반 Reranking을 적용하여 가장 중요한 근거를 상위에 노출합니다.
4. PostgreSQL + pgvector 연결이 제공되면 데이터베이스를 조회하며,
   미설치 환경에서는 동일한 필터링 로직을 갖는 내장 메모리 검색기로 안전하게 폴백합니다.
"""
import os
from typing import List, Optional

import numpy as np

from src.features.disclosure_rag_001.disclosure_knowledge.service import (
    embed_text,
    get_default_disclosure_documents,
    process_and_embed_documents,
)
from src.features.disclosure_rag_001.schemas import (
    DisclosureChunk,
    SearchFilter,
    SearchQuery,
    SearchResultChunk,
)

# 검색 메모리 캐시
_GLOBAL_CHUNKS_CACHE: Optional[List[DisclosureChunk]] = None

# 재무 위험 관련 핵심 가중 단어 (Reranking 가산점 대상)
RISK_KEYWORDS = [
    "감자", "결손", "자본잠식", "영업정지", "부도", "회생",
    "당기순손실", "적자", "상장폐지", "불확실성", "관리종목"
]


def get_search_corpus() -> List[DisclosureChunk]:
    """검색 대상이 되는 공시 청크 목록을 반환합니다.

    설계 이유:
    전체 공시 문서를 매 요청마다 재임베딩하지 않도록 메모리에 캐싱하여
    빠른 응답 속도를 보장합니다.
    """
    global _GLOBAL_CHUNKS_CACHE
    if _GLOBAL_CHUNKS_CACHE is None:
        docs = get_default_disclosure_documents()
        _GLOBAL_CHUNKS_CACHE = process_and_embed_documents(docs)
    return _GLOBAL_CHUNKS_CACHE


def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """두 벡터 간의 코사인 유사도를 계산합니다 (-1.0 ~ 1.0).

    설계 이유:
    공시 질의어와 공시 청크 간의 의미적(Semantic) 유사도를 정량적으로 측정하기 위함입니다.
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def calculate_sparse_score(query: str, text: str) -> float:
    """질의어에 포함된 단어들이 본문에 등장하는 빈도 기반 키워드 점수를 계산합니다.

    설계 이유:
    고유 명사(예: 회사명, 공시 분류명, 수치 등)의 정확한 일치를 보정하기 위해
    Sparse 키워드 매칭 점수를 함께 사용합니다.
    """
    query_tokens = set(query.lower().split())
    if not query_tokens:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for token in query_tokens if token in text_lower)
    return float(matches / len(query_tokens))


def calculate_rerank_score(
    chunk: DisclosureChunk,
    hybrid_score: float,
    as_of_date: str
) -> float:
    """하이브리드 점수에 위험 키워드 및 최신성 가산점을 부여하여 리랭킹 점수를 계산합니다.

    설계 이유:
    단순 텍스트 유사도만으로는 실제 재무 위험에 직결되는 결정적 공시(감자, 영업정지 등)가
    후순위로 밀릴 수 있으므로, 위험 키워드 가중치와 기준일 직전 최신 공시에 가산점을 부여합니다.
    """
    score = hybrid_score

    # 1. 재무 위험 핵심 키워드 가산점 (+0.15)
    content = chunk.content
    has_risk_word = any(word in content for word in RISK_KEYWORDS)
    if has_risk_word:
        score += 0.15

    # 2. 기준일자에 가까운 최근 공시 가산점 (+0.05)
    try:
        diff_days = int(as_of_date) - int(chunk.rcept_dt)
        if 0 <= diff_days <= 10000:  # 대략 1년 이내의 최근 공시
            score += 0.05
    except ValueError:
        pass

    return round(score, 4)


def search_disclosures_with_filter(
    query_text: str,
    search_filter: SearchFilter,
    top_k: int = 3,
    hybrid_alpha: float = 0.6,
    custom_chunks: Optional[List[DisclosureChunk]] = None
) -> List[SearchResultChunk]:
    """기업 식별자와 기준일자 필터를 강제 적용하여 하이브리드 검색 및 리랭킹을 수행합니다.

    설계 이유:
    [핵심 가드레일]
    1. chunk.stock_code == search_filter.stock_code: 타사 공시 혼입을 100% 배제합니다.
    2. chunk.rcept_dt <= search_filter.as_of_date: 분석 기준일 이후의 미래 공시를 100% 차단합니다.
    이 두 필터를 통과한 문서들에 대해서만 임베딩 유사도와 키워드 유사도를 결합하여 순위를 산출합니다.
    """
    corpus = custom_chunks if custom_chunks is not None else get_search_corpus()

    # 1단계: 엄격한 메타데이터 필터링 (가드레일 준수)
    filtered_chunks: List[DisclosureChunk] = []
    for chunk in corpus:
        # 타사 공시 차단
        if chunk.stock_code != search_filter.stock_code:
            continue
        # 미래 공시 혼입 차단 (Lookahead bias 차단)
        if str(chunk.rcept_dt) > str(search_filter.as_of_date):
            continue
        filtered_chunks.append(chunk)

    if not filtered_chunks:
        return []

    # 2단계: 질의어 임베딩 벡터 생성
    query_vec = embed_text(query_text)

    # 3단계: 유사도 계산 및 하이브리드 결합
    results: List[SearchResultChunk] = []
    for chunk in filtered_chunks:
        # Dense 점수 계산
        dense_score = 0.0
        if chunk.embedding:
            dense_score = calculate_cosine_similarity(query_vec, chunk.embedding)

        # Sparse 점수 계산
        sparse_score = calculate_sparse_score(query_text, chunk.content)

        # 하이브리드 점수 결합 (0.0 ~ 1.0)
        hybrid = (hybrid_alpha * dense_score) + ((1.0 - hybrid_alpha) * sparse_score)

        # 4단계: 리랭킹 점수 계산
        rerank = calculate_rerank_score(chunk, hybrid, search_filter.as_of_date)

        results.append(
            SearchResultChunk(
                chunk=chunk,
                dense_score=round(dense_score, 4),
                sparse_score=round(sparse_score, 4),
                hybrid_score=round(hybrid, 4),
                rerank_score=rerank,
            )
        )

    # 5단계: 리랭킹 점수 기준 내림차순 정렬 및 상위 Top-K 추출
    results.sort(key=lambda item: item.rerank_score, reverse=True)
    return results[:top_k]


def query_pgvector_if_available(
    query_text: str,
    search_filter: SearchFilter,
    top_k: int = 3
) -> Optional[List[SearchResultChunk]]:
    """PostgreSQL + pgvector 연결이 구성된 경우 DB 쿼리를 수행하고, 미구성 시 None을 반환합니다.

    설계 이유:
    운영 환경에 PostgreSQL과 pgvector 확장이 존재할 때 실제 DB의 인덱싱된 벡터 검색을
    사용할 수 있도록 연결 고리를 제공하며, 환경이 없는 개발/테스트 환경에서는
    In-Memory 엔진으로 무중단 폴백하도록 지원합니다.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None

    try:
        import psycopg
        # PostgreSQL 및 pgvector를 통한 쿼리 실행 시도
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                # 읽기 전용으로 안전하게 필터 검색 (stock_code 및 rcept_dt 필터 필수 적용)
                query_sql = """
                    SELECT chunk_id, doc_id, corp_code, corp_name, stock_code,
                           report_name, rcept_dt, section, content
                    FROM disclosure_chunks
                    WHERE stock_code = %s AND rcept_dt <= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """
                query_vec = embed_text(query_text)
                cur.execute(query_sql, (search_filter.stock_code, search_filter.as_of_date, str(query_vec), top_k))
                rows = cur.fetchall()
                if rows:
                    results = []
                    for row in rows:
                        chunk = DisclosureChunk(
                            chunk_id=row[0],
                            doc_id=row[1],
                            corp_code=row[2],
                            corp_name=row[3],
                            stock_code=row[4],
                            report_name=row[5],
                            rcept_dt=row[6],
                            section=row[7],
                            content=row[8],
                        )
                        results.append(SearchResultChunk(
                            chunk=chunk,
                            dense_score=1.0,
                            sparse_score=1.0,
                            hybrid_score=1.0,
                            rerank_score=1.0
                        ))
                    return results
    except Exception:
        # DB 연결 실패 또는 pgvector 미설치 시 조용히 메모리 검색으로 전환
        pass

    return None


def search_disclosures(query: SearchQuery) -> List[SearchResultChunk]:
    """공시 검색의 표준 진입점 함수입니다.

    설계 이유:
    DB(pgvector) 검색 가능 여부를 먼저 점검하고, 불가할 경우 철저한 필터링이 보장되는
    In-Memory 하이브리드 검색을 수행하여 안정성을 확보합니다.
    """
    # 1. DB 환경 시도
    db_results = query_pgvector_if_available(
        query_text=query.query_text,
        search_filter=query.filter,
        top_k=query.top_k,
    )
    if db_results is not None:
        return db_results

    # 2. 내장 인메모리 하이브리드 검색 수행
    return search_disclosures_with_filter(
        query_text=query.query_text,
        search_filter=query.filter,
        top_k=query.top_k,
        hybrid_alpha=query.hybrid_alpha,
    )
