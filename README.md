# AutoResearchSystem

Automated research agent: topic → questions → RAG-grounded answers → review →
auto-fix → report (.md / .docx / .pdf).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
copy .env.example .env        # then put your OPENROUTER_API_KEY in .env
```

## Run (CLI)

```bash
# Put PDFs/DOCX/TXT/MD into data/documents/, then:
python main.py --topic "AI in healthcare" --docs ./data/documents/
python main.py --topic "..." --questions 6 --no-ingest   # reuse existing vector store
```

Reports are written to `data/outputs/report_<timestamp>.{md,docx,pdf,meta.json}`.

## Run (Web UI)

```bash
python -m interface.web_ui
```

Two tabs:
- **📄 Research** — upload documents, enter a topic + number of questions, get a
  full reviewed report (.md / .docx / .pdf).
- **💬 Chat** — ask single questions and get answers grounded in your documents,
  with conversation memory and source chunks shown. Vague follow-ups
  ("what are its risks?") still retrieve correctly because the previous turn is
  folded into the retrieval query.

Both tabs share the **same persistent document store** ([data/vector_store/](data/vector_store/)),
so documents persist across sessions and are available to both modes.

## Run (Scheduler)

```bash
python -m interface.scheduler --topic "..." --interval 3600 --max-runs 0
```

## Tests (offline, no API key)

```bash
python -m tests.test_offline
```

## Architecture

| Layer        | Package      | Responsibility |
|--------------|--------------|----------------|
| Core         | `core/`      | config, logging, SQLite, files, orchestration (`task_manager`) |
| AI           | `ai/`        | OpenRouter client, prompts, answer generation, reviewer |
| RAG          | `rag/`       | document loading, chunking, local embeddings, ChromaDB, retrieval |
| Research     | `research/`  | question generation, query rewriting, verification, auto-fix |
| Output       | `output/`    | markdown, word, pdf, metadata |
| Interface    | `interface/` | CLI, Gradio web UI, scheduler |

### Key design rules
- **2 models only:** `anthropic/claude-haiku-4.5` (primary) for everything;
  `google/gemini-2.5-flash` (fallback) only on the final retry. (Slugs verified
  against OpenRouter's live model list — the spec's slugs no longer exist.)
- **`reviewer.py` never decides retries** — it only returns `{score, verdict, reason}`.
- **`research/verification.py` is the sole owner** of `retry_count` logic.
- **`auto_fix.py` improves the prior answer** using reviewer feedback (no regen from scratch).
- **Embeddings run locally** on CPU (sentence-transformers) — no API tokens.
- Each answer is stored with its RAG context for audit.

> Note: package folders use valid Python names (`core`, `ai`, …) rather than the
> numeric-prefixed names in the original spec, because Python identifiers cannot
> start with a digit. PDF export uses docx→PDF (docx2pdf / LibreOffice) instead
> of weasyprint to avoid native GTK/Pango dependencies on Windows.
