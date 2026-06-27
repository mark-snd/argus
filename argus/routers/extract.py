"""POST /extract 엔드포인트 — 특정 URL에서 콘텐츠 추출."""

import time
from typing import List

from fastapi import APIRouter, HTTPException

from argus.schemas import (
    ExtractRequest,
    ExtractResponse,
    ExtractedContent,
)
from argus.services.crawler import extract_urls

router = APIRouter(tags=["Extract"])


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="URL 콘텐츠 추출",
    description="""
    특정 URL에서 HTML을 크롤링하고, 순수 텍스트 + 메타데이터를 추출합니다.
    - `basic` 모드: 메인 본문 추출
    - `advanced` 모드: 전체 페이지 심층 분석
    """,
    response_description="추출된 콘텐츠 및 실패한 URL 목록",
)
async def extract(request: ExtractRequest) -> ExtractResponse:
    """URL 목록의 콘텐츠를 병렬로 추출합니다."""
    start = time.perf_counter()

    urls = [str(u) for u in request.urls]

    try:
        raw_results, failed = await extract_urls(
            urls=urls,
            include_images=request.include_images,
            include_links=(request.extract_depth.value == "advanced"),
            extract_depth=request.extract_depth.value,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"크롤링 실패: {exc}",
        ) from exc

    extracted_results: List[ExtractedContent] = []
    for item in raw_results:
        extracted_results.append(
            ExtractedContent(
                url=item["url"],
                raw_content=item["raw_content"],
                title=item.get("title"),
                author=item.get("author"),
                published_date=item.get("published_date"),
                images=item.get("images"),
                links=item.get("links"),
            )
        )

    response_time = time.perf_counter() - start

    return ExtractResponse(
        results=extracted_results,
        failed_results=failed if failed else None,
        response_time=round(response_time, 3),
    )
