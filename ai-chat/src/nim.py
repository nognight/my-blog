"""Async client for the NVIDIA NIM chat-completions API (OpenAI-compatible).

Targets the hosted NVIDIA API (https://integrate.api.nvidia.com) by default;
point NIM_BASE_URL at a self-hosted NIM (e.g. http://localhost:8000) to use a
local container instead. Uses httpx, which Python Workers patch to run on the
Fetch API — async I/O only, which is exactly what we need.
"""

from __future__ import annotations

from typing import AsyncIterator

import httpx

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com"
DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
    }


async def stream_chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> AsyncIterator[str]:
    """Stream a chat completion from NIM.

    Yields the payload of each SSE ``data:`` line as a raw string (JSON chunks,
    ending with ``[DONE]``). The caller is responsible for re-emitting them as
    Server-Sent Events.
    """
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        async with client.stream(
            "POST", url, headers=_headers(api_key), json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("data: "):
                    yield line[len("data: "):]