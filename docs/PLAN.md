# Plan — distribution & ops

Status: **CI and MCP done** (2026-09-30). Frontend and deployment not started. Build plan for four
additive work items. No pipeline/agent/extraction/embedding/config logic changes.

## Decisions

| Item | Decision |
|---|---|
| MCP server | 3 granular tools (`sql_query` / `vector_search` / `role_detail`) over the existing closures, direct DB, stdio transport. No DeepSeek key in the MCP process. |
| Deployment | Single VPS + extended docker-compose (`web` + `ollama` added; `db`/`pgdata` untouched). Ollama on-host, **CPU** (bge-m3 is ~2 GB — slow but fine for a demo). Provider + budget **TBD**. |
| Frontend | React + Vite + Tailwind SPA served from FastAPI `StaticFiles`; Vite dev-proxy → `localhost:8000`; `VITE_API_BASE` for prod. |
| CI | `.github/workflows/ci.yml`: ruff + mypy + pytest. 7 DB tests skipped via missing `EVAL_DATABASE_URL`. Code made robust to missing env (no dummy vars in CI). |

## Context (why these shapes)

- Serving is thin: `create_app()` with `/health` + `GET/POST /ask` (SSE). The agent query path is
  three closures (`make_sql_query` / `make_vector_search` / `make_role_detail`) over a `conn`.
- `vector_search` embeds via Ollama (`bge-m3`, 1024-dim) at query time — every path needs
  `OLLAMA_BASE_URL` reachable.
- Tests aren't fully offline: 7 tests in `tests/test_agent_tools.py` need the populated eval
  snapshot (`EVAL_DATABASE_URL`, `db_meta.role='eval'`). The other ~141 are offline.
- The committed snapshot (`evals/snapshots/2026-08-12_raw.dump`) is raw-only; the structured corpus
  lives only in the uncommitted local `jobmarket_eval`.

## 1. MCP server — done (2026-09-30)

Landed as specified, with one deviation: stayed on `mcp` 1.29 (`FastMCP`), not SDK v2
(`MCPServer`). `uv lock --upgrade-package mcp` also moves pydantic-ai 2.24 → 2.52. See DECISIONS.

- `src/mcp/server.py`: one `@mcp.tool()` per closure, a conn per call, stdio via `mcp.run()`.
- `mcp` 1.29 in `pyproject.toml` + `uv.lock`.
- `tests/test_mcp.py`: schema + missing-URL, offline. No DB tests.
- README MCP client example. `DATABASE_URL` and `OLLAMA_BASE_URL` go in the config `env` block.

## 2. Deployment

- Add `web` (uvicorn in a slim image, new `Dockerfile`) + `ollama` services to `docker-compose.yml`.
  **Keep `db` and `pgdata` as-is** — additive services preserve the Compose project name and volume.
- Deploy = run the pipeline once on the host (ingest → extract → embed), then cron
  ingest/purge/rollups/embed for the 90-day window. The app against an empty DB returns nothing.
- TLS/reverse proxy if public. Provider + budget TBD before this starts.
- Run the deferred agent eval baseline against the snapshot **before and after** the
  provider/model swap — the one place agent behaviour is expected to change.

## 3. Frontend

- New `frontend/` Vite project (React + Tailwind); `EventSource('/ask?q=')` for GET, streaming
  `fetch` for POST; components per SSE frame (`tool_call` / `tool_result` / `answer` / `error`).
- `src/serving/app.py`: mount `StaticFiles` at `/` in `create_app()` (keep `/health` + `/ask`).
- `.gitignore`: add `node_modules/`, `dist/`. `frontend/` is invisible to pytest/mypy/ruff.

## 4. CI — done (2026-09-29)

Landed as specified, with two deviations from the draft: `uv sync --locked` (Astral's current
flag; asserts the lock matches `pyproject.toml`) and pinned action SHAs (`checkout` v7.0.1,
`setup-uv` v9.0.0) instead of floating tags.

- New `.github/workflows/ci.yml`: `setup-python 3.13` → `uv sync` → `ruff check src/ evals/ tests/`
  → `mypy src/ tests/` → `pytest -q`.
- Skip the 7 DB tests: `pytest.skip` inside the `eval_conn` fixture when `EVAL_DATABASE_URL` is unset.
- Two env-robustness edits so the offline suite imports without env:
  1. `src/serving/app.py` — `url = os.environ.get("DATABASE_URL")`, raise a clear error in
     `_connect()` when unset.
  2. `src/agent/loop.py` — `Agent(..., defer_model_check=True)` so `build_agent` doesn't demand
     `DEEPSEEK_API_KEY` at construction. **Scope note:** this touches agent construction (on the
     "no agent logic" line); verify `defer_model_check` defers DeepSeek's *key* lookup in
     pydantic-ai 2.24.0, else `skipif` that one test.

## Sequencing

1. CI (guards everything else, lowest risk). Done.
2. MCP server (additive, local-only, immediate win in any MCP client). Done.
3. Frontend (builds against localhost; `VITE_API_BASE` flips to prod later).
4. Deployment (last; gated on provider + budget).
* Scheduled re-ingestion.

1 and 2 are independent. 3 needs only localhost. 4 needs the host decision.

## Risk

- All four items are additive. Python changes are limited to the `StaticFiles` mount (keep
  `/health`+`/ask`) and the two env-robustness edits. No existing test logic changes.
- Docker Compose risk is confined to *renaming* `db`/`pgdata` or the folder — adding `web`/`ollama`
  services is safe (see AGENTS.md).
- Any future swap of the embedder (`embed.py`) re-embeds the corpus and invalidates the snapshot's
  vectors — keep it untouched unless separately scoped.

## Open decisions

- Hosting provider + monthly budget (blocks deployment execution only). CPU host settled.
