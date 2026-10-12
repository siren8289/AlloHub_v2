"""공시 데이터 지식 베이스 구축 모듈: 수집, 청킹, 임베딩.

기능 및 설계 이유:
기업의 사업보고서, 감사보고서, 주요사항보고서(감자, 영업정지 등) 공시를 분할(Chunking)하고
밀집 벡터(Embedding)로 변환하여 검색 가능한 지식 베이스를 생성합니다.
외부 API 키가 없는 오프라인 환경에서도 scikit-learn 기반의 정규화 임베딩으로 완전하게 동작하도록 설계되었습니다.
"""
import hashlib
import math
from typing import List, Optional

import numpy as np

from src.core.config import get_gemini_api_key
from src.features.disclosure_rag_001.schemas import DisclosureChunk, DisclosureDocument

# 고정 임베딩 차원 (오프라인 폴백용)
FALLBACK_EMBEDDING_DIM = 512


def get_default_disclosure_documents() -> List[DisclosureDocument]:
    """기본 제공되는 공시 문서 데이터셋을 반환합니다.

    설계 이유:
    공공데이터 API 연결 전이나 테스트 환경에서도 실제 공시 양식(감자, 영업정지, 사업보고서 등)을
    기반으로 검색과 근거 검증을 즉시 수행할 수 있도록 표준 공시 말뭉치를 제공합니다.
    시점 검증 테스트를 위해 과거 공시와 미래 공시를 함께 포함하고 있습니다.
    """
    docs = [
        # 1. KR모터스 (A000040) - 과거 공시 (감자결정)
        DisclosureDocument(
            doc_id="DOC_KR_20260512_01",
            corp_code="1601110007032",
            corp_name="KR모터스(주)",
            stock_code="A000040",
            report_name="주요사항보고서(감자결정)",
            rcept_no="20260512000101",
            rcept_dt="20260512",
            section="감자의 목적 및 사유",
            content=(
                "당사는 결손금 보전 및 재무구조 개선을 목적으로 보통주 5주를 동일한 액면주식 1주로 "
                "병합하는 무상감자를 결정하였습니다. 감자비율은 80%이며, 자본금은 500억원에서 "
                "100억원으로 감소합니다. 누적된 영업손실로 인한 자본잠식 해소가 주요 배경입니다."
            ),
        ),
        # 2. KR모터스 (A000040) - 과거 공시 (영업정지)
        DisclosureDocument(
            doc_id="DOC_KR_20260620_01",
            corp_code="1601110007032",
            corp_name="KR모터스(주)",
            stock_code="A000040",
            report_name="주요사항보고서(영업정지)",
            rcept_no="20260620000202",
            rcept_dt="20260620",
            section="영업정지 사유",
            content=(
                "주요 생산공장 노후설비 보수 및 안전진단 실시로 인하여 창원공장의 생산라인이 "
                "일시 가동 중단(영업정지)되었습니다. 영업정지 분야의 매출액은 최근 매출의 25%에 해당하며, "
                "보수 완료 후 조속한 생산 재개를 예정하고 있습니다."
            ),
        ),
        # 3. KR모터스 (A000040) - 과거 공시 (사업보고서 및 감사보고서)
        DisclosureDocument(
            doc_id="DOC_KR_20260331_01",
            corp_code="1601110007032",
            corp_name="KR모터스(주)",
            stock_code="A000040",
            report_name="사업보고서(2025.12)",
            rcept_no="20260331000303",
            rcept_dt="20260331",
            section="재무제표 및 감사의견",
            content=(
                "외부감사인은 당사의 2025사업연도 재무제표에 대해 '적정의견'을 표명하였으나, "
                "당기순손실 210억원이 발생하여 계속기업 가정에 불확실성이 존재함을 강조사항으로 기재하였습니다. "
                "그러나 회생절차나 부도 관련 절차는 진행 중이지 않습니다."
            ),
        ),
        # 4. KR모터스 (A000040) - 미래 공시 (Lookahead bias 차단 검증용: 20261115 일자)
        DisclosureDocument(
            doc_id="DOC_KR_20261115_FUTURE",
            corp_code="1601110007032",
            corp_name="KR모터스(주)",
            stock_code="A000040",
            report_name="주요사항보고서(유상증자결정)",
            rcept_no="20261115000404",
            rcept_dt="20261115",
            section="유상증자 목적",
            content=(
                "[미래 공시] 당사는 운영자금 조달을 위해 150억원 규모의 제3자배정 유상증자를 결정하였습니다. "
                "이 공시는 2026년 11월 15일에 공개된 자료이므로 10월 분석 시점에는 사용되어서는 안 됩니다."
            ),
        ),
        # 5. 동화약품 (A000020) - 타사 공시 (타사 혼입 차단 검증용)
        DisclosureDocument(
            doc_id="DOC_DH_20260325_01",
            corp_code="1101110043870",
            corp_name="동화약품(주)",
            stock_code="A000020",
            report_name="사업보고서(2025.12)",
            rcept_no="20260325000505",
            rcept_dt="20260325",
            section="배당 및 이익 현황",
            content=(
                "당사는 안정적인 현금흐름을 바탕으로 보통주 1주당 180원의 현금배당을 결정하였습니다. "
                "배당수익률은 2.83%이며 당기순이익 282억원을 기록하여 안정적인 재무건전성을 유지하고 있습니다. "
                "부도, 영업정지, 회생 등 특이 위험 사유는 없습니다."
            ),
        ),
        # 6. 삼성전자 (A005930) - 타사 공시
        DisclosureDocument(
            doc_id="DOC_SEC_20260320_01",
            corp_code="1101110006246",
            corp_name="삼성전자(주)",
            stock_code="A005930",
            report_name="사업보고서(2025.12)",
            rcept_no="20260320000606",
            rcept_dt="20260320",
            section="사업의 개요 및 재무상태",
            content=(
                "당사는 반도체 및 모바일 부문의 견조한 실적을 바탕으로 견고한 재무구조를 유지하고 있습니다. "
                "지속적인 현금배당 정책을 유지 중이며 재무 위험 징후는 발견되지 않았습니다."
            ),
        ),
    ]
    return docs


