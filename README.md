# My Blog

A personal tech blog and portfolio site built with **Astro**, featuring a
multi-language (English / 日本語 / 中文) engineering portfolio, a blog with
Markdown & MDX posts, and an **AI-assisted chat** widget powered by a
Cloudflare Workers + NVIDIA NIM backend.

## 🧱 Repository Structure

```
.
├── matrix/          # Astro blog & portfolio site (main frontend)
├── ai-chat/         # Cloudflare Worker AI chat backend (SSE streaming)
└── .github/
    └── workflows/   # GitHub Actions: deploy-matrix.yml (Vercel)
```

### matrix — Astro site

The main web application. It renders a senior-software-engineer portfolio in
three locales and a collection of blog posts.

- **Framework**: Astro (server output, Vercel adapter)
- **Locales**: `en`, `ja`, `zh` (driven by a `?lang=` query param)
- **Blog**: Markdown & MDX content in `src/content/blog/`
- **Chat widget**: an `AskAI` component that streams answers from the `ai-chat`
  worker over SSE

Key commands (run from `matrix/`):

| Command          | Action                                  |
| :--------------- | :-------------------------------------- |
| `npm install`    | Install dependencies                    |
| `npm run dev`    | Start dev server at `localhost:4321`    |
| `npm run build`  | Build the production site to `./dist/`  |
| `npm run preview`| Preview the production build locally    |

> Note: run the dev server with `astro dev --background` per `matrix/AGENTS.md`.

### ai-chat — Cloudflare Worker

A pure-TypeScript AI chat bot on **Cloudflare Workers**. It receives a JSON
payload (`context` + `question`), calls the **NVIDIA NIM** chat-completions
API, and streams the answer back over **Server-Sent Events (SSE)**.

- Simple RAG without a database (context is passed in the request body)
- Per-IP rate limiting with queuing (`RATE_LIMIT_SECONDS`, `RATE_LIMIT_MAX_QUEUE`)
- SSE streaming with token throttling
- Configurable via `wrangler.jsonc` variables (e.g. `NIM_BASE_URL`, `NIM_MODEL`)

Run from `ai-chat/`:

| Command               | Action                                  |
| :-------------------- | :-------------------------------------- |
| `npm install`         | Install wrangler + typescript           |
| `npm run typecheck`   | Run `tsc --noEmit`                      |
| `npm run dev`         | Start local dev server (`wrangler dev`) |
| `npm run deploy`      | Deploy the worker to Cloudflare         |

See [`ai-chat/README.md`](ai-chat/README.md) for full details.

## 🚀 Deployment

`matrix` is deployed to **Vercel** via the GitHub Actions workflow
`.github/workflows/deploy-matrix.yml` (manual `workflow_dispatch` with
`preview` / `production` targets). The `ai-chat` worker is deployed
independently with `wrangler deploy`.

## ✨ Features

- ✅ SEO-friendly with canonical URLs and Open Graph data
- ✅ Sitemap & RSS feed support
- ✅ Markdown & MDX blog content
- ✅ Multi-language portfolio (EN / 日本語 / 中文)
- ✅ AI-assisted Q&A chat over the profile
