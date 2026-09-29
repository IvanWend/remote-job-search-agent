# Roadmap

A **remote job search agent over heterogeneous boards.**

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md. Nothing here restates what the code says.

## Current state (2026-09-29)

- **Phase: 5 — Distribution & ops.** CI is in. Phases 1–4 complete. Next is the MCP server, then
  frontend, then deployment. The agent eval suite stays deferred to deployment. Plan: `docs/PLAN.md`.

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

- [x] Model — bge-m3 at 1024-dim (verified live)
- [x] Embedding pipeline — `embed.py`: `title + seniority + stack + description`, `text::vector` cast (DECISIONS: storage)
- [x] pgvector search + basic metadata filters (seniority, remote) — `vector_search.py`, HNSW index (009)
- [x] SQL analytics queries (skill frequency, salary distributions) — hand-written — `analytics.py`
- [x] Monthly rollups so trends survive the purge (see DECISIONS: storage) — `rollups.py` + DDL 010

## Phase 4 — Agent

- [x] Tools: `sql_query`, `vector_search`, `role_detail` (`resume_match` → `role_detail`)
- [x] Agent loop with DeepSeek tool-calling (`output_type=Answer`, sequential tool execution)
- [ ] Agent eval suite (~15 canned questions) — deferred to Phase 5 deployment (baseline
      before/after the provider/model swap)
- [x] FastAPI endpoint with SSE streaming

## Phase 5 — Distribution & ops

- [x] CI — `.github/workflows/ci.yml` (ruff + mypy + pytest; 7 DB tests skipped via missing
      `EVAL_DATABASE_URL`); `app.py` / `build_agent` import without env (see docs/PLAN.md)
- [ ] MCP server — `src/mcp/server.py` (FastMCP), 3 granular tools over the existing closures,
      stdio transport, direct DB (no DeepSeek key)
- [ ] Frontend — React + Vite + Tailwind SPA, served from FastAPI `StaticFiles`
- [ ] Deployment — single VPS + extended docker-compose (`web` + `ollama`, CPU host);
      provider + budget TBD; run the agent eval baseline before/after the provider/model swap

## Phase 6 — Polish

- [ ] README with architecture diagram, eval-results table, demo GIF
- [ ] Cross-source dedup (fuzzy company+title), trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Next

1. MCP server (`src/mcp/`) — 3 tools over the existing closures, stdio, no DeepSeek key.
2. Then frontend (`frontend/`) → deployment, per `docs/PLAN.md`.
3. Decide hosting provider + budget before deployment; CPU host for Ollama is settled.
