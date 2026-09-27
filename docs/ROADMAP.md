# Roadmap

A **remote job search agent over heterogeneous boards.**

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md. Nothing here restates what the code says.

## Current state (2026-09-27)

Phase 4 (agent) complete — the DeepSeek tool-calling loop and the FastAPI + SSE serving layer are
both done and smoke-tested live. Phase 3 storage complete and verified (1,098 raw → 1,663 roles →
1,660 vectors): `embed.py` (bge-m3), `vector_search.py` (HNSW cosine + `::vector` read path +
filters), `analytics.py` (skill/salary shapes), `rollups.py` (monthly aggregates outliving the
purge). The agent exposes `sql_query` / `vector_search` / `role_detail` as closures over a per-run
conn (see DECISIONS: agent) and runs under `ToolManager.parallel_execution_mode("sequential")` with
`temperature=0`. Serving is `src/serving/app.py` — `GET`/`POST /ask` stream SSE events
(`tool_call` → `tool_result` → `answer`) plus `/health` (see DECISIONS: serving). Remaining: the
agent eval suite (~15 canned questions) against the snapshot, then Phase 5 polish.

A distribution & ops plan (MCP server, deployment, frontend, CI) is drafted in `docs/PLAN.md` —
tracked under Phase 6 below.

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
- [ ] Agent eval suite (~15 canned questions) — must run against the snapshot
- [x] FastAPI endpoint with SSE streaming

## Phase 5 — Polish

- [ ] README with architecture diagram, eval-results table, demo GIF
- [ ] Cross-source dedup (fuzzy company+title), trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Phase 6 — Distribution & ops

- [ ] CI — `.github/workflows/ci.yml` (ruff + mypy + pytest; 7 DB tests skipped via missing
      `EVAL_DATABASE_URL`); make `app.py` / `build_agent` import-safe without env (see docs/PLAN.md)
- [ ] MCP server — `src/mcp/server.py` (FastMCP), 3 granular tools over the existing closures,
      stdio transport, direct DB (no DeepSeek key)
- [ ] Frontend — React + Vite + Tailwind SPA, served from FastAPI `StaticFiles`
- [ ] Deployment — single VPS + extended docker-compose (`web` + `ollama`, CPU host);
      provider + budget TBD

## Next

1. CI first — `.github/workflows/ci.yml` + the two env-robustness edits (`app.py` DATABASE_URL
   guard, `build_agent` defer model check) — it guards everything else.
2. Then MCP server (`src/mcp/`) → frontend (`frontend/`) → deployment, per `docs/PLAN.md`.
3. Decide hosting provider + budget before deployment; CPU host for Ollama is settled.
