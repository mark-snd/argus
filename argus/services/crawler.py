"""웹 크롤링 및 콘텐츠 추출 서비스."""

import asyncio
from typing import List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from trafilatura import extract

CrawlerResult = dict  # 반환형 별칭

# 클라이언트 전역 설정(재활용)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)


async def _fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """단일 URL 비동기 HTTP GET 요청."""
    response = await client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response


def _build_result(
    url: str,
    html: str,
    extract_images: bool,
    extract_links: bool,
    extract_depth: str,
) -> CrawlerResult:
    """HTML 문자열을 파싱하여 정형화된 결과 딕셔너리를 반환합니다."""
    soup = BeautifulSoup(html, "lxml")

    # 1. 메타데이터 추출
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    author = (
        soup.find("meta", attrs={"name": "author"})
        or soup.find("meta", attrs={"property": "og:author"})
        or soup.find("meta", attrs={"name": "article:author"})
    )
    author = author.get("content", "").strip() if author else None

    published_date = (
        soup.find("meta", attrs={"name": "date"})
        or soup.find("meta", attrs={"property": "article:published_time"})
        or soup.find("meta", attrs={"name": "publish-date"})
    )
    published_date = published_date.get("content", "").strip() if published_date else None

    # 2. 본문 콘텐츠 추출 (trafilatura 사용)
    raw_content = extract(
        html,
        include_formatting=False,
        include_links=False,
        include_tables=False,
        include_images=False,
        deduplicate=True,
        favor_precision=(extract_depth == "advanced"),
    ) or ""
    raw_content = raw_content.strip()

    # 3. 이미지 추출
    images = None
    if extract_images:
        seen = set()
        img_tags = soup.find_all("img")
        image_urls = []
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if src:
                absolute = urljoin(url, src)
                if absolute not in seen and absolute.startswith(("http://", "https://")):
                    seen.add(absolute)
                    image_urls.append(absolute)
        images = image_urls if image_urls else None

    # 4. 하이퍼링크 추출
    links = None
    if extract_links:
        seen = set()
        anchor_tags = soup.find_all("a", href=True)
        link_urls = []
        for a in anchor_tags:
            absolute = urljoin(url, a["href"])
            if absolute not in seen and absolute.startswith(("http://", "https://")):
                seen.add(absolute)
                link_urls.append(absolute)
        links = link_urls if link_urls else None

    return {
        "url": url,
        "raw_content": raw_content,
        "title": title,
        "author": author,
        "published_date": published_date,
        "images": images,
        "links": links,
    }


async def _extract_single(
    client: httpx.AsyncClient,
    url: str,
    extract_images: bool,
    extract_links: bool,
    extract_depth: str,
) -> CrawlerResult:
    """개별 URL에 대한 크롤링/추출 작업."""
    response = await _fetch(client, url)
    html = response.text
    result = _build_result(url, html, extract_images, extract_links, extract_depth)
    result["_success"] = True
    return result


async def extract_urls(
    urls: List[str],
    include_images: bool = False,
    include_links: bool = False,
    extract_depth: str = "basic",
) -> tuple[List[CrawlerResult], List[str]]:
    """여러 URL의 콘텐츠를 병렬로 추출합니다.

    Returns
    -------
    tuple
        (성공한 결과 목록, 실패한 URL 목록)
    """
    results: List[CrawlerResult] = []
    failed: List[str] = []

    async with httpx.AsyncClient(
        headers=_HEADERS,
        timeout=_TIMEOUT,
        limits=_LIMITS,
    ) as client:
        tasks = [
            _extract_single(
                client, url, include_images, include_links, extract_depth
            )
            for url in urls
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for url, resp in zip(urls, responses):
        if isinstance(resp, Exception):
            failed.append(url)
        else:
            results.append(resp)

    return results, failed


async def fetch_page(url: str) -> dict:
    """단일 페이지를 가장 가볍게 가져와 메타 정보를 반환합니다 (검색 결과용)."""
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, timeout=_TIMEOUT, limits=_LIMITS
        ) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        title = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else url
        )

        snippet = extract(
            response.text,
            include_formatting=False,
            include_links=False,
            include_tables=False,
            include_images=False,
            target_len=300,
            favor_recall=True,
        ) or ""
        snippet = snippet.strip().replace("\n", " ")
        snippet = snippet[:500]  # 최대 500자 제한

        return {
            "url": url,
            "title": title,
            "snippet": snippet,
        }
    except Exception as exc:  # 크롤링 실패 시 URL 기본 정보만 반환
        return {
            "url": url,
            "title": url,
            "snippet": "",
            "_error": str(exc),
        }
