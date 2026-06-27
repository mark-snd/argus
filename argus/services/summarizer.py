"""콘텐츠 요약 서비스 — 규칙 기반 + LLM(SNDWorks Gateway)."""

import re
from typing import List, Optional

from argus.services.llm_client import get_llm_client


def _extract_key_sentences(text: str, num_sentences: int = 3) -> str:
    """문장 단위 추출 후 상위 num_sentences개를 반환합니다."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return text[:500]
    chosen = sentences[:num_sentences]
    return " ".join(chosen)


async def summarize_search_results(
    query: str,
    results: List[dict],
    method: str = "auto",
) -> str:
    """여러 검색 결과를 바탕으로 답변을 생성합니다.

    Parameters
    ----------
    query : str
        원본 검색어 / 질문
    results : list[dict]
        검색 결과 목록 (title, url, content 포함)
    method : str
        "auto" (LLM 가능 시 LLM, 불가 시 규칙 기반),
        "extractive" (강제 규칙 기반),
        "abstractive" (강제 LLM — 키 없으면 에러)

    Returns
    -------
    str
        AI-optimized 요약 답변
    """
    client = get_llm_client()

    # 강제 규칙 기반
    if method == "extractive":
        return _extractive_summary(query, results)

    # 강제 LLM (키 없으면 에러)
    if method == "abstractive":
        return await _llm_summary(query, results)

    # auto: LLM 가능하면 쓰고, 아니면 규칙 기반 fallback
    if client.available:
        return await _llm_summary(query, results)
    return _extractive_summary(query, results)


def _extractive_summary(query: str, results: List[dict]) -> str:
    """추출 요약: 각 결과의 핵심 문장을 합쳐 답변을 구성합니다."""
    parts: List[str] = []
    for idx, r in enumerate(results[:5], 1):
        content = r.get("content", "")
        if not content:
            continue
        key_sentences = _extract_key_sentences(content, num_sentences=1)
        parts.append(f"{key_sentences}")

    if not parts:
        return "관련 정보를 찾을 수 없습니다."

    combined = " ".join(parts)
    summary = _extract_key_sentences(combined, num_sentences=3)
    return summary if len(summary) > 20 else combined[:500]


async def _llm_summary(query: str, results: List[dict]) -> str:
    """LLM(SNDWorks Gateway)을 호출하여 추상 요약을 생성합니다."""
    client = get_llm_client()
    try:
        return await client.summarize(query, results)
    except Exception as exc:
        # LLM 실패 시 규칙 기반으로 fallback
        return f"[LLM 요약 실패: {exc}]\n\n{_extractive_summary(query, results)}"


async def generate_answer(
    query: str,
    results: List[dict],
    include_sources: bool = True,
) -> str:
    """검색 결과를 바탕으로 end-user용 답변 문자열을 생성합니다."""
    summary = await summarize_search_results(query, results, method="auto")

    if not include_sources or not results:
        return summary

    source_lines: List[str] = [
        "\n\n**출처:**",
    ]
    for idx, r in enumerate(results[:5], 1):
        source_lines.append(f"{idx}. [{r.get('title', 'Untitled')}]({r.get('url', '')})")

    return summary + "\n".join(source_lines)
