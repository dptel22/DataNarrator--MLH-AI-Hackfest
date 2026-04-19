# NarrAI Codebase Audit Report

> **Audit date:** 2026-04-19  
> **Audited by:** Perplexity (re-run of Jules PR #16 which merged empty)  
> **Files read:** `main.py`, `gemini_agent.py`, `elevenlabs_agent.py`, `supabase_agent.py`, `tests/test_main.py`, `tests/test_elevenlabs.py`, `tests/test_gemini.py`  
> **Scope:** Read-only audit — no code changed. Every finding below is an open issue to fix.

---

## Summary

| Priority | Count | Description |
|---|---|---|
| P0 | 2 | Breaks in production or silently corrupts data |
| P1 | 5 | Reliability / correctness issues |
| P2 | 4 | Code hygiene / maintainability |
| P3 | 3 | Test coverage gaps |

---

## P0 — Production Blockers

### F-01 · `BACKEND_URL = ""` hardcoded in `index.html`

**File:** `index.html`  
**Symptom:** All `fetch()` calls resolve relative to the page origin. Works on `localhost` because the backend is the same origin. **Breaks silently** if the frontend is ever served from a different domain than the backend (e.g. static CDN + separate Render service).  
**Fix:** Use a runtime-injectable constant:
```js
const BACKEND_URL = window.__BACKEND_URL__ || "";
```
Or ensure `index.html` is always served from the FastAPI process (which it currently is via `FileResponse("index.html")`). If keeping single-origin, document this constraint clearly in the README so it's never accidentally split.

---

### F-02 · `UnicodeDecodeError` not caught in CSV reading

**File:** `main.py`, line ~40  
**Code:**
```python
try:
    df = pd.read_csv(io.BytesIO(contents))
except (pd.errors.EmptyDataError, pd.errors.ParserError) as csv_err:
    raise HTTPException(status_code=400, detail="Invalid CSV file format.")
```
**Symptom:** A CSV saved in Latin-1, Windows-1252, or any non-UTF-8 encoding raises `UnicodeDecodeError` which is **not** a `pd.errors.ParserError`. It escapes the `except` block, hits the outer `except Exception as e`, and returns a raw `500` with Python exception text leaked to the client.  
**Fix:**
```python
except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as csv_err:
    raise HTTPException(status_code=400, detail="Invalid CSV file format or encoding. Please save as UTF-8.")
```

---

## P1 — Reliability Issues

### F-03 · Bare `except Exception as e` in `main.py` leaks stack traces to client

**File:** `main.py`, `/analyze` endpoint (line ~75) and `/followup` endpoint (line ~90)  
**Code:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```
**Symptom:** `str(e)` for an unexpected exception can include file paths, internal variable names, and implementation details. Exposes internal structure to end users. Also no `logging.exception()` call means the error is invisible in server logs beyond what Render captures from stdout.  
**Fix:**
```python
import logging
logger = logging.getLogger(__name__)
# ...
except Exception as e:
    logger.exception("Unhandled error in /analyze")
    raise HTTPException(status_code=500, detail="Internal server error.")
```

---

### F-04 · Missing `os.getenv()` fallback in `gemini_agent.py`

**File:** `gemini_agent.py`, lines 10-12  
**Code:**
```python
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
```
**Symptom:** If `GEMINI_API_KEY` is not set, `genai` is never configured. The first call to `model.generate_content()` raises an `google.auth.exceptions.DefaultCredentialsError` or similar — which is caught by the outer `except Exception` and silently returns `ERROR_INSIGHT`. There is no log warning that the key is missing, making this very hard to debug on Render.  
**Fix:** Add an explicit warning at module load time:
```python
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    import logging
    logging.getLogger(__name__).warning(
        "GEMINI_API_KEY is not set — all Gemini calls will fail silently."
    )
```

---

### F-05 · Missing `os.getenv()` fallback in `supabase_agent.py`

**File:** `supabase_agent.py`, `_create_supabase_client()`  
**Code:**
```python
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")
```
**Symptom:** `_create_supabase_client()` raises `ValueError` if env vars are missing — but this function is **never called** now that `ingest_csv` was removed. `get_table_summary()` doesn't use Supabase at all. However, the dead `_create_supabase_client` function and the `supabase` import at the top still run on every cold start, attempting to import the `supabase` package. If `supabase` is ever removed from `requirements.txt`, the entire app will crash at import time.  
**Fix:** Either remove `_create_supabase_client` and the `supabase` import entirely (safest), or add a lazy import inside the function body.

---

### F-06 · `elevenlabs_agent.py` — misleading filename

**File:** `elevenlabs_agent.py`  
**Symptom:** The file now contains only gTTS code. The name `elevenlabs_agent.py` misleads every future contributor and any tool that searches for ElevenLabs usage. This is **also** the residual ElevenLabs reference Jules flagged.  
**Fix:** Rename to `tts_agent.py` and update the import in `main.py`:
```python
# main.py — change
import elevenlabs_agent          # old
import tts_agent as elevenlabs_agent  # transitional alias, or
import tts_agent                 # clean
```
This is a backend-only `chore:` PR.

---

### F-07 · Tech stack badge in `index.html` still says "Google Cloud TTS"

**File:** `index.html`  
**Symptom:** The badge was updated from ElevenLabs to "Google Cloud TTS" in a prior PR but never updated again after #15 switched to gTTS. Still displays incorrect technology to judges.  
**Fix:** Find and replace the badge text: `Google Cloud TTS` → `gTTS`. Frontend-only `fix:` PR.

---

## P2 — Code Hygiene

### F-08 · `console.log` statements left in `index.html` JS

**File:** `index.html`  
**Symptom:** Debug `console.log` calls visible in browser DevTools for any judge or user who opens the console. Unprofessional for a demo.  
**Fix:** Remove all `console.log` calls. Keep `console.error` for genuine error paths only.

---

### F-09 · DOM state not reset between analyses

**File:** `index.html`  
**Symptom:** If a user uploads CSV A (which produces a chart + audio), then uploads CSV B (which only produces insight + audio with no chart), the previous analysis's `followupAnswer` div, `followupAudio` player, and the follow-up question input are **not cleared**. The old follow-up answer from CSV A remains visible while looking at CSV B's analysis.  
**Fix:** In the `analyzeBtn` click handler, before the `fetch()` call, add explicit resets:
```js
followupAnswer.textContent = "";
followupSection.style.display = "none";
followupInput.value = "";
```

---

### F-10 · `test_main.py` mocks `supabase_agent.ingest_csv` which no longer exists

**File:** `tests/test_main.py`, line 18  
**Code:**
```python
mock_supabase.ingest_csv.return_value = None
```
**Symptom:** `ingest_csv` was removed in PR #12. This mock line is a no-op (mocking a non-existent attribute on a Mock object does nothing harmful, but it is stale and misleading). Any new contributor reading this test will think `ingest_csv` is still used.  
**Fix:** Remove the `mock_supabase.ingest_csv.return_value = None` line.

---

### F-11 · README still references old stack (Snowflake, ElevenLabs, DataNarrator)

**File:** `README.md`  
**Symptom:** README was written for the original Snowflake + ElevenLabs architecture. References to Snowflake connector, ElevenLabs API, and the old name "DataNarrator" are stale. Judges reading the README will see a mismatched description.  
**Fix:** Full README rewrite — update stack table (gTTS, Supabase, Gemini 2.5 Flash), remove Snowflake, update setup instructions, update project name to NarrAI, update deploy URL.

---

## P3 — Test Coverage Gaps

### F-12 · No test for non-CSV file upload rejection

**File:** `tests/test_main.py`  
**Missing:** A test that POSTs a `.txt` or `.json` file to `/analyze` and asserts `status_code == 400`.  

---

### F-13 · No test for oversized file rejection

**File:** `tests/test_main.py`  
**Missing:** A test that POSTs a file > 10MB and asserts `status_code == 400` with the size error message.

---

### F-14 · No test for `UnicodeDecodeError` path in `/analyze`

**File:** `tests/test_main.py`  
**Missing:** Once F-02 is fixed, a test should verify that a non-UTF-8 CSV returns `400` rather than `500`.

---

## Fix Priority Order

For a hackathon context, tackle in this order:

1. **F-02** — `UnicodeDecodeError` (backend PR, 5 min fix)
2. **F-06** — Rename `elevenlabs_agent.py` → `tts_agent.py` (backend `chore:` PR)
3. **F-07** — Badge text `Google Cloud TTS` → `gTTS` (frontend PR, 1 line)
4. **F-09** — Reset DOM state between analyses (frontend PR)
5. **F-03** — Bare except logging (backend PR)
6. **F-04** — Gemini API key missing warning (backend PR)
7. **F-08** — Remove `console.log` (frontend PR)
8. **F-10** — Remove stale `ingest_csv` mock (test PR)
9. **F-11** — README rewrite (docs PR)
10. **F-05, F-12, F-13, F-14** — Supabase cleanup + new tests (post-hackfest)

---

## What Is Confirmed Working ✅

- CORS is fixed (`allow_credentials=False`) — PR #12
- `pd.read_csv` wrapped in try/except for `ParserError` / `EmptyDataError` — PR #12
- ElevenLabs fully replaced with gTTS — PR #15
- Gemini model pinned to `gemini-2.5-flash` — confirmed in `gemini_agent.py`
- JSON extraction hardened with `re.search` — confirmed in `gemini_agent.py`
- `col_unknown` fallback in `_normalize_column_name` — confirmed in `supabase_agent.py`
- Stale chart reset + `showError()` replacing `alert()` — PR #13
- Audio player hidden when no audio — PR #11
- Client-side 10MB + CSV extension guard — PR #11
- `pandas==2.2.2` and `numpy==1.26.4` pinned — confirmed in `requirements.txt`
- `/followup` endpoint exists and is tested — `test_main.py`
