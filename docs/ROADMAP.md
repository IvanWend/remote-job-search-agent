# Roadmap

A **remote job search agent over heterogeneous boards.**

**Maintenance rule.** Current state is rewritten from scratch each session, not appended to.
Decisions go in DECISIONS.md. Nothing here restates what the code says.

## Current state (2026-10-13)

- **Re-scoped: production labor-market analyzer** (query box + monthly report + RU/EN + deployed
  demo). The full forward plan lives in **`docs/PLAN.md`** — this file stays the done-checklist.
- Phases 1–4 complete. Phase 5 so far: agent eval suite (18 questions, 51/54 — `i1` injection +
  `x3` RU-salary are flaky, see DECISIONS: Still open), guardrails (`usage_limits` + per-IP rate
  limit; total-token cap loosened 50k→200k after live queries hit it), packaging (hatchling,
  import name `jobmarket_agent`), MCP server. Fresh ingest + extract done — 1,422/1,422 ok,
  1,973 roles over 1,390 postings.
- **Frontend rebuilt as the Techanizer UI** (Figma design merged into `frontend/`, npm; the
  `figma_generated_ui/` download discarded after the merge): query box + Analysis/Monthly-report
  tabs, RU/EN chrome, dark/light; Analysis renders structured tool output (skill bars, salary
  tables, role cards) and highlights skill names inline via a surface-form dictionary; Monthly
  report is a placeholder until the report job lands.
- Review findings locked into PLAN.md: retention flips from 90-day-delete to keep-everything
  (`in_window` = current), skill tokens are fragmented (alias v2), salary coverage ~29%, HN loader
  only fetches the latest thread, `/ask` has no auth, no eval gating in CI.
- **Structured answer pulled forward to PLAN step 1**: every visual bug so far came from the UI
  inferring layout from untyped tool JSON per query; the typed contract replaces it.

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
- [x] Agent eval suite — `evals/eval_agent.py`: 18 questions + scorer, 3× runs; baseline 45/45 on
      the original 15 (before the provider/model swap), then +d9/x2/x3 for the salary-ranking fix
- [x] FastAPI endpoint with SSE streaming

## Phase 5 — Distribution & ops

- [x] CI — ruff + mypy + pytest over pgvector + curated fixture (`export_ci_fixture.py`)
- [x] MCP server — `jobmarket_agent/mcp/server.py` (FastMCP 1.29), 3 tools, direct DB
- [x] Frontend — Techanizer UI (React + Vite + Tailwind v4, Figma design merged): query box,
      Analysis/Monthly tabs, RU/EN chrome, dark/light; renders structured tool output +
      highlighted prose; hand-written SSE client; served from FastAPI `StaticFiles` mounted only
      when `dist/` exists (CI has no build)
- [x] Rate limit + spend cap + max-turns on the agent loop (before public, non-negotiable)
- [x] Packaging — installable (hatchling + `jobmarket_agent` flat layout); see DECISIONS: Packaging
- [x] Fresh ingest + extract right before deploy (demo freshness)
- [ ] Deployment — single VPS + docker-compose (`web` + `ollama`); provider + budget TBD;
      run the agent eval before/after the provider/model swap
- [ ] Scheduled re-ingestion — fix rollup staleness + purge↔refresh ordering first, then cron

## Phase 6 — Polish

- [ ] README with architecture diagram, eval-results table, Known limitations, demo GIF
- [ ] Cross-source dedup (fuzzy company+title) + trend charts
- [ ] Hand-roll the validate-and-retry loop to see what `pydantic-ai` hides (see DECISIONS)

## Next

1. Follow `docs/PLAN.md` build order, step 1: the structured answer contract — schema →
   prompt → SSE frame → UI contract render → eval-grader rewrite.
