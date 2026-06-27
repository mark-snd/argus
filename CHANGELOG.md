# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-28

### Added
- **LLM 기반 AI 요약 답변** — DeepSeek v4 Pro / Kimi k2.6 연동 (SNDWorks Gateway)
- `POST /v1/search?include_answer=true` 시 LLM이 검색 결과를 종합하여 추상 요약 생성
- 자동 fallback: API 키 없으면 규칙 기반 추출 요약으로 대체
- `.env` 기반 환경변수 설정 (`SNDWORKS_API_KEY`, `SNDWORKS_BASE_URL`, `SNDWORKS_MODEL`)
- `argus/services/llm_client.py` — OpenAI 호환 SNDWorks Gateway 클라이언트
- `extra_body`를 통한 DeepSeek Thinking 제어 (`reasoning_effort: high`)

### Changed
- `summarizer.py` 전면 개편: `async` 기반, `auto` / `extractive` / `abstractive` 모드 지원
- `search.py`, `answer.py` 라우터를 `async` 요약 함수에 맞게 수정

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
