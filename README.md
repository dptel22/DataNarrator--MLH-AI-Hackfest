# NarrAI — MLH AI Hackfest

> **Your CSV data, explained out loud.** Upload any spreadsheet, get a spoken natural-language briefing, an auto-generated chart, and the ability to ask follow-up questions — all in under 10 seconds.

🔴 **Live demo:** [datanarrator-mlh-ai-hackfest.onrender.com](https://datanarrator-mlh-ai-hackfest.onrender.com)

---

## The Problem

Most people receive data as a CSV and have no idea what it means. Opening it in Excel, figuring out trends, writing a summary — that takes time and skill most people don't have. Analysts are bottlenecks. Dashboards require setup. Nothing just *tells* you what your data says.

**NarrAI removes that bottleneck entirely.** Drop in a CSV. In seconds, a multi-agent AI pipeline reads your data, writes a three-sentence insight with a concrete recommendation, renders the most relevant chart, and reads the whole thing to you out loud. You can then ask follow-up questions in plain English and hear the answers spoken back.

---

## Demo

| Step | What happens |
|------|--------------|
| 1. Upload a CSV | Drag-and-drop or file picker, up to 10MB |
| 2. Gemini reads it | Summarises columns, detects patterns, writes a human-readable insight |
| 3. Chart renders | The most meaningful chart type (bar, line, pie) auto-selected and drawn |
| 4. Audio plays | gTTS converts the insight to MP3 and plays it directly in the browser |
| 5. Ask anything | Type a follow-up question — get a spoken answer in seconds |

---

## How It Works

```text
Browser (index.html)
   │  POST /analyze  ← multipart CSV upload
   │  POST /followup ← { insight, question }
   ▼
FastAPI  (main.py)
   ├── gemini_agent.py     Sends column summary + sample rows to Gemini 2.5 Flash.
   │                       Receives JSON: { insight, chart_data }.
   │                       Falls back to regex extraction if Gemini returns extra prose.
   ├── tts_agent.py        Converts insight text → MP3 bytes via gTTS.
   │                       Returns base64-encoded audio to the browser.
   └── supabase_agent.py   Fire-and-forget: logs session_id, row count, columns
                           to Supabase as a BackgroundTask so it never blocks the response.
```

**Key engineering decisions:**
- `pandas` summarises the CSV server-side — only metadata goes to Gemini, never raw rows. Privacy-safe.
- Supabase logging runs as a FastAPI `BackgroundTask` — if Supabase is slow or down, the user never notices.
- JSON extraction uses `re.search` to find the JSON block even when Gemini prepends filler text.
- CORS is locked to `allow_credentials=False` to satisfy the Fetch spec.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| AI insight + chart | [Gemini 2.5 Flash](https://ai.google.dev/) via `google-generativeai` |
| Text-to-speech | [gTTS 2.5.3](https://gtts.readthedocs.io/) |
| Data processing | pandas 2.2.2 + numpy 1.26.4 |
| Upload logging | [Supabase](https://supabase.com/) (optional) |
| Frontend | Vanilla JS + [Chart.js](https://www.chartjs.org/) |
| Deployment | [Render](https://render.com/) free tier |

---

## Running Locally

```bash
# 1. Clone
git clone https://github.com/dptel22/NarrAI-MLH-AI_Hackfest.git
cd NarrAI-MLH-AI_Hackfest

# 2. Install
pip install -r requirements.txt

# 3. Set env vars
export GEMINI_API_KEY=your_key_here
# Optional Supabase logging:
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your_service_role_key

# 4. Run
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) and upload any CSV.

### Supabase setup (optional)

If you want upload logging, run this once in your Supabase SQL editor:

```sql
create extension if not exists pgcrypto;

create table if not exists public.csv_uploads (
  id         uuid        primary key default gen_random_uuid(),
  session_id text        not null,
  row_count  integer,
  columns    text[],
  created_at timestamptz default now()
);

alter table public.csv_uploads enable row level security;
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 10 tests pass. Coverage includes `/analyze` happy path, bad encoding, oversized files, non-CSV rejection, Supabase credential fallback, and fire-and-forget failure isolation.

---

## What We Learned

- **Gemini output is non-deterministic.** We had to add `re.search`-based JSON extraction because Gemini 2.5 Flash sometimes wraps its JSON response in markdown prose. The robust parser is now the default.
- **Sync in async is a silent killer.** The original Supabase logging call blocked the entire async `/analyze` handler. Moving it to a `BackgroundTask` made the response path latency-independent from third-party APIs.
- **Free-tier infra has sharp edges.** ElevenLabs' free tier detects Render's shared IP range as suspicious activity and returns 401. We replaced it with gTTS — zero external dependency, fully offline-capable.

---

## AI Tools Disclosure

This project was built at MLH AI Hackfest. The following AI tools were used during development:

| Tool | How it was used |
|------|-----------------|
| **Gemini 2.5 Flash** | Runtime AI: generates insights and chart specs from CSV data |
| **GitHub Copilot** | PR code review — automated review comments on all PRs |
| **Google Jules** | Codebase audit, bug triage, test coverage PRs |
| **Codex (ChatGPT)** | Implementation of specific fixes (Supabase restore, BackgroundTasks) |
| **Perplexity AI** | Architecture decisions, debugging guidance, PR review triage |

All AI-generated code was reviewed, tested, and merged by the human author.

---

## Project Structure

```text
NarrAI-MLH-AI_Hackfest/
├── main.py                  FastAPI app — /analyze and /followup endpoints
├── gemini_agent.py          Gemini 2.5 Flash insight + chart generation
├── tts_agent.py             gTTS text-to-speech synthesis
├── supabase_agent.py        Fire-and-forget upload logging
├── index.html               Single-page frontend
├── requirements.txt
├── render.yaml              Render deployment blueprint
└── tests/
    ├── test_main.py         /analyze and /followup endpoint tests
    ├── test_gemini.py       Gemini agent unit tests
    ├── test_tts.py          TTS agent unit tests
    └── test_supabase_agent.py  Supabase logging unit + isolation tests
```
