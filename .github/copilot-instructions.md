# DataNarrator — Copilot Instructions

## What This App Does
DataNarrator is a hackathon project that takes a CSV file, analyzes it with Gemini 1.5 Flash, generates a voice briefing via ElevenLabs TTS, and optionally logs results to Supabase. Users can ask follow-up questions about their data and get spoken answers back.

## Tech Stack
- **Backend:** FastAPI (Python 3.11), Uvicorn
- **AI/ML:** Google Gemini 1.5 Flash (`gemini_agent.py`)
- **TTS:** ElevenLabs Turbo v2 (`elevenlabs_agent.py`)
- **Database:** Supabase (`supabase_agent.py`)
- **Frontend:** Single-file HTML (`index.html` at repo root) — vanilla JS, no framework, all logic inline
- **Deploy:** Render (Python 3.11, `render.yaml`, env vars set in Render dashboard)

## Project Structure
```
/
├── main.py                  # FastAPI app — only entry point
├── gemini_agent.py          # Gemini analysis + follow-up Q&A
├── elevenlabs_agent.py      # ElevenLabs TTS → returns base64 mp3
├── supabase_agent.py        # Supabase logging (optional, non-blocking)
├── index.html               # ONLY frontend file — do not touch /frontend/
├── requirements.txt         # Pinned versions only (no loose deps)
├── runtime.txt              # python-3.11.0
├── render.yaml              # Render deploy config
└── .env.example             # Env var template
```

## Critical Rules
- **ONLY edit `index.html` at the root.** The `/frontend/` folder is dead code — ignore it completely.
- **All JavaScript is inline inside `index.html`.** Never create separate `.js` files.
- **Never touch `main.py`, `gemini_agent.py`, `elevenlabs_agent.py`, `supabase_agent.py`** unless explicitly asked.
- **Never add `localStorage` or `sessionStorage`** — the app runs in sandboxed iframes that block storage.
- **Python version is 3.11.0** — do not change `runtime.txt`. Pandas must be `==2.2.2` to avoid compile errors on Render.
- **Environment variables** are set in the Render dashboard env group "Hack fest" — never hardcode keys.

## API Endpoints (main.py)
- `POST /analyze` — accepts `multipart/form-data` with CSV file, returns `{ insight, audio_base64, columns, row_count, chart_data }`
- `POST /followup` — accepts `{ question, context }` JSON, returns `{ answer, audio_base64 }`
- `GET /` — serves `index.html`

## Key Bugs Already Fixed — Don't Reintroduce
- Use `data.columns.length` NOT `data.col_count` for the column count badge
- After setting `audio.src`, always call `audio.load()` then `audio.play().catch(()=>{})`
- No Web Speech API / SpeechSynthesis fallback — ElevenLabs is the only TTS

## Coding Style
- Python: keep functions small, no unnecessary abstractions, use `async def` for FastAPI routes
- JS: vanilla ES6+, `fetch()` with `async/await`, no jQuery, no frameworks
- Error handling: always show user-facing error messages in the UI, never silent failures
- Commits: use conventional commits (`feat:`, `fix:`, `chore:`, `refactor:`)

## What NOT to Do
- Do not create new Python files unless asked
- Do not install new dependencies without updating `requirements.txt` with a pinned version
- Do not add `print()` debug statements to production code
- Do not commit `.mp3`, `.csv`, or `.env` files
- Do not use Python 3.12+ features — stay compatible with 3.11
