"""검색 백엔드 인터페이스 및 구현체."""

import asyncio
import re
from typing import List, Optional
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup

from .crawler import fetch_page

# HTTP 클라이언트 전역 설정
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}
_TIMEOUT = httpx.Timeout(20.0, connect=5.0)
_DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"


class SearchResultItem:
    """검색 결과 간소화 모델(내부 사용)."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "duckduckgo",
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source


async def _search_duckduckgo(
    query: str,
    max_results: int = 10,
) -> List[SearchResultItem]:
    """DuckDuckGo HTML 엔드포인트를 이용한 비동기 검색."""
    params = {"q": query}

    async with httpx.AsyncClient(
        headers=_HEADERS, timeout=_TIMEOUT
    ) as client:
        response = await client.post(_DUCKDUCKGO_URL, data=params)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    items: List[SearchResultItem] = []

    for result in soup.select(".result"):
        title_tag = result.select_one(".result__title a")
        snippet_tag = result.select_one(".result__snippet")
        url_tag = result.select_one(".result__url")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        raw_href = title_tag.get("href", "")

        # DuckDuckGo 리다이렉트 URL 처리
        if raw_href.startswith("/"):
            href = urljoin("https://duckduckgo.com", raw_href)
            # DuckDuckGo 리다이렉트 파라미터에서 실제 URL 추출
            match = re.search(r"uddg=([^&]+)", href)
            if match:
                import urllib.parse
                actual_url = urllib.parse.unquote(match.group(1))
            else:
                actual_url = href
        else:
            actual_url = raw_href

        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        items.append(
            SearchResultItem(
                title=title,
                url=actual_url,
                snippet=snippet,
            )
        )

        if len(items) >= max_results:
            break

    return items


async def perform_search(
    query: str,
    max_results: int = 5,
    include_raw_content: bool = False,
    include_images: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    time_range: Optional[str] = None,
) -> List[dict]:
    """검색을 수행하고 AI-optimized 결과를 반환합니다.

    Parameters
    ----------
    query : str
        검색어
    max_results : int
        최대 결과 수
    include_raw_content : bool
        각 결과에 전체 크롤링 콘텐츠 포함 여부
    include_images : bool
        이미지 포함 여부 (현재 DuckDuckGo HTML API에서는 지원하지 않음)
    include_domains : list[str] | None
        포함할 도메인 목록
    exclude_domains : list[str] | None
        제외할 도메인 목록
    time_range : str | None
        시간 범위 필터 (day, week, month, year)

    Returns
    -------
    list[dict]
        검색 결과 항목 목록
    """
    # 1. 검색어에 시간 필터 추가
    enriched_query = query
    if time_range:
        enriched_query = f"{query} {time_range}"

    # 2. DuckDuckGo에서 검색
    raw_results = await _search_duckduckgo(enriched_query, max_results=max_results * 2)

    # 3. 도메인 필터링
    filtered: List[SearchResultItem] = []
    for item in raw_results:
        domain_match = True
        if include_domains:
            domain_match = any(
                dom in item.url for dom in include_domains
            )
        if exclude_domains:
            domain_match = domain_match and not any(
                dom in item.url for dom in exclude_domains
            )
        if domain_match:
            filtered.append(item)
        if len(filtered) >= max_results:
            break

    # 4. 각 결과에 대해 추가 크롤링 (상세 스니펫 + 원본 콘텐츠)
    tasks = [fetch_page(item.url) for item in filtered]
    page_infos = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[dict] = []
    for item, info in zip(filtered, page_infos):
        if isinstance(info, Exception):
            # 크롤링 실패 시 snippet만 사용
            page_title = item.title
            page_snippet = item.snippet
        else:
            page_title = info.get("title") or item.title
            page_snippet = info.get("snippet") or item.snippet

        # 점수는 간단히 snippet 길이/검색어 포함 여부 기반
        score = _calculate_score(query, item.title, page_snippet)

        result_entry = {
            "title": page_title,
            "url": item.url,
            "content": page_snippet,
            "score": round(score, 3),
        }

        if include_raw_content:
            result_entry["raw_content"] = page_snippet[:2000] if page_snippet else ""

        results.append(result_entry)

    # 점수 기준 내림차순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _calculate_score(query: str, title: str, snippet: str) -> float:
    """간단한 관련성 점수 계산 (0.0 ~ 1.0)."""
    query_words = set(query.lower().split())
    title_lower = title.lower()
    snippet_lower = snippet.lower() if snippet else ""

    score = 0.5  # 기본 점수

    # 제목에 검색어 포함 시 높은 점수
    if any(word in title_lower for word in query_words):
        score += 0.3

    # 스니펫에 검색어 포함 시 중간 점수
    if any(word in snippet_lower for word in query_words):
        score += 0.15

    # 스니펫 길이 보너스 (정보가 많을 수록)
    snippet_len = len(snippet_lower)
    if snippet_len > 200:
        score += 0.05

    return min(score, 1.0)
