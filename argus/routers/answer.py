"""POST /answer 엔드포인트 — 검색 기반 Q&A."""

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from argus.schemas import (
    AnswerRequest,
    AnswerResponse,
    SearchDepth,
    SourceReference,
)
from argus.services.search_engine import perform_search
from argus.services.summarizer import generate_answer

router = APIRouter(tags=["Answer"])


@router.post(
    "/answer",
    response_model=AnswerResponse,
    summary="검색 기반 AI 답변",
    description="""
    질문에 대해 웹 검색을 수행하고, 검색 결과를 종합하여 AI 답변을 생성합니다.
    Tavily의 `/answer`와 동일한 동작입니다.
    """,
    response_description="질문에 대한 AI 생성 답변과 출처",
)
async def answer(request: AnswerRequest) -> AnswerResponse:
    """검색 결과를 종합하여 질문에 대한 답변을 생성합니다."""
    start = time.perf_counter()

    # 1. 검색 수행
    try:
        search_results = await perform_search(
            query=request.query,
            max_results=request.max_results,
            include_raw_content=(request.search_depth == SearchDepth.ADVANCED),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"검색 실패: {exc}",
        ) from exc

    # 2. 답변 생성
    try:
        answer_text = generate_answer(
            query=request.query,
            results=search_results,
            include_sources=request.include_sources,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"답변 생성 실패: {exc}",
        ) from exc

    # 3. 출처 정보 구성
    sources: Optional[List[SourceReference]] = None
    if request.include_sources and search_results:
        sources = [
            SourceReference(
                title=r["title"],
                url=r["url"],
                score=r["score"],
            )
            for r in search_results[:5]
        ]

    # 4. 이미지 (현재는 검색에서 미지원)
    images: Optional[List[str]] = None

    response_time = time.perf_counter() - start

    return AnswerResponse(
        query=request.query,
        answer=answer_text,
        sources=sources,
        images=images,
        response_time=round(response_time, 3),
    )
