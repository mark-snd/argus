"""POST /search 엔드포인트 — AI-optimized 웹 검색."""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from argus.schemas import (
    IncludeImage,
    SearchDepth,
    SearchRequest,
    SearchResponse,
    SearchResultContent,
    TimeRange,
)
from argus.services.search_engine import perform_search
from argus.services.summarizer import summarize_search_results

router = APIRouter(tags=["Search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="AI-Optimized 웹 검색",
    description="""
    검색어에 대해 웹 검색을 수행하고, 각 결과를 AI-friendly하게 요약/정제하여 반환합니다.
    - `basic` 모드: 빠른 검색 + 요약 스니펫
    - `advanced` 모드: 더 많은 결과 크롤링 + 심층 요약
    """,
    response_description="검색어 기반 AI-optimized 검색 결과 목록",
)
async def search(request: SearchRequest) -> SearchResponse:
    """검색 요청을 처리하고 AI-optimized 결과를 반환합니다."""
    start = time.perf_counter()

    try:
        results = await perform_search(
            query=request.query,
            max_results=request.max_results,
            include_raw_content=request.include_raw_content,
            include_images=(request.include_images != IncludeImage.NONE),
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains,
            time_range=request.time_range.value if request.time_range else None,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"검색 엔진 접근 실패: {exc}",
        ) from exc

    # advanced 모드: 더 많은 결과를 크롤링하여 요약 강화
    if request.search_depth == SearchDepth.ADVANCED and results:
        # 이미 perform_search 내부에서 fetch_page를 호출했으므로
        # 추가적으로 각 페이지 원본 가져와서 요약 품질 향상 가능
        pass  # 추후 advanced 전용 크롤러로 확장 가능

    # AI 요약 답변 생성
    answer: Optional[str] = None
    if request.include_answer and results:
        answer = summarize_search_results(
            query=request.query,
            results=results,
            method="extractive",
        )

    search_results = [
        SearchResultContent(
            title=r["title"],
            url=r["url"],
            content=r["content"],
            score=r["score"],
            raw_content=r.get("raw_content"),
        )
        for r in results
    ]

    response_time = time.perf_counter() - start

    return SearchResponse(
        query=request.query,
        answer=answer,
        results=search_results,
        response_time=round(response_time, 3),
    )
