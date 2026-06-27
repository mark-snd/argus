"""SNDWorks AI Gateway (DeepSeek + Kimi) 연동 클라이언트."""

import os
from typing import List, Optional

from openai import AsyncOpenAI

# 기본 설정 ──────────────────────────────────────────────
DEFAULT_BASE_URL = "https://ai.sndworks.ai/deepseek"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_LLM_TIMEOUT = 30.0

# 사용자 환경변수 우선, 없으면 기본값
BASE_URL = os.getenv("SNDWORKS_BASE_URL", DEFAULT_BASE_URL)
API_KEY = os.getenv("SNDWORKS_API_KEY", "")
MODEL = os.getenv("SNDWORKS_MODEL", DEFAULT_MODEL)


class LLMClient:
    """OpenAI 호환 SNDWorks 게이트웨이 클라이언트."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_LLM_TIMEOUT,
    ):
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.api_key = api_key or API_KEY
        self.model = model or MODEL
        self.timeout = timeout

        # 키가 없어도 클라이언트는 생성되나, 호출 시 에러 발생
        self._client: Optional[AsyncOpenAI] = None

    @property
    def available(self) -> bool:
        """API 키가 설정되어 있으면 True."""
        return bool(self.api_key and self.api_key.strip() not in ("", "your-gateway-key-here"))

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.available:
                raise RuntimeError(
                    "SNDWORKS_API_KEY 환경변수가 설정되지 않았습니다. "
                    "~/argus/.env 파일에 키를 입력 후 서버를 재시작하세요."
                )
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._client

    async def summarize(
        self,
        query: str,
        results: List[dict],
        thinking: bool = True,
        reasoning_effort: Optional[str] = "high",
    ) -> str:
        """검색 결과를 바탕으로 LLM 요약 답변을 생성합니다."""
        # 컨텍스트 구성
        context_chunks = []
        for i, r in enumerate(results[:5], 1):
            content = r.get("content", "") or r.get("raw_content", "")
            title = r.get("title", "Untitled")
            context_chunks.append(
                f"[{i}] {title}\n{content[:800]}"  # 최대 800자로 제한
            )

        context = "\n\n".join(context_chunks)

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 웹 검색 결과를 분석하여 사용자의 질문에 답변하는 AI 어시스턴트입니다. "
                    "아래 제공된 검색 결과를 바탕으로, 객관적이고 정확하게 답변을 작성하세요. "
                    "출처 정보를 인용하되, 모호한 내용은 추측하지 마세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"질문: {query}\n\n"
                    f"검색 결과:\n{context}\n\n"
                    f"위 결과를 바탕으로 질문에 답변해 주세요."
                ),
            },
        ]

        # Extra body 설정 (DeepSeek thinking 제어)
        extra_body: dict = {}
        if thinking:
            if "deepseek" in self.base_url:
                extra_body["chat_template_kwargs"] = {
                    "thinking": True,
                    "reasoning_effort": reasoning_effort,
                }
            elif "kimi" in self.base_url:
                extra_body["chat_template_kwargs"] = {"thinking": True}

        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
            extra_body=extra_body if extra_body else None,
        )

        return response.choices[0].message.content or ""


# 싱글톤 인스턴스 (_default_client)
_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