def split_text_into_chunks(text: str, chunk_size: int = 250, chunk_overlap: int = 50) -> List[str]:
    """긴 본문 텍스트를 문맥 유지를 위해 오버랩을 두고 여러 청크로 분할합니다.

    설계 이유:
    공시 본문은 문장 간의 인과관계가 중요하므로, 단순 글자 수 분할 시 문맥이 잘리는 문제를 막기 위해
    일정한 글자 수와 앞뒤 중첩(overlap) 구간을 두어 청크 단위 검색의 정확도를 높입니다.
    """
    clean_text = " ".join(text.split())
    if len(clean_text) <= chunk_size:
        return [clean_text]

    chunks = []
    start = 0
    text_length = len(clean_text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = clean_text[start:end]
        chunks.append(chunk)
        if end >= text_length:
            break
        # 오버랩만큼 뒤로 이동하여 다음 청크 시작
        start += chunk_size - chunk_overlap

    return chunks


def chunk_document(doc: DisclosureDocument, chunk_size: int = 250, chunk_overlap: int = 50) -> List[DisclosureChunk]:
    """공시 문서를 분할하여 메타데이터가 보존된 청크 목록을 생성합니다.

    설계 이유:
    검색 시 특정 문단만 검색되더라도, 원본 공시의 문서명, 공시일자, 종목코드를
    추적하여 인용(Citation)과 기간 검증(Point-in-time)을 정확히 수행하기 위함입니다.
    """
    raw_chunks = split_text_into_chunks(doc.content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    result = []
    for index, content in enumerate(raw_chunks):
        chunk_obj = DisclosureChunk(
            chunk_id=f"{doc.doc_id}_C{index + 1}",
            doc_id=doc.doc_id,
            corp_code=doc.corp_code,
            corp_name=doc.corp_name,
            stock_code=doc.stock_code,
            report_name=doc.report_name,
            rcept_dt=doc.rcept_dt,
            section=doc.section,
            content=content,
            embedding=None,
        )
        result.append(chunk_obj)
    return result


def compute_fallback_embedding(text: str, dim: int = FALLBACK_EMBEDDING_DIM) -> List[float]:
    """텍스트의 문자 및 어절 n-gram 특성을 기반으로 정규화된 단위 벡터 임베딩을 계산합니다.

    설계 이유:
    외부 LLM API 키가 없거나 네트워크가 차단된 환경에서도 한국어 복합명사(예: '무상감자'와 '감자')의
    의미적 유사도 검색이 안정적으로 작동하도록 문자 경계 n-gram(char_wb) 기반
    scikit-learn HashingVectorizer를 활용하여 L2 정규화 밀집 벡터를 생성합니다.
    """
    from sklearn.feature_extraction.text import HashingVectorizer

    vectorizer = HashingVectorizer(
        n_features=dim,
        analyzer="char_wb",
        ngram_range=(2, 3),
        alternate_sign=False,
        norm="l2",
    )
    sparse_matrix = vectorizer.transform([text])
    dense_vec = sparse_matrix.toarray()[0].astype(np.float32)
    return dense_vec.tolist()


def embed_text(text: str) -> List[float]:
    """단일 텍스트에 대한 임베딩 벡터를 반환합니다. Gemini 사용 가능 시 활용하고 실패 시 내장 임베딩을 사용합니다.

    설계 이유:
    Google GenAI API가 유효하면 최신 임베딩 모델을 활용하고,
    미설정 또는 오류 발생 시 자체 내장 임베딩으로 유연하게 전환하여 시스템 장애를 방지합니다.
    """
    api_key = get_gemini_api_key()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            resp = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            if hasattr(resp, "embedding") and resp.embedding:
                return resp.embedding.values
            if hasattr(resp, "embeddings") and resp.embeddings:
                return resp.embeddings[0].values
        except Exception:
            # 외부 API 오류 시 조용히 내장 폴백으로 전환
            pass

    return compute_fallback_embedding(text)


def process_and_embed_documents(docs: List[DisclosureDocument]) -> List[DisclosureChunk]:
    """공시 문서 목록을 받아 청킹하고 각각 임베딩 벡터를 주입한 청크 목록을 반환합니다.

    설계 이유:
    검색 엔진에 등록하기 전에 전체 텍스트를 청킹하고 벡터화하는 파이프라인의 통합 진입점입니다.
    """
    all_chunks: List[DisclosureChunk] = []
    for doc in docs:
        chunks = chunk_document(doc)
        for chunk in chunks:
            chunk.embedding = embed_text(chunk.content)
            all_chunks.append(chunk)
    return all_chunks
