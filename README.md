# Argus

> Argus라는 이름은 그리스 신화 속 백 개의 눈을 가진 거인 아르거스 판옵테스(Argus Panoptes)에서 따왔습니다. 그는 결코 모든 눈을 동시에 감지 않아 무엇 하나 그의 감시를 피해갈 수 없었습니다. Argus API 역시 웹 전역을 끊임없이 감시하고 수집하여, AI 에이전트가 놓치는 정보 없이 정제된 검색 결과를 바로 활용할 수 있게 해줍니다.
>
> Argus is named after Argus Panoptes, the all-seeing giant of Greek mythology whose body was covered with a hundred eyes, making it impossible for anything to escape his watch. Just as Argus never closed all his eyes at once, this API tirelessly watches, gathers, and surfaces information from across the web — delivering AI-ready search results so your agents never miss what matters.

[Tavily API](https://tavily.com)를 오마주한 AI-optimized 검색 API 서버입니다.

AI 에이전트와 LLM 애플리케이션이 바로 사용할 수 있도록 정제된 JSON 형태의 검색 결과를 제공합니다.

---

## 빠른 시작

### 1. 설치

```bash
pip install -r requirements.txt
```

### 2. 실행

```bash
uvicorn argus.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 주요 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/v1/search` | POST | AI-optimized 웹 검색 |
| `/v1/extract` | POST | URL에서 콘텐츠 추출 |
| `/v1/answer` | POST | 검색 기반 Q&A |

---

## 사용 예시

### `/search` — 웹 검색

```bash
curl -X POST http://localhost:8000/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FastAPI 성능 최적화 팁",
    "max_results": 3,
    "include_answer": true,
    "search_depth": "advanced"
  }'
```

**응답 예시:**

```json
{
  "query": "FastAPI 성능 최적화 팁",
  "answer": "FastAPI 성능을 최적화하려면 비동기 I/O를 활용하고, ORM 쿼리를 최적화하며...",
  "results": [
    {
      "title": "FastAPI Best Practices",
      "url": "https://example.com/fastapi-tips",
      "content": "async/await를 적극 활용하고...",
      "score": 0.95
    }
  ],
  "response_time": 1.234
}
```

### `/extract` — URL 콘텐츠 추출

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://news.ycombinator.com/item?id=12345"
    ],
    "extract_depth": "advanced",
    "include_images": true
  }'
```

**응답 예시:**

```json
{
  "results": [
    {
      "url": "https://news.ycombinator.com/item?id=12345",
      "raw_content": "Hacker News 에서의 토론...",
      "title": "Show HN: Argus",
      "author": "user123",
      "published_date": "2024-06-27",
      "images": null,
      "links": ["https://github.com/..."]
    }
  ],
  "failed_results": null,
  "response_time": 0.856
}
```

### `/answer` — 검색 기반 Q&A

```bash
curl -X POST http://localhost:8000/v1/answer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2026년 AI 트렌드는?",
    "max_results": 5
  }'
```

**응답 예시:**

```json
{
  "query": "2026년 AI 트렌드는?",
  "answer": "2026년 AI 트렌드는 멀티모달 모델의 대중화...",
  "sources": [
    {
      "title": "AI Trends 2026",
      "url": "https://example.com/ai-trends",
      "score": 0.92
    }
  ],
  "response_time": 2.341
}
```

---

## CLI 도구

```bash
python3 argus-cli.py search "FastAPI 성능 팁" -n 3 --answer --depth advanced
python3 argus-cli.py answer "2026년 AI 트렌드는?" -n 5
python3 argus-cli.py extract "https://example.com" --depth advanced
```

기본 API 서버는 맥미니(`http://192.168.0.113:8000`)을 사용합니다.

---

## 아키텍처

Argus는 요청 → 라우터 → 서비스 → 외부 데이터 소스 → 응답 파이프라인으로 동작합니다.

```
                ┌─────────────┐
                │   Client    │
                │  argus-cli  │
                │ curl, etc   │
                └──────┬──────┘
                       │
                       ▼
             ┌──────────────────┐
             │  FastAPI Router  │
             │  /v1/search      │
             │  /v1/extract     │
             │  /v1/answer      │
             └────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│Search Engine│ │   Crawler   │ │  Summarizer  │
│ DuckDuckGo  │ │ trafilatura │ │ (extractive) │
│ HTML API    │ │ BeautifulSoup│ │              │
└──────┬──────┘ └──────┬──────┘ └──────┬───────┘
       │              │               │
       ▼              ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Web Sources │ │ Raw Content  │ │ JSON Response│
└──────────────┘ └──────────────┘ └──────────────┘
```

### 런타임 흐름

| 엔드포인트 | 흐름 | 핵심 함수 |
|-----------|------|----------|
| `POST /v1/search` | DuckDuckGo 검색 → 각 URL 크롤링 → 스니펫/점수 생성 | `perform_search()` → `fetch_page()` |
| `POST /v1/extract` | 여러 URL 병렬 크롤링 → 본문 + 메타데이터 추출 | `extract_urls()` → `_extract_single()` |
| `POST /v1/answer` | DuckDuckGo 검색 → 검색 결과 종합 → 답변 생성 | `perform_search()` → `generate_answer()` |

---

## 프로젝트 구조

```
.
├── argus/
│   ├── routers/
│   │   ├── search.py       # /search 엔드포인트
│   │   ├── extract.py      # /extract 엔드포인트
│   │   └── answer.py       # /answer 엔드포인트
│   ├── services/
│   │   ├── crawler.py      # 웹 크롤링 / 콘텐츠 추출
│   │   ├── search_engine.py # DuckDuckGo 기반 검색
│   │   └── summarizer.py   # 추출 요약 / 답변 생성
│   ├── schemas.py          # Pydantic 데이터 모델
│   └── main.py             # FastAPI 앱 진입점
├── requirements.txt
├── argus-cli.py
└── README.md
```

---

## 환경변수 (선택)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `UVICORN_HOST` | 바인딩 호스트 | `0.0.0.0` |
| `UVICORN_PORT` | 바인딩 포트 | `8000` |

---

## 향후 확장 아이디어

1. **LLM 연동**: OpenAI / Anthropic API를 연동해 `abstractive summarization` 활성화
2. **검색 백엔드 추가**: Google Custom Search API, Bing API, Brave Search API 등 교체 가능하게 Adapter 패턴 적용
3. **캐싱**: Redis 등으로 검색 결과 캐싱
4. **인증**: API Key 기반 Rate Limiting
5. **이미지 검색**: 이미지 결과 포함 (현재는 텍스트 기반)

---

## 라이선스

MIT
