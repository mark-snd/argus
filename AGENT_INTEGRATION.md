# Argus — Agent Integration Guide

> 맥미니(Mark-Macmini, 192.168.0.113)에서 실행 중인 Argus 연동 가이드.
> 생성일: 2026-06-28

---

## 1. 서버 접근 정보

| 항목 | 값 |
|------|-----|
| **Base URL (맥미니 내부)** | `http://localhost:8000` |
| **Base URL (같은 네트워크)** | `http://192.168.0.113:8000` |
| **Docs (Swagger UI)** | `http://localhost:8000/docs` |
| **Health Check** | `GET http://localhost:8000/health` |

서버는 `launchd`로 등록되어 있어 맥미니 재부팅 시 자동으로 시작됩니다.

---

## 2. 엔드포인트 요약

### POST /v1/search — AI-Optimized 웹 검색

검색어를 입력하면 웹 검색 결과를 AI-friendly JSON으로 반환합니다.

**요청 예시 (JSON body):**
```json
{
  "query": "FastAPI 성능 최적화",
  "max_results": 5,
  "include_answer": true,
  "search_depth": "advanced"
}
```

**선택 파라미터:**
- `max_results` (int, 기본 5): 1~20
- `search_depth` (string): `"basic"` | `"advanced"`
- `include_answer` (bool, 기본 false): AI 요약 답변 포함 여부
- `include_raw_content` (bool, 기본 false): 각 결과 전체 콘텐츠 포함
- `time_range` (string | null): `"day"` | `"week"` | `"month"` | `"year"`
- `include_domains` (string[]): 특정 도메인만 검색
- `exclude_domains` (string[]): 특정 도메인 제외

---

### POST /v1/extract — URL 콘텐츠 추출

특정 URL에서 텍스트와 메타데이터를 추출합니다.

**요청 예시:**
```json
{
  "urls": ["https://example.com/article"],
  "extract_depth": "advanced",
  "include_images": true
}
```

**선택 파라미터:**
- `urls` (string[]): 추출할 URL 목록 (최대 20개)
- `extract_depth` (string): `"basic"` | `"advanced"`
- `include_images` (bool): 이미지도 함께 추출

---

### POST /v1/answer — 검색 기반 Q&A

질문에 대해 검색하고, 결과를 종합하여 AI 답변을 생성합니다.

**요청 예시:**
```json
{
  "query": "2026년 AI 트렌드는?",
  "max_results": 5,
  "include_sources": true
}
```

**선택 파라미터:**
- `max_results` (int, 기본 5): 1~20
- `include_sources` (bool, 기본 true): 출처 URL 포함
- `include_images` (bool): 이미지 포함
- `search_depth` (string): `"basic"` | `"advanced"`

---

## 3. Python 연동 예시 (httpx 기반)

```python
import httpx


class ArgusClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(self, query: str, max_results: int = 5, include_answer: bool = True) -> dict:
        resp = await self.client.post(
            f"{self.base_url}/v1/search",
            json={"query": query, "max_results": max_results, "include_answer": include_answer}
        )
        resp.raise_for_status()
        return resp.json()

    async def extract(self, urls: list[str]) -> dict:
        resp = await self.client.post(
            f"{self.base_url}/v1/extract",
            json={"urls": urls, "extract_depth": "advanced"}
        )
        resp.raise_for_status()
        return resp.json()

    async def answer(self, query: str, include_sources: bool = True) -> dict:
        resp = await self.client.post(
            f"{self.base_url}/v1/answer",
            json={"query": query, "include_sources": include_sources}
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


# 사용 예시
async def main():
    client = ArgusClient()
    result = await client.search("FastAPI 성능 팁", max_results=3)
    print(result.get("answer"))
    for r in result.get("results", []):
        print(f"- {r['title']} ({r['url']})")
    await client.close()
```

---

## 4. 환경변수 설정 (권장)

Hermes 설정 파일(예: `.env`)에 추가:

```bash
ARGUS_API_URL=http://localhost:8000
```

---

## 5. File locations on Mac Mini

```
~/ai-search-api/
├── argus/
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── schemas.py           # Pydantic 모델
│   └── services/
│       ├── search_engine.py # 검색 엔진 (DuckDuckGo)
│       ├── crawler.py       # 웹 크롤러
│       └── summarizer.py    # 요약/답변 생성
├── venv/                    # Python 가상환경
└── AGENT_INTEGRATION.md     # 이 파일
```

---

*Last updated: 2026-06-28*
