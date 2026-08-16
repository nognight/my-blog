import { CHAT_PAGE_HTML } from "./chat_page";

const DEFAULT_BASE_URL = "https://integrate.api.nvidia.com";
const DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b";

const SYSTEM_PROMPT =
  "You are a precise assistant. Answer the user's question using ONLY the " +
  "information provided in the CONTEXT section. If the CONTEXT does not " +
  "contain the answer, say that you don't know. Never invent facts, and " +
  "answer in the same language as the question.";

interface ChatRequestBody {
  context?: unknown;
  question?: unknown;
  model?: unknown;
  max_tokens?: unknown;
  temperature?: unknown;
  top_p?: unknown;
  reasoning_budget?: unknown;
}

interface NimOptions {
  model: string;
  maxTokens: number;
  temperature: number;
  topP: number;
  reasoningBudget: number | null;
}

type ChatMessage = { role: string; content: string };

function buildMessages(context: string, question: string): ChatMessage[] {
  return [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: `CONTEXT:\n${context}\n\nQUESTION:\n${question}` },
  ];
}

function clampNum(value: unknown, min: number, max: number, fallback: number): number {
  const n = Number(value);
  return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
}

function concatBytes(chunks: Uint8Array[], size: number): Uint8Array {
  const merged = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return merged;
}

class RateLimiter {
  private readonly intervalSec: number;
  private readonly maxQueue: number;
  private readonly nextSlot = new Map<string, number>();
  private readonly queued = new Map<string, number>();

  constructor(intervalSec = 5, maxQueue = 5) {
    this.intervalSec = intervalSec;
    this.maxQueue = maxQueue;
  }

  // Reserves the next slot for `ip`. Returns seconds to wait (0 = run now),
  // or null when the queue is full (caller replies 429).
  acquire(ip: string): number | null {
    const now = Date.now() / 1000;
    const slot = Math.max(now, this.nextSlot.get(ip) ?? 0);
    if (slot > now && (this.queued.get(ip) ?? 0) >= this.maxQueue) return null;
    if (slot > now) this.queued.set(ip, (this.queued.get(ip) ?? 0) + 1);
    this.nextSlot.set(ip, slot + this.intervalSec);
    return slot - now;
  }

  // Must be called exactly once per queued message after it runs.
  release(ip: string): void {
    const remaining = (this.queued.get(ip) ?? 0) - 1;
    if (remaining > 0) this.queued.set(ip, remaining);
    else this.queued.delete(ip);
  }
}

let limiter: RateLimiter | null = null;
function getLimiter(env: Env): RateLimiter {
  if (!limiter) {
    limiter = new RateLimiter(
      Number(env.RATE_LIMIT_SECONDS ?? 5),
      Number(env.RATE_LIMIT_MAX_QUEUE ?? 5),
    );
  }
  return limiter;
}

function clientIp(request: Request): string {
  return (
    request.headers.get("cf-connecting-ip") ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

function corsHeaders(): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResponse(
  body: unknown,
  status: number,
  extraHeaders: Record<string, string> = {},
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...corsHeaders(), ...extraHeaders },
  });
}

