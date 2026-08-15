CHAT_PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI Chat</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  label { display: block; font-weight: 600; margin: 1rem 0 0.25rem; }
  textarea, input { width: 100%; box-sizing: border-box; background: #111; color: #eee;
    border: 1px solid #333; border-radius: 8px; padding: 0.6rem; font: inherit; }
  button { margin-top: 1rem; padding: 0.6rem 1.4rem; border: 0; border-radius: 8px;
    background: #2563eb; color: #fff; font-weight: 600; cursor: pointer; }
  button:disabled { opacity: 0.5; cursor: wait; }
  pre { background: #111; border: 1px solid #333; border-radius: 8px; padding: 1rem;
    white-space: pre-wrap; min-height: 6rem; margin-top: 1.5rem; }
  .meta { color: #888; }
</style>
</head>
<body>
<h1>AI Chat</h1>
<p class="meta">Context + question are sent to the worker; the NIM answer streams back over SSE.</p>
<label for="context">Context (retrieved passages)</label>
<textarea id="context" rows="8" placeholder="Paste context passages here..."></textarea>
<label for="question">Question</label>
<input id="question" placeholder="Ask about the context..." />
<button id="send">Send</button>
<pre id="out"></pre>
<script>
const $ = (id) => document.getElementById(id);
const out = $("out");

function parseSse(block) {
  let event = "message", data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += (data ? "\n" : "") + line.slice(5).trim();
  }
  return { event, data };
}

$("send").onclick = async () => {
  const context = $("context").value.trim();
  const question = $("question").value.trim();
  if (!context || !question) return;

  const btn = $("send");
  btn.disabled = true;
  out.textContent = "";

  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ context, question }),
    });
    if (!resp.ok) {
      out.textContent = `HTTP ${resp.status}: ${await resp.text()}`;
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\\n\\n");
      buffer = blocks.pop();
      for (const block of blocks) {
        const { event, data } = parseSse(block);
        if (event === "queued") {
          const j = JSON.parse(data);
          out.textContent += `\\n[queued] waiting ${j.wait_seconds.toFixed(1)}s...\\n`;
        } else if (event === "error") {
          const j = JSON.parse(data);
          out.textContent += `\\n[error] ${j.message}\\n`;
        } else if (data === "[DONE]") {
          out.textContent += "\\n\\n[DONE]";
        } else {
          try {
            const j = JSON.parse(data);
            const delta = j.choices?.[0]?.delta?.content ?? "";
            if (delta) out.textContent += delta;
          } catch {}
        }
      }
    }
  } catch (err) {
    out.textContent = "Error: " + err.message;
  } finally {
    btn.disabled = false;
  }
};
</script>
</body>
</html>
"""