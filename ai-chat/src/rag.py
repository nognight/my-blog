"""Simple RAG without a database.

The client sends ``context`` + ``question`` in the JSON payload; we stuff the
context into the prompt and let the model answer strictly from it. No vector
DB, no retrieval — the "retrieval" step is the caller's responsibility.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a precise assistant. Answer the user's question using ONLY the "
    "information provided in the CONTEXT section. If the CONTEXT does not "
    "contain the answer, say that you don't know. Never invent facts, and "
    "answer in the same language as the question."
)


def build_messages(context: str, question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}",
        },
    ]