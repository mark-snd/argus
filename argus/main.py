"""FastAPI 애플리케이션 진입점."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from argus.routers import search, extract, answer

app = FastAPI(
    title="Argus",
    description="""
    **Argus**는 Tavily API를 오마주한 AI-optimized 검색 API 서버입니다.

    AI 에이전트와 LLM 애플리케이션이 바로 사용할 수 있도록
    정제된 JSON 형태의 검색 결과를 제공합니다.

    ## 주요 엔드포인트

    * **/search** — AI-optimized 웹 검색
    * **/extract** — URL에서 콘텐츠 추출
    * **/answer** — 검색 기반 Q&A (요약 답변 포함)
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Argus Support",
    },
)

# CORS 설정 — AI 에이전트/프론트엔드에서 자유롭게 호출 가능
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(search.router, prefix="/v1")
app.include_router(extract.router, prefix="/v1")
app.include_router(answer.router, prefix="/v1")


@app.get("/", tags=["Health"], summary="루트 헬스체크")
async def root() -> dict:
    """API 서버 상태 확인."""
    return {
        "service": "Argus",
        "version": "0.1.0",
        "status": "healthy",
        "endpoints": {
            "search": "/v1/search",
            "extract": "/v1/extract",
            "answer": "/v1/answer",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"], summary="헬스체크")
async def health() -> dict:
    """서버가 정상 동작 중인지 확인합니다."""
    return {"status": "ok"}
