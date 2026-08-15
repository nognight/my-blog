from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """JSON body expected by POST /chat.

    Minimal RAG contract: the client supplies the retrieved context and the
    question; the worker builds the prompt and streams the model's answer.
    """

    context: str = Field(
        ...,
        min_length=1,
        description="Retrieved context passages the model should answer from",
    )
    question: str = Field(
        ...,
        min_length=1,
        description="The user's question about the context",
    )
    model: str | None = Field(
        default=None,
        description="NIM model id; defaults to the NIM_MODEL worker variable",
    )
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class QueueStatus(BaseModel):
    """Payload of the ``queued`` SSE event, emitted while a request waits."""

    wait_seconds: float
    position: int