"""콘텐츠 요약 서비스 — 규칙 기반 + LLM 인터페이스."""

import re
from typing import List, Optional


def _extract_key_sentences(text: str, num_sentences: int = 3) -> str:
    """문장 단위 추출 후 상위 num_sentences개를 반환합니다."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return text[:500]
    chosen = sentences[:num_sentences]
    return " ".join(chosen)


def summarize_search_results(
    query: str,
    results: List[dict],
    method: str = "extractive",
) -> str:
    """여러 검색 결과를 바탕으로 답변을 생성합니다.

    Parameters
    ----------
    query : str
        원본 검색어 / 질문
    results : list[dict]
        검색 결과 목록 (title, url, content 포함)
    method : str
        "extractive" (추출 요약) 또는 "abstractive" (추상 요약, LLM 필요)

    Returns
    -------
    str
        AI-optimized 요약 답변
    """
    if method == "extractive" or not results:
        return _extractive_summary(query, results)

    # TODO: 외부 LLM (OpenAI, Claude 등) 연동 시 사용
    return _llm_summary(query, results)


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


def _llm_summary(query: str, results: List[dict]) -> str:
    """추상 요약: LLM API를 호출하여 답변을 생성합니다.

    이 함수는 외부 LLM (OpenAI, Anthropic, Ollama 등)이
    설정되어 있을 때 사용됩니다. 현재는 플레이스홀더입니다.
    """
    # 실제 LLM 연동 시 아래와 같은 형태로 구현:
    #
    # import openai
    # context = "\n\n".join(
    #     f"[{i+1}] {r['title']}\n{r['content'][:500]}"
    #     for i, r in enumerate(results[:5])
    # )
    # prompt = (
    #     f"질문: {query}\n\n"
    #     f"아래 정보를 바탕으로 답변해 주세요:\n{context}\n\n"
    #     f"답변:"
    # )
    # response = openai.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # return response.choices[0].message.content

    raise NotImplementedError(
        "추상 요약(abstractive summarization)은 현재 구현되지 않았습니다. "
        "openai 또는 anthropic API 키를 등록하거나 "
        "method='extractive'를 사용하세요."
    )


def generate_answer(
    query: str,
    results: List[dict],
    include_sources: bool = True,
) -> str:
    """검색 결과를 바탕으로 end-user용 답변 문자열을 생성합니다."""
    summary = summarize_search_results(query, results, method="extractive")

    if not include_sources or not results:
        return summary

    source_lines: List[str] = [
        "\n\n**출처:**",
    ]
    for idx, r in enumerate(results[:5], 1):
        source_lines.append(f"{idx}. [{r.get('title', 'Untitled')}]({r.get('url', '')})")

    return summary + "\n".join(source_lines)
