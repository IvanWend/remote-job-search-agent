# Roadmap

The **service / infrastructure** half of my AI-engineering portfolio, built one phase at a time.

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md, traps in GOTCHAS.md. Nothing here restates what the code says.

## How it works

INGESTION    HN (Algolia) + Remotive + Web3.career + Habr Career ──►  raw_postings (Postgres)
RETENTION    rolling 90-day window — filtered at ingest, purged on age
EXTRACTION   LLM + Pydantic schema, grounded by verbatim quotes ──►  structured_postings
STORAGE      Postgres + pgvector; local bge-m3 embeddings (1024-dim) ──►  posting_embeddings
AGENT        DeepSeek tool-calling loop: sql_query · vector_search · resume_match
SERVING      FastAPI (SSE streaming) · Langfuse tracing · Docker Compose

## Current state (2026-08-23)

Phase 2. The pipeline runs end to end: `main` (argparse, `--dry-run`, wall-clock + `Stats`) is in
`pipeline.py`, and two 20-row HN pilots have completed against DeepSeek. Grounding audited over the
first pilot — 218/218 quotes verbatim once curly apostrophes are folded. `description` was added
before the full pass, since backfilling it would mean paying for extraction twice.

**Blocking the full corpus pass:** `ruff` fails on `pipeline.py:331` (E501, the summary log format
string). `configure_tracing` is a stub returning `None` and nothing calls it — Langfuse is unwired.

**Corpus** — 1,098 raw rows, 20 extracted (35 roles, 33 with a description). Second pilot returned
35 roles where the first returned 36 over the same 20 postings: DeepSeek splits roles
nondeterministically, so a role-count delta is not by itself a prompt improvement.

## Phase 1 — Ingestion

- [x] Four board clients: HN (Algolia), Remotive, Web3.career, Habr Career
- [x] 90-day rolling window filter + idempotent upsert on `(source, external_id)` — `load.py`
- [x] `retention.py` + `purge.py`, guarded by `db_meta.role='live'` (see GOTCHAS: psycopg / Docker)
- [x] Frozen eval baseline: `evals/snapshots/2026-08-12_raw.dump` → `jobmarket_eval`, `jobmarket_ro`
- [x] `evals/generate_gold_dataset.py` → `gold_40_candidates.json`, seeded, reruns byte-identical

## Phase 2 — Extraction + evals

- [x] `src/extraction/normalize.py` — pure helpers, model-free
- [x] `src/extraction/source_adapters.py` — `(source, external_id, raw_text)` → `ExtractionInput`
- [x] `src/extraction/schema.py` — four Pydantic models, five grounding validators
- [x] `src/extraction/transform.py` — fill-down + conversion (see DECISIONS: schema)
- [x] `tests/test_normalize.py` — parametrized cases over every public function
- [x] `db/schema/005_structured_postings.sql` (see DECISIONS: storage)
- [x] `src/extraction/prompt.py` — `SYSTEM_PROMPT`, injected so prompt edits stay a clean diff
- [x] `src/extraction/pipeline.py` — `pending`, `build_agent`, `extract`, `persist`
- [x] `src/extraction/pipeline.py` — `run` (chunked gather, serial writes)
- [x] `src/extraction/pipeline.py` — `main` (argparse, `--dry-run`, wall-clock + `Stats` summary)
- [x] `db/schema/006_role_description.sql` — per-role `description`, inheritable (see DECISIONS)
- [ ] Langfuse Cloud over OTLP, wired in `main` (see DECISIONS: pipeline)
- [x] Pilot `--limit 20 --source hn` — ran twice, before and after `description`
- [ ] Full corpus pass over the remaining 1,078 rows
- [ ] Tests for `schema.py`, `source_adapters.py`, `transform.py` — need the offline fixtures below
- [ ] Hand-label `evals/gold_labeled.json`, keyed on `(source, external_id)` (see DECISIONS)
- [ ] Eval script: per-field accuracy, `doc_type`, role count, role alignment (see DECISIONS)
- [ ] Iterate the prompt until acceptable accuracy (set the threshold after the first run)
- [ ] Cache a fixture response per source so the demo path runs offline

## Still open

- **Grounding is asserted, not verified.** `_required_quotes_present` checks a quote *key* exists;
  nothing compares the quote to the source text. The model is honest today (218/218) — the schema
  would not notice if it stopped. Fix is Pydantic validation context carrying the source text.
- **`stack` fill-down over-propagates.** Posting 2's five roles all carry
  `['claude code','cursor','aider']`, grounded in a quote that appears only in the Agentic Engineer
  bullet. Phase 3's `unnest(stack)` skill frequency will over-count.
- **`description` fill-down does not separate roles that differ only by seniority.** Posting 12's
  Senior and Staff Product Engineer share one span. Embed `title + seniority + stack + description`,
  not the description alone.
- **Observed paraphrase mode:** the model stitches bullet lists into one paragraph (posting 12),
  each sentence verbatim but the whole not a contiguous span. Watch it as the corpus scales.
- **`id` is not a stable key.** `persist` is DELETE-then-INSERT, so re-extraction retires every
  `structured_postings.id`. Key anything downstream — `posting_embeddings` above all — on
  `(raw_posting_id, role_index)`.
- `Stats` is logged and then discarded; the full pass's cost will not be recoverable afterward.
- The `ON CONFLICT` comment on `structured_postings_raw_posting_role_key` in 005 is stale —
  `persist` deletes and re-inserts.

## Phase 3 — Storage + retrieval

- [ ] Model - bge-m3` at 1024-dim
- [ ] Embedding pipeline — decide what text gets embedded and document why
- [ ] pgvector search + basic metadata filters (seniority, remote)
- [ ] SQL analytics queries (skill frequency, salary distributions) — hand-written
- [ ] Monthly rollups so trends survive the purge (see DECISIONS: storage)

## Phase 4 — Agent

- [ ] Tools: `sql_query` (whitelisted), `vector_search`, `resume_match`
- [ ] Agent loop with DeepSeek tool-calling
- [ ] Agent eval suite (~15 canned questions) — must run against the snapshot
- [ ] FastAPI endpoint with SSE streaming

## Phase 5 — Polish

- [ ] README with architecture diagram, eval-results table, demo GIF
- [ ] Cross-source dedup (fuzzy company+title), trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Next

1. Wrap `pipeline.py:331` so `ruff` passes, then commit
2. Langfuse over OTLP — implement `configure_tracing`, pass the provider into `build_agent`
3. Full corpus extraction pass — accept bad output, store it
4. `embed.py` + the `posting_embeddings` DDL at `vector(1024)`
5. pgvector `vector_search`
6. DeepSeek tool-calling loop, three tools
7. FastAPI + SSE
8. Then label the gold set and write the eval script
