import asyncio
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from workers import WorkerEntrypoint

from chat_page import CHAT_PAGE_HTML
from nim import DEFAULT_BASE_URL, DEFAULT_MODEL, stream_chat_completion
from rag import build_messages
from rate_limiter import RateLimiter
from schemas import ChatRequest

app = FastAPI(title="AI Chat Worker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

_limiter: RateLimiter | None = None


def _get_limiter(env) -> RateLimiter:
    global _limiter
    if _limiter is None:
        interval = float(getattr(env, "RATE_LIMIT_SECONDS", None) or 5.0)
        max_queue = int(getattr(env, "RATE_LIMIT_MAX_QUEUE", None) or 5)
        _limiter = RateLimiter(interval=interval, max_queue=max_queue)
    return _limiter


def _client_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    if request.client is not None:
        return request.client.host
    return "unknown"


def _config(env, body: ChatRequest) -> tuple[str, str]:
    base_url = getattr(env, "NIM_BASE_URL", None) or DEFAULT_BASE_URL
    model = body.model or getattr(env, "NIM_MODEL", None) or DEFAULT_MODEL
    return base_url, model


@app.get("/", response_class=HTMLResponse)
async def chat_page():
    return CHAT_PAGE_HTML


@app.get("/health")
async def health(request: Request):
    env = request.scope["env"]
    return {
        "status": "ok",
        "model": getattr(env, "NIM_MODEL", None) or DEFAULT_MODEL,
        "api_key_configured": bool(getattr(env, "NVAPI_KEY", "")),
    }


@app.post("/chat")
async def chat(body: ChatRequest, request: Request):
    env = request.scope["env"]
    api_key = getattr(env, "NVAPI_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="NVAPI_KEY secret is not configured")

    ip = _client_ip(request)
    limiter = _get_limiter(env)
    delay = await limiter.acquire(ip)
    if delay is None:
        raise HTTPException(
            status_code=429,
            detail="Rate limited: too many queued messages for this IP. Try again later.",
        )

    return StreamingResponse(
        _sse_stream(env, limiter, ip, delay, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _sse_stream(env, limiter: RateLimiter, ip: str, delay: float, body: ChatRequest):
    try:
        if delay > 0:
            yield f"event: queued\ndata: {json.dumps({'wait_seconds': delay})}\n\n"
            await asyncio.sleep(delay)

        base_url, model = _config(env, body)
        messages = build_messages(body.context, body.question)

        async for chunk in stream_chat_completion(
            base_url=base_url,
            api_key=env.NVAPI_KEY,
            model=model,
            messages=messages,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
            top_p=body.top_p,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
    finally:
        if delay > 0:
            await limiter.release(ip)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)