async function fetchNim(
  env: Env,
  messages: ChatMessage[],
  opts: NimOptions,
): Promise<Response> {
  const url = `${env.NIM_BASE_URL ?? DEFAULT_BASE_URL}/v1/chat/completions`;
  const payload: Record<string, unknown> = {
    model: opts.model,
    messages,
    max_tokens: opts.maxTokens,
    temperature: opts.temperature,
    top_p: opts.topP,
    stream: true,
    chat_template_kwargs: { enable_thinking: true },
  };
  if (opts.reasoningBudget != null) payload.reasoning_budget = opts.reasoningBudget;

  return fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.NVAPI_KEY}`,
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(300_000),
  });
}

// readMany() is implemented by the Workers runtime but not yet in workers-types.
type ReadManyReader = ReadableStreamDefaultReader<Uint8Array> & {
  readMany(): Promise<{ value: Uint8Array[]; done: boolean }>;
};

async function handleChat(request: Request, env: Env): Promise<Response> {
  let body: ChatRequestBody;
  try {
    body = await request.json<ChatRequestBody>();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  const context = String(body.context ?? "").trim();
  const question = String(body.question ?? "").trim();
  if (!context || !question) {
    return jsonResponse({ error: "context and question are required" }, 400);
  }

  const ip = clientIp(request);
  const delay = getLimiter(env).acquire(ip);
  if (delay === null) {
    return jsonResponse(
      { error: "Rate limited: too many queued messages for this IP. Try again later." },
      429,
    );
  }

  const messages = buildMessages(context, question);
  const opts: NimOptions = {
    model: String(body.model ?? env.NIM_MODEL ?? DEFAULT_MODEL),
    maxTokens: clampNum(body.max_tokens, 1, 16384, 4096),
    temperature: clampNum(body.temperature, 0, 2, 1.0),
    topP: clampNum(body.top_p, 0, 1, 0.95),
    reasoningBudget:
      body.reasoning_budget == null ? null : clampNum(body.reasoning_budget, 0, 16384, 4096),
  };

  let upstream: Response;
  try {
    upstream = await fetchNim(env, messages, opts);
  } catch (err) {
    getLimiter(env).release(ip);
    return jsonResponse({ error: String((err as Error)?.message ?? err) }, 502);
  }
  if (!upstream.ok) {
    getLimiter(env).release(ip);
    return jsonResponse({ error: `NIM HTTP ${upstream.status}` }, 502);
  }
  if (upstream.body === null) {
    getLimiter(env).release(ip);
    return jsonResponse({ error: "NIM returned an empty body" }, 502);
  }
  const upstreamBody = upstream.body;

  const encoder = new TextEncoder();
  const { readable, writable } = new TransformStream<Uint8Array>();
  const writer = writable.getWriter();

  (async () => {
    try {
      if (delay > 0) {
        await writer.write(
          encoder.encode(`event: queued\ndata: ${JSON.stringify({ wait_seconds: delay })}\n\n`),
        );
        await new Promise((resolve) => setTimeout(resolve, delay * 1000));
      }
      const reader = upstreamBody.getReader() as ReadManyReader;
      let chunks: Uint8Array[] = [];
      let size = 0;
      while (true) {
        if (typeof reader.readMany === "function") {
          const { value, done } = await reader.readMany();
          if (done) break;
          for (const valueChunk of value) {
            chunks.push(valueChunk);
            size += valueChunk.byteLength;
          }
        } else {
          const { value, done } = await reader.read();
          if (done) break;
          chunks.push(value);
          size += value.byteLength;
        }
        if (size >= 16384) {
          await writer.write(concatBytes(chunks, size));
          chunks = [];
          size = 0;
        }
      }
      if (chunks.length) await writer.write(concatBytes(chunks, size));
      await writer.write(encoder.encode("data: [DONE]\n\n"));
    } catch (err) {
      try {
        await writer.write(
          encoder.encode(
            `event: error\ndata: ${JSON.stringify({ message: String((err as Error)?.message ?? err) })}\n\n`,
          ),
        );
      } catch {}
    } finally {
      try {
        await writer.close();
      } catch {}
      getLimiter(env).release(ip);
    }
  })();

  return new Response(readable, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      "x-accel-buffering": "no",
      ...corsHeaders(),
    },
  });
}

function handleHealth(env: Env): Response {
  return jsonResponse(
    {
      status: "ok",
      model: env.NIM_MODEL ?? DEFAULT_MODEL,
      api_key_configured: Boolean(env.NVAPI_KEY),
    },
    200,
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const url = new URL(request.url);

    if (url.pathname === "/" || url.pathname === "") {
      return new Response(CHAT_PAGE_HTML, {
        headers: { "content-type": "text/html; charset=utf-8", ...corsHeaders() },
      });
    }
    if (url.pathname === "/health") return handleHealth(env);
    if (url.pathname === "/chat" && request.method === "POST") {
      return handleChat(request, env);
    }
    return new Response("Not found", { status: 404, headers: corsHeaders() });
  },
} satisfies ExportedHandler<Env>;