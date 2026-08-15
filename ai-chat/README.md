# AI Chat Worker

A **FastAPI + asyncio** AI chat bot deployed on **Cloudflare Workers** (Python
Workers, open beta). It receives a JSON payload with `context` and `question`,
calls the **NVIDIA NIM** chat-completions API, and streams the answer back to
the client as **Server-Sent Events (SSE)**.

- Simple RAG **without a database**: the caller passes retrieved context in the
  request body; the worker stuffs it into the prompt.
- **Per-IP rate limit**: one message every 5 seconds. Requests that arrive
  inside the window are put into an asyncio queue and deferred until their slot
  opens. If more than 5 messages are already queued for an IP, the request is
  rejected with `429`.
- Response is streamed over SSE (`text/event-stream`), forwarded chunk-by-chunk
  from NIM's streaming API.

## Architecture

```
client ──POST /chat {context, question}──▶ Cloudflare Worker (Python + FastAPI)
                                               │ 1. per-IP rate limit (5s window)
                                               │ 2. defer to queue if inside window
                                               │ 3. stream NIM answer over SSE
client ◀────────── SSE stream ────────────────┤
```

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.12+)
- [Node.js](https://nodejs.org/) 18+ (for wrangler)
- An NVIDIA API key (for the hosted NIM API) — get one at
  <https://org.ngc.nvidia.com/setup/api-key>. A self-hosted NIM can be used by
  overriding `NIM_BASE_URL`.

## Setup

```bash
npm install              # installs wrangler
cp .dev.vars.example .dev.vars   # add your NVAPI_KEY for local dev
```

## Local development

```bash
npm run dev              # uv run pywrangler dev
```

Open the printed URL (`http://localhost:8787`), paste some context into the
textarea, ask a question, and watch the answer stream in. Rapid-fire the Send
button to see the `queued` SSE event (requests are deferred ~5s) and the `429`
rejection when the queue is full.

### API

`POST /chat` — body:

```json
{
  "context": "NVIDIA NIM is a set of optimized microservices...",
  "question": "What is NIM?",
  "model": "nvidia/llama-3.1-nemotron-nano-8b-v1",
  "max_tokens": 512,
  "temperature": 0.7
}
```

`model`, `max_tokens` and `temperature` are optional (defaults come from worker
vars). The response is an SSE stream:

```
event: queued
data: {"wait_seconds": 2.5}

data: {"id":"cmpl-...","object":"chat.completion.chunk","choices":[...]}
...
data: [DONE]
```

Other endpoints: `GET /` (chat test page), `GET /health`.

## Deploy

```bash
npm run deploy                 # uv run pywrangler deploy
wrangler secret put NVAPI_KEY  # then set the secret on the deployed worker
```

Configuration lives in `wrangler.jsonc`:

| Variable                 | Default                                    | Purpose                        |
| ------------------------ | ------------------------------------------ | ------------------------------ |
| `NIM_BASE_URL`           | `https://integrate.api.nvidia.com`         | NIM endpoint (hosted or self)  |
| `NIM_MODEL`              | `nvidia/llama-3.1-nemotron-nano-8b-v1`     | Default model id               |
| `NIM_MAX_TOKENS`         | `512`                                      | Default max tokens             |
| `RATE_LIMIT_SECONDS`     | `5`                                        | Per-IP message interval        |
| `RATE_LIMIT_MAX_QUEUE`   | `5`                                        | Max queued messages per IP     |
| `NVAPI_KEY` (secret)     | —                                          | NIM API key (`Authorization: Bearer`) |

## Notes & caveats

- **Rate limiter scope**: the limiter lives in the Worker isolate that handled
  the request, so it is consistent per-isolate, not across all Cloudflare edge
  locations. Fine for a demo / low-traffic bot. For strict global enforcement,
  swap `src/rate_limiter.py` for a Durable Object per IP (same
  `acquire`/`release` interface).
- **Queue = deferred execution**: a "queued" request is not stored — it simply
  waits until its 5-second slot opens, then runs. If the client disconnects,
  the queued slot is released (handled in `finally`).
- Python Workers are in **open beta**; you need the `python_workers`
  compatibility flag (already set in `wrangler.jsonc`).
- NIM uses OpenAI-compatible endpoints, so swapping in any OpenAI-compatible
  provider (OpenAI, Together, ...) only requires changing `NIM_BASE_URL` and
  the model name.