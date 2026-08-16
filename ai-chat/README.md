# AI Chat Worker

A **TypeScript** AI chat bot on **Cloudflare Workers**. It receives a JSON
payload with `context` and `question`, calls the **NVIDIA NIM** chat-completions
API, and streams the answer back to the client as **Server-Sent Events (SSE)**.

The worker is pure TypeScript (no Python runtime) so every request stays well
inside the Workers free-tier CPU budget: the SSE relay pipes NIM's raw stream
through a `ReadableStream` and batches writes, avoiding any per-token
processing.

- Simple RAG **without a database**: the caller passes retrieved context in the
  request body; the worker stuffs it into the prompt.
- **Per-IP rate limit**: one message every 5 seconds. Requests that arrive
  inside the window are put into a queue and deferred until their slot opens. If
  more than 5 messages are already queued for an IP, the request is rejected
  with `429`.
- Response is streamed over SSE (`text/event-stream`), forwarded chunk-by-chunk
  from NIM's streaming API.

## Architecture

```
client ──POST /chat {context, question}──▶ Cloudflare Worker (TypeScript)
                                               │ 1. per-IP rate limit (5s window)
                                               │ 2. defer to queue if inside window
                                               │ 3. stream NIM answer over SSE
client ◀────────── SSE stream ────────────────┤
```

## Requirements

- [Node.js](https://nodejs.org/) 18+ (for wrangler)
- An NVIDIA API key (for the hosted NIM API) — get one at
  <https://org.ngc.nvidia.com/setup/api-key>. A self-hosted NIM can be used by
  overriding `NIM_BASE_URL`.

## Setup

```bash
npm install              # installs wrangler + typescript
npm run typecheck        # npx tsc --noEmit
cp .dev.vars.example .dev.vars   # add your NVAPI_KEY for local dev
```

## Local development

```bash
npm run dev              # npx wrangler dev
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
  "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "max_tokens": 4096,
  "temperature": 1.0,
  "top_p": 0.95,
  "reasoning_budget": 4096
}
```

`model`, `max_tokens`, `temperature`, `top_p` and `reasoning_budget` are
optional (defaults come from the worker). The default model has thinking
enabled, so the stream carries `reasoning_content` deltas before the answer.
The response is an SSE stream:

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
npm run deploy                 # npx wrangler deploy
wrangler secret put NVAPI_KEY  # then set the secret on the deployed worker
```

Configuration lives in `wrangler.jsonc`:

| Variable                 | Default                                    | Purpose                        |
| ------------------------ | ------------------------------------------ | ------------------------------ |
| `NIM_BASE_URL`           | `https://integrate.api.nvidia.com`         | NIM endpoint (hosted or self)  |
| `NIM_MODEL`              | `nvidia/nemotron-3.5-lightning-30b-a3b`    | Default model id               |
| `NIM_MAX_TOKENS`         | `4096`                                     | Default max tokens             |
| `RATE_LIMIT_SECONDS`     | `5`                                        | Per-IP message interval        |
| `RATE_LIMIT_MAX_QUEUE`   | `5`                                        | Max queued messages per IP     |
| `NVAPI_KEY` (secret)     | —                                          | NIM API key (`Authorization: Bearer`) |

## Notes & caveats

- **Rate limiter scope**: the limiter lives in the Worker isolate that handled
  the request, so it is consistent per-isolate, not across all Cloudflare edge
  locations. Fine for a demo / low-traffic bot. For strict global enforcement,
  swap the limiter for a Durable Object per IP (same `acquire`/`release`
  interface).
- **Queue = deferred execution**: a "queued" request is not stored — it simply
  waits until its 5-second slot opens, then runs. If the client disconnects,
  the queued slot is released (handled in the stream's `finally`).
- **Free-tier CPU**: the worker is pure TypeScript and batches SSE writes,
  keeping requests at ~0.5 ms CPU per KB streamed (`/health` is ~0 ms) —
  comfortably inside the free plan's 10 ms budget for typical chats.
- NIM uses OpenAI-compatible endpoints, so swapping in any OpenAI-compatible
  provider (OpenAI, Together, ...) only requires changing `NIM_BASE_URL` and
  the model name.