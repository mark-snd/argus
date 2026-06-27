# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-28

### Added
- FastAPI 기반 Tavily-style 검색 API 서버
- `POST /v1/search` — AI-optimized 웹 검색 (DuckDuckGo HTML 기반)
- `POST /v1/extract` — URL 콘텐츠 추출 (trafilatura + BeautifulSoup)
- `POST /v1/answer` — 검색 기반 Q&A (규칙 기반 요약)
- Pydantic 스키마 기반 요청/응답 검증
- CLI 도구 `argus-cli.py` (Python httpx 기반)
- 맥미니 launchd 자동 실행 설정
- CORS — 모든 오리진 허용
