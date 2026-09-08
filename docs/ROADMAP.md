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

## Current state (2026-08-27)

Phase 2. **The full corpus pass is done** — 1,098/1,098 raw rows extracted into 1,663 roles:
1,077 `ok`, 14 `invalid` (retries exhausted), 7 `error` (all the 65s timeout, which stringifies to
`''` — the `error` column is empty for every one of them). ~85 min at `chunk_size=5`.

Two repairs followed, neither of which called the model again (`src/extraction/backfill.py`):
the salary quote is now re-parsed when the four `salary_*` fields are unusable, and the fields the
prompt never sees are filled from the board's own JSON. Salary coverage went 149 → 481 roles,
`company` 1,465 → 1,649. 655 roles carry a `derived_fields` list saying which columns are not the
model's own answer.

`evals/grounding_audit.py` measures grounding over the whole corpus: **12,598 values checked,
2.7% not verbatim** — 293 stitched (a bullet list joined into a paragraph, every fragment real),
51 absent. `company`, `remote_policy`, `employment_type` and `salary` are at 0.0%.

## Phase 1 — Ingestion

- [x] Four board clients: HN (Algolia), Remotive, Web3.career, Habr Career
- [x] 90-day rolling window filter + idempotent upsert on `(source, external_id)` — `load.py`
- [x] `retention.py` + `purge.py`, guarded by `db_meta.role='live'` (see GOTCHAS: psycopg / Docker)
- [x] Frozen eval baseline: `evals/snapshots/2026-08-12_raw.dump` → `jobmarket_eval`, `jobmarket_ro`
- [x] `evals/generate_gold_dataset.py` → `gold_40_candidates.json`, seeded, reruns byte-identical

## Phase 2 — Extraction + evals

- [x] Extraction modules — `normalize`, `source_adapters`, `schema`, `transform`, `prompt`, plus
      DDL 005–007: `structured_postings`, per-role `description`, `derived_fields` (see DECISIONS)
- [x] `src/extraction/pipeline.py` — `pending`/`build_agent`/`extract`/`persist`, chunked `run`,
      argparse `main`, Langfuse tracing via the v4 SDK (see DECISIONS: pipeline)
- [x] Corpus pass — `--limit 20 --source hn` pilot, then all 1,098 raw rows → 1,663 roles
- [x] Repairs + audit — salary-quote fallback, `apply_ground_truth`, `backfill.py` over the stored
      corpus, `evals/grounding_audit.py`
- [x] `tests/test_normalize.py`, `tests/test_transform.py`, `tests/test_source_adapters.py`
- [ ] Offline fixtures — cache a response per source so the demo path runs offline, then tests for
      `schema.py`
- [ ] Eval loop — hand-label `evals/gold_labeled.json` on `(source, external_id)`, per-field /
      `doc_type` / role-alignment script, iterate the prompt to a threshold set after run one

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

1. `embed.py` + the `posting_embeddings` DDL at `vector(1024)`
2. pgvector `vector_search`
3. DeepSeek tool-calling loop, three tools
4. FastAPI + SSE
5. Then label the gold set and write the eval script
