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
- **📄 Research** — upload documents, enter a topic, pick the research depth (how
  many aspects to analyze internally), and get a full synthesized report
  (.md / .docx / .pdf). The internal questions are not shown in the report.
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
- **Hybrid sourcing:** answers prefer the document context, but when the context
  doesn't cover the question the model answers from general knowledge instead of
  refusing. Each statement is labeled **[From documents]** or **[General knowledge]**.
  This means you can research topics beyond your uploaded files.
- **Reports are a synthesized research narrative:** each run produces an Executive
  Summary, Introduction, Key Findings & Analysis, and Conclusion
  ([research/synthesizer.py](research/synthesizer.py)). The per-question Q&A is used
  internally as raw material for the synthesis but is **not** shown in the report.
  (It's still stored in SQLite and the `.meta.json` sidecar for auditing.)
- **2 models only:** `anthropic/claude-haiku-4.5` (primary) for everything;
  `google/gemini-2.5-flash` (fallback) only on the final retry. (Slugs verified
  against OpenRouter's live model list — the spec's slugs no longer exist.)
- **`reviewer.py` never decides retries** — it only returns `{score, verdict, reason}`.
- **`research/verification.py` is the sole owner** of `retry_count` logic.
- **`auto_fix.py` improves the prior answer** using reviewer feedback (no regen from scratch).
- **Embeddings run locally** on CPU (sentence-transformers,
  `paraphrase-multilingual-MiniLM-L12-v2`) — no API tokens. The multilingual model
  handles Vietnamese (and other languages) well; the English-only `all-MiniLM-L6-v2`
  gave noisy similarity on Vietnamese text. Override via `EMBEDDING_MODEL` in `.env`
  (changing it requires resetting the store and re-ingesting).
- **UTF-8 console** is forced on startup so the CLI works with Vietnamese/non-Latin
  output on Windows.
- Each answer is stored with its RAG context for audit.

> Note: package folders use valid Python names (`core`, `ai`, …) rather than the
> numeric-prefixed names in the original spec, because Python identifiers cannot
> start with a digit. PDF export uses docx→PDF (docx2pdf / LibreOffice) instead
> of weasyprint to avoid native GTK/Pango dependencies on Windows.
