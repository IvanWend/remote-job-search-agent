# remote-job-search-agent

A remote job search agent over heterogeneous boards: ingest HN "Who is Hiring" + Remotive +
Web3.career + Habr Career postings, **kept to a rolling 90-day window** → LLM structured extraction
(Pydantic, quote-grounded) → Postgres + pgvector → DeepSeek agent with tools → FastAPI.

This is the **service/infra** portfolio project; the retrieval/agent lab is the separate
**product-search** repo. Built skill-by-skill, to learn.

**Read `docs/ROADMAP.md` at the start of every session** — phase checklist, locked decisions, and
durable gotchas. `docs/PROMPT.md` holds the current session state (where we left off / next up).

## How to work with me

- **Short, structured answers.** Numbered steps or bullets, not prose walls. Actionable first,
  rationale only where a decision hinges on it. Long detailed messages are the wrong format for me.
- I write the code by default. Your job is guidance, review, and feedback — don't edit project
  files unless I ask. Docs (AGENTS / README / ROADMAP / PROMPT) are fair game on a wrap-up.
- **When I'm writing the code, spec it Input → Logic → Output**, one compact block per function,
  examples taken from `evals/gold_40_candidates.json` rather than invented.
- **Keep docs and comments lean.** ROADMAP is a checklist plus locked decisions, not a design doc.
  Comments earn their place only where a decision is non-obvious — the rationale belongs in chat.
- When I say I've implemented something, verify it: read the code and run it before assessing.
  Paste-errors-not-fixes — explain the error, don't silently patch.
- I'm doing this to learn — explain the concept when I ask, not by default. Every file must pass
  the explain-back test before we call a step done.
- Watch my token budget: prefer a fresh session per phase over dragging a long context around, and
  say so when a wrap-up + new session is the cheaper move.
- **At the end of every session, suggest the commit(s)**: message + file list, one commit per
  concern, subjects in the repo style (short lowercase imperative, e.g. "add sql_query agent
  tool"). I review and run them myself — never commit for me.

## Models (OpenCode Go)

Default: `opencode-go/glm-5.3`, pinned in `opencode.json`. Switch per session with `/models`, or
per run with `opencode run --model …`. Route by task, not habit:

- Everyday coding, tool loops, refactors → **glm-5.3** (the default).
- Docs, wrap-ups, verification, quick Q&A → **gpt-6-luna** or **glm-5.3-flash** (flash-tier
  price); **space-bunny-free** when cost matters more than polish.
- Hard debugging, architecture calls → **kimi-k3** or **grok-4.7** (premium tier — use it for
  the decision, implement with the default).

## Conventions

- **Import direction inside `src/extraction/` is one-way:** `normalize` is model-free, `schema` and
  `source_adapters` import it, `transform` imports both. Don't put fill-down back in `normalize.py`.
- The ingestion clients, `evals/generate_gold_dataset.py` and `normalize.py` carry no docstrings and
  few comments — deliberate, don't flag it and don't add them back. `schema.py`, `transform.py` and
  `source_adapters.py` do carry short docstrings where a model's *contract* is non-obvious.
- `experiments/` is a scratchpad: never imported by `src/`, relative paths fine, no tests. A cell
  graduates to `src/` as a function with a test. `.gitignore` excludes `experiments/*` entirely.
- Not an installable package (no `[build-system]`), so imports are `src.…` from the repo root.
  `[tool.pytest.ini_options]` sets `pythonpath = ["."]` to make that work under pytest.
- **Tests are parametrized tables, and the values come from `evals/gold_40_candidates.json`** — a
  real card value beats a plausible one. Where a test pins behaviour that is a known hole rather
  than the intended rule, say so in a comment and log it in ROADMAP "Still open".
- Toolchain gate before any commit:
  `uv run ruff check src/ evals/ tests/ && uv run mypy src/ tests/ && uv run pytest -q`.

## Watch out

- **`purge.py` deletes rows the boards will not serve again.**
  `evals/snapshots/2026-08-12_raw.dump` is the only copy. Re-snapshot to a new date-stamped
  filename, never in place.
- `docker exec ... pg_dump "$DATABASE_URL"` expands the variable on the **host** — an unsourced
  `.env` passes an empty string and pg_dump falls back to the container socket as `root`
  (`FATAL: role "root" does not exist`). `set -a; . ./.env; set +a` first, or pass
  `-U jobmarket -d jobmarket`. Same trap as bare `psycopg.connect()`.
- Docker needs no babysitting — systemd service, enabled at boot, user is in the `docker` group. A
  rogue Windows Postgres service on the same port has bitten this before: if `docker compose up`
  fails to bind 5432, check `Get-Service *postgres*` in an elevated PowerShell.
- **The repo is `remote-job-search-agent`; the working directory is still `job-market-agent`.**
  `docker-compose.yml` sets no explicit `name:`, so Compose derives `job-market-agent-db-1` and the
  `job-market-agent_pgdata` volume from the **directory**, not the repo. Renaming the folder
  orphans the volume that holds the corpus.
- Proxy: `~/.proxy.env` is the single source of truth. Never put globs (`127.*`, `<local>`) in
  `no_proxy` — `requests`/`httpx` don't honor them the way `curl` does, and localhost calls silently
  route through the proxy.

Source-specific quirks (Habr/Web3 API shapes, imputed salaries, labeling rules) live in
ROADMAP.md under "Durable gotchas" and Phase 2. Don't duplicate them here.
