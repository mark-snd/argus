"""Argus - Pydantic data models."""

from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SearchDepth(str, Enum):
    """검색 깊이 옵션."""

    BASIC = "basic"
    ADVANCED = "advanced"


class IncludeImage(str, Enum):
    """이미지 포함 옵션."""

    NONE = "none"
    THUMBNAIL = "thumbnail"
    FULL = "full"


class TimeRange(str, Enum):
    """검색 시간 범위 필터."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SearchResultContent(BaseModel):
    """개별 검색 결과 항목."""

    title: str = Field(..., description="검색 결과의 제목")
    url: HttpUrl = Field(..., description="검색 결과의 URL")
    content: str = Field(..., description="AI-optimized 요약 내용")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="검색어와의 관련성 점수 (0.0 ~ 1.0)",
    )
    raw_content: Optional[str] = Field(
        default=None,
        description="전체 원본 크롤링 콘텐츠 (include_raw_content=True 시)",
    )
    published_date: Optional[str] = Field(
        default=None,
        description="콘텐츠 발행일 (ISO 8601 형식)",
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="관련 이미지 URL 목록",
    )


class SearchRequest(BaseModel):
    """POST /search 요청 본문."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="검색어",
    )
    search_depth: SearchDepth = Field(
        default=SearchDepth.BASIC,
        description="검색 깊이: basic(빠른 검색) 또는 advanced(심층 분석)",
    )
    topic: Optional[str] = Field(
        default="general",
        description="검색 주제: general, news, finance 등",
    )
    days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="최근 N일 이내 결과만 필터링",
    )
    time_range: Optional[TimeRange] = Field(
        default=None,
        description="시간 범위 필터: day, week, month, year",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="반환할 최대 결과 수",
    )
    include_images: IncludeImage = Field(
        default=IncludeImage.NONE,
        description="이미지 포함 수준",
    )
    include_answer: bool = Field(
        default=False,
        description="True 시 AI 요약 답변(answer)을 results와 함께 반환",
    )
    include_raw_content: bool = Field(
        default=False,
        description="True 시 각 결과에 전체 원본 콘텐츠 포함",
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="검색에 포함할 도메인 목록",
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="검색에서 제외할 도메인 목록",
    )


class SearchResponse(BaseModel):
    """POST /search 응답."""

    query: str = Field(..., description="원본 검색어")
    answer: Optional[str] = Field(
        default=None,
        description="AI 생성 요약 답변 (include_answer=True 시)",
    )
    results: List[SearchResultContent] = Field(
        default_factory=list,
        description="검색 결과 목록",
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="관련 이미지 URL 목록",
    )
    response_time: float = Field(
        ...,
        description="응답 처리 시간(초)",
    )


class ExtractRequest(BaseModel):
    """POST /extract 요청 본문."""

    urls: List[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="콘텐츠를 추출할 URL 목록 (최대 20개)",
    )
    include_images: bool = Field(
        default=False,
        description="True 시 페이지 내 이미지도 함께 추출",
    )
    extract_depth: SearchDepth = Field(
        default=SearchDepth.BASIC,
        description="추출 깊이: basic(메인 콘텐츠) 또는 advanced(전체 페이지 분석)",
    )


class ExtractedContent(BaseModel):
    """개별 URL에서 추출된 콘텐츠."""

    url: HttpUrl = Field(..., description="원본 URL")
    raw_content: str = Field(..., description="추출된 순수 텍스트 콘텐츠")
    title: Optional[str] = Field(
        default=None,
        description="페이지 제목",
    )
    author: Optional[str] = Field(
        default=None,
        description="작성자 정보",
    )
    published_date: Optional[str] = Field(
        default=None,
        description="발행일",
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="페이지 내 이미지 URL 목록",
    )
    links: Optional[List[str]] = Field(
        default=None,
        description="페이지 내 하이퍼링크 목록",
    )


class ExtractResponse(BaseModel):
    """POST /extract 응답."""

    results: List[ExtractedContent] = Field(
        default_factory=list,
        description="추출된 콘텐츠 목록",
    )
    failed_results: Optional[List[str]] = Field(
        default=None,
        description="추출에 실패한 URL 목록",
    )
    response_time: float = Field(
        ...,
        description="응답 처리 시간(초)",
    )


class AnswerRequest(BaseModel):
    """POST /answer 요청 본문."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="질문",
    )
    search_depth: SearchDepth = Field(
        default=SearchDepth.ADVANCED,
        description="검색 깊이: basic 또는 advanced",
    )
    include_sources: bool = Field(
        default=True,
        description="True 시 답변에 출처 URL 포함",
    )
    include_images: bool = Field(
        default=False,
        description="True 시 관련 이미지 포함",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="참조할 검색 결과 최대 수",
    )


class SourceReference(BaseModel):
    """답변의 출처 참조 정보."""

    title: str = Field(..., description="출처 제목")
    url: HttpUrl = Field(..., description="출처 URL")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="관련성 점수",
    )


class AnswerResponse(BaseModel):
    """POST /answer 응답."""

    query: str = Field(..., description="원본 질문")
    answer: str = Field(..., description="AI 생성 답변")
    sources: Optional[List[SourceReference]] = Field(
        default=None,
        description="답변의 출처 목록 (include_sources=True 시)",
    )
    images: Optional[List[str]] = Field(
        default=None,
        description="관련 이미지 URL 목록 (include_images=True 시)",
    )
    response_time: float = Field(
        ...,
        description="응답 처리 시간(초)",
    )
