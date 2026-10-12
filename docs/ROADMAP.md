# Roadmap

A **remote job search agent over heterogeneous boards.**

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md. Nothing here restates what the code says.

## Current state (2026-10-11)

- **Phase: 5 — Distribution & ops.** Phases 1–4 complete; Stages 1–3 done plus the UI rework:
  agent eval suite (baseline 45/45), data hardening (`currency_enum` + NULL-currency caveat), and
  the frontend, now a chat-assistant UI (turns thread, one-line tool status, markdown answer;
  traces and evidence hidden). Next: rate-limit/spend-cap → packaging → deployment → re-ingestion
  → polish.

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
- [x] Frontend — React + Vite + Tailwind SPA (one chat page, hand-written SSE client), served from
      FastAPI `StaticFiles` mounted only when `dist/` exists (CI has no build)
- [ ] Rate limit + spend cap + max-turns on the agent loop (before public, non-negotiable)
- [ ] Packaging — minimal package config (reverses the "not a package" convention; log in DECISIONS)
- [ ] Deployment — single VPS + docker-compose (`web` + `ollama`); provider + budget TBD;
      run the agent eval before/after the provider/model swap
- [ ] Fresh ingest + extract right before deploy (demo freshness)
- [ ] Scheduled re-ingestion — fix rollup staleness + purge↔refresh ordering first, then cron

## Phase 6 — Polish

- [ ] README with architecture diagram, eval-results table, Known limitations, demo GIF
- [ ] Cross-source dedup (fuzzy company+title) + trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Next

1. Rate limit + spend cap + max-turns on the agent loop (Phase 5).
2. Packaging — minimal package config (Phase 5).
