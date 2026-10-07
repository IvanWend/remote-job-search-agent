# Roadmap

A **remote job search agent over heterogeneous boards.**

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md. Nothing here restates what the code says.

## Current state (2026-10-07)

- **Phase: 5 — Distribution & ops, reordered to "prove it, then ship".** CI and the MCP server are
  in; Phases 1–4 core complete. The extraction eval loop is done and the corpus is frozen
  (`2026-10-04_structured.dump` → refreshed `jobmarket_eval`). The agent eval suite is in
  (`evals/eval_agent.py`, baseline 45/45). Next: data hardening → frontend → deployment →
  re-ingestion → polish. Plan: `docs/PLAN.md`.

## Phase 1 — Ingestion

- [x] Four board clients: HN (Algolia), Remotive, Web3.career, Habr Career
- [x] 90-day rolling window filter + idempotent upsert on `(source, external_id)` — `load.py`
- [x] `retention.py` + `purge.py`, guarded by `db_meta.role='live'` (see GOTCHAS: psycopg / Docker)
- [x] Frozen eval baseline: `evals/snapshots/2026-08-12_raw.dump` → `jobmarket_eval`, `jobmarket_ro`
- [x] `evals/generate_gold_dataset.py` → `gold_40_candidates.json`, seeded, reruns byte-identical

## Phase 2 — Extraction + evals

- [x] Extraction modules — `normalize`, `source_adapters`, `schema`, `transform`, `prompt`, DDL 005–007
- [x] Pipeline — `pending`/`build_agent`/`extract`/`persist`, chunked `run`, Langfuse tracing
- [x] Corpus pass + repairs — pilot, then all 1,098 rows → 1,663 roles; `apply_ground_truth`, `backfill.py`
- [x] Tests — `test_normalize` / `test_transform` / `test_source_adapters` / `test_schema` + fixtures
- [x] Eval + freeze — `gold_labeled.json`, `eval_extraction.py` (prompt 2×, seniority 68→93%), re-snapshot → `jobmarket_eval`

## Phase 3 — Storage + retrieval

- [x] Model — bge-m3 at 1024-dim (verified live)
- [x] Embedding pipeline — `embed.py`: `title + seniority + stack + description`, `text::vector` cast (DECISIONS: storage)
- [x] pgvector search + basic metadata filters (seniority, remote) — `vector_search.py`, HNSW index (009)
- [x] SQL analytics queries (skill frequency, salary distributions) — hand-written — `analytics.py`
- [x] Monthly rollups so trends survive the purge (see DECISIONS: storage) — `rollups.py` + DDL 010

## Phase 4 — Agent

- [x] Tools: `sql_query`, `vector_search`, `role_detail` (`resume_match` → `role_detail`)
- [x] Agent loop with DeepSeek tool-calling (`output_type=Answer`, sequential tool execution)
- [x] Agent eval suite — `evals/eval_agent.py`: 15 questions + scorer, 3× runs; baseline 45/45
      (before the provider/model swap)
- [x] FastAPI endpoint with SSE streaming

## Phase 5 — Distribution & ops

- [x] CI — ruff + mypy + pytest over pgvector + curated fixture (`export_ci_fixture.py`)
- [x] MCP server — `src/mcp/server.py` (FastMCP 1.29), 3 tools, direct DB
- [ ] Frontend — React + Vite + Tailwind SPA, served from FastAPI `StaticFiles`
- [ ] Deployment — single VPS + docker-compose (`web` + `ollama`); provider + budget TBD

## Phase 6 — Polish

- [ ] README with architecture diagram, eval-results table, demo GIF
- [ ] Cross-source dedup (fuzzy company+title), trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Next

1. Data hardening — `currency_enum` validation (reject `"xyz" → "XYZ"`) + NULL-currency handling
   (Stage 2, code-only, post-freeze).

Full order and locked decisions: `docs/PLAN.md`.
