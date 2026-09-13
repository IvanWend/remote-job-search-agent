# Remote Job Search Agent

A **remote job search agent over heterogeneous boards.** It ingests tech job postings, extracts
structured data from messy prose with an LLM, stores it in **Postgres + pgvector** (relational *and*
embeddings in one database), and answers analytical questions — *"what skills are trending for
backend roles"*, *"which postings match this résumé"*. Portfolio project; second after
[cv-tailor-ru](../) (LLM résumé tailoring).

**Status:** ingestion **done**, extraction **done**, storage embeddings **done**. All four source
clients — HN, Remotive, Web3.career, Habr Career — plus the idempotent loader and the retention
purge are working and verified. The corpus is remote-only and kept to a **rolling 90-day window** —
**1,098 postings** (HN 502, Habr 460, Web3 100, Remotive 36) → **1,663 structured roles**. The eval
baseline is frozen (`jobmarket_eval`, read-only role) and the 40-row gold-set candidate pool is
sampled. **Phase 2 (extraction) is complete:** the extraction path runs end to end — source adapter
→ LLM → Pydantic validators → normalize/fill-down — across all four sources, traced with Langfuse.
**Phase 3 (storage) in progress:** local `bge-m3` embeddings (1024-dim) are written for all 1,660
embeddable roles; `vector_search` (pgvector HNSW + metadata filters), SQL analytics, and the
Phase 4 agent are next. See [docs/ROADMAP.md](docs/ROADMAP.md) for what is built vs. planned.

**Career signals targeted:** structured LLM extraction from unstructured text, RAG over a
self-built corpus, agent tool-calling, eval-driven development, LLM observability, containerized
deployment.

## How it works

```
INGESTION    HN (Algolia) + Remotive + Web3.career + Habr Career ──►  raw_postings (Postgres)
RETENTION    rolling 90-day window — filtered at ingest, purged on age
EXTRACTION   LLM + Pydantic schema, grounded by verbatim quotes ──►  structured_postings
STORAGE      Postgres + pgvector; local bge-m3 embeddings (1024-dim) ──►  posting_embeddings
AGENT        DeepSeek tool-calling loop: sql_query · vector_search · resume_match
SERVING      FastAPI (SSE streaming) · Langfuse tracing · Docker Compose
```

Each source runs as an **independent pipeline** — fetch → window filter → idempotent upsert →
commit. A board that is down or has changed shape costs its own rows and nothing else.

The design contrast that makes the project a good demo: **HN postings are pure unstructured prose**
(hardest extraction target), **Remotive and Web3.career are semi-structured JSON**, and **Habr is
both** — a structured card plus a separately-fetched HTML body. Normalizing them into one schema is
the point, and their own structured fields (salary, tags) double as free eval ground truth when held
out of the model's input. Every non-null extracted field carries a
**verbatim source quote** so evals can check grounding and catch fabrication (lesson carried from
cv-tailor-ru).

## Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.13 (pinned via `.python-version`; `requires-python >=3.12`) |
| Agent + extraction LLM | DeepSeek (OpenAI-compatible API); Groq fallback |
| Structured outputs | Pydantic v2 — the schema is the contract for extraction *and* evals |
| Embeddings | `bge-m3` via local Ollama, `vector(1024)` — multilingual, 8192-token context, no torch dependency |
| HTML parsing | BeautifulSoup 4 (stdlib `html.parser` backend) — Habr description bodies |
| Database | Postgres 17 + pgvector (single DB: relational + vector) |
| API | FastAPI, SSE streaming |
| Tracing | Langfuse (self-hosted, Docker) — every LLM call traced from day one |
| Orchestration | Docker Compose |
| Testing / evals | pytest + custom eval scripts + gold-set JSON |

## Data sources

Remote-only, and **corpus size is deliberately not a goal** — freshness is. Postings older than 90
days are mostly filled and only add noise to retrieval.

- **HN "Who is Hiring" (primary)** — monthly threads via the free Algolia HN API
  (`hn.algolia.com/api/v1`); top-level comments are job postings, pure prose. No auth. One thread
  per run; a 90-day window holds about three, and the idempotent upsert makes repeat runs free.
  "One top-level comment = one posting" is a **convention, not an enforced rule** — a small share are
  discussion, spam or misplaced résumés, sorted out in the extraction layer, not at ingest.
- **Web3.career** — token-gated (free, email-gated). Hard cap of 100 jobs per call; `page` and
  `offset` are ignored, so breadth comes from repeating per `tag`. Full HTML `description`. Its
  `estimated_*` salary fields are the site's own guess, not employer-stated — not ground truth.
- **Remotive** — `remotive.com/api/remote-jobs`, free, no auth; semi-structured JSON. Only ever
  exposes ~17–34 currently-live postings, no history.
- **Habr Career** — undocumented frontend API, no key needed, real pagination (`per_page=50` is the
  server's true cap; a larger value is echoed back in `meta.perPage` but still yields 50 rows, so
  page off `meta.totalPages`). The list endpoint returns cards with **no description text**, so the
  prose comes from an HTML parse of `/vacancies/{id}` — one request per posting, which is why the
  loader skips ids it already stores. Postings are Russian. ~460 live remote postings spanning about
  30 days; 31% carry an employer-stated salary, and `predictedSalary` is Habr's own guess.
- **Cut:** Adzuna (imputed salaries, truncated descriptions, not remote-focused) — its rows stay in
  the frozen eval snapshot. **Parked:** CryptoJobsList (RSS returns zero items, API is
  Cloudflare-guarded). **Ruled out:** hh.ru (API closed Dec 2025; ToS forbids derivative DBs — do
  not scrape), LinkedIn (ToS / auth walls).

## Data model

**Extraction schema** (Pydantic v2, built — two layers, deliberately separate):

```python
# verbatim: what the LLM emitted, before any conversion
class PostingExtraction(_Inheritable):
    doc_type: Literal["posting", "candidate", "other"]   # non-postings score as themselves
    company: str | None                                  # posting-level only
    roles: list[RoleExtraction]

class RoleExtraction(_Inheritable):
    title: str | None
    seniority: str | None             # a free string here, not an enum — see below

class _Inheritable(BaseModel):        # None at role level means *inherit*, not absent
    stack: list[str] | None
    location: str | None
    remote_policy: str | None
    employment_type: str | None
    salary_min / salary_max: str | float | None   # verbatim: "180k", "$3k"
    salary_period / salary_currency: str | None   # verbatim: "year", "$"
    source_quotes: dict[str, str]     # field -> verbatim quote grounding the value

# derived: transform() fills down, converts, and is what gets stored
class NormalizedRole(BaseModel):
    role_index: int
    seniority: Literal["intern", "junior", "mid", "senior", "staff+", "unknown"]
    stack: list[str]                  # synonyms folded by a Python alias map
    salary_min / salary_max: int | None   # monthly
    salary_currency: str | None       # ISO 4217, never converted
    remote_policy: Literal["remote", "hybrid", "onsite", "unknown"]
    employment_type: Literal["full-time", "part-time", "contract", "unknown"]
    ...
```

The **enum-shaped fields stay free strings on the verbatim layer** on purpose: it keeps *the model
misread the posting* and *my alias map has a gap* separately measurable. Conversion happens once, in
`transform.py`, where it is unit-testable.

A multi-role posting splits into **one record per role** (`company` posting-level, `title`/
`seniority` role-level, the other eight inherit-with-override — `stack` unions rather than
replaces), so `structured_postings` is 1:N with `raw_postings`. Five validators enforce the
grounding rules: blank-string coercion, salary coherence, `source_quotes` keys must be real field
names, required quotes on the fields where the spike fabricated, and the non-posting shape.

**Database schema** (Postgres — `raw_postings`, `structured_postings`, `extraction_runs` and
`posting_embeddings` finalized):

```sql
raw_postings (
  id BIGINT IDENTITY PK, source TEXT, external_id TEXT, raw_text TEXT,
  thread_month DATE, posted_at TIMESTAMPTZ NOT NULL, ingested_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ,
  CHECK (source IN ('hn','remotive','web3','habr')), UNIQUE (source, external_id)
)
db_meta ( singleton BOOL PK, role TEXT CHECK (role IN ('live','eval')) )  -- purge guard
structured_postings (            -- one row per ROLE, 1:N with raw_postings
  id BIGINT IDENTITY PK, raw_posting_id FK ON DELETE CASCADE, role_index INT,
  company TEXT, title TEXT, location TEXT,
  seniority TEXT, remote_policy TEXT, employment_type TEXT,   -- NOT NULL DEFAULT 'unknown', CHECKed
  stack TEXT[], salary_min INT, salary_max INT, salary_currency TEXT,  -- salary monthly
  source_quotes JSONB, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ,
  UNIQUE (raw_posting_id, role_index)
)
extraction_runs (                -- one row per raw posting, success or not
  raw_posting_id FK PK ON DELETE CASCADE, status TEXT CHECK (status IN ('ok','invalid','error')),
  doc_type TEXT, role_count INT, model TEXT, error TEXT, extracted_at TIMESTAMPTZ
)
posting_embeddings  (
  raw_posting_id BIGINT, role_index INT, embedding vector(1024), embedded_text TEXT,
  embedded_at TIMESTAMPTZ, PK (raw_posting_id, role_index),
  FK → structured_postings (raw_posting_id, role_index) ON DELETE CASCADE
)
```

Two tables, not one, because a non-posting extracts *successfully* into **zero** role rows — a
résumé in the wrong HN thread is indistinguishable from a row never attempted. `extraction_runs` is
what makes the pass resumable (`WHERE NOT EXISTS`) and its coverage countable. `ON DELETE CASCADE`
on both is load-bearing: the 90-day purge deletes `raw_postings` out from under them.

`posted_at` is `NOT NULL` because the purge filters on it and `WHERE posted_at < …` silently skips
NULLs — those rows would live forever. `db_meta` holds one row saying whether this database is the
live rolling corpus or a restored eval snapshot; the purge refuses to run unless it reads `'live'`,
which is what protects the eval baseline from a mistyped connection string.

Ingestion is **idempotent, verified end-to-end**: the loader upserts on `(source, external_id)` with
a guarded `ON CONFLICT … DO UPDATE … SET updated_at = now() WHERE raw_text IS DISTINCT FROM …`, so
re-fetching an unchanged posting is a true no-op and `updated_at` only moves when the text actually
changes. A repeat run reports `inserted: 0, updated: 0` for every source whose board hasn't moved.

Each source commits as one transaction, with a **per-row savepoint** so a single malformed posting
is counted as `failed` and skipped instead of aborting the rest — in psycopg a failed statement
poisons the whole transaction, and every row after it would otherwise fail too.

Each fetcher is handed the `external_id`s already stored for its source. Only Habr uses them: its
prose costs one HTTP request *per posting*, so a cold run is ~15 minutes and a warm one 35 seconds.
The tradeoff — a stored Habr posting is never re-read, so an edited one keeps its original text.
That id read is wrapped in `conn.transaction()`; a bare `SELECT` would leave the connection
idle-in-transaction and demote `upsert_posting`'s transaction to a savepoint.

## Setup

> Everything below is working today: `raw_postings` DDL, the four ingestion clients (HN, Remotive,
> Web3.career, Habr Career), the loader (idempotent upsert, verified end-to-end), and the retention
> purge.

Developed on **WSL2 Ubuntu** with Docker Engine running natively in WSL (systemd) — *not* Docker
Desktop. Requirements: Python 3.12+ (3.13 pinned via `.python-version`),
[uv](https://docs.astral.sh/uv/), Docker Engine + Compose, `postgresql-client`, a DeepSeek API key.

```bash
# 0. Create the venv and install locked deps
uv sync

# 1. Bootstrap the pgvector extension BEFORE first boot.
#    ./init is mounted at /docker-entrypoint-initdb.d, which runs only when the
#    data directory is empty — first boot, then silently never again.
mkdir -p init
printf 'CREATE EXTENSION IF NOT EXISTS vector;\n' > init/001_extensions.sql

# 2. Bring up Postgres + pgvector
docker compose up -d
docker compose ps                       # wait for "healthy"

# 3. Apply the schema in order (each file is re-runnable, so safe to repeat)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema/001_raw_postings.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema/002_posted_at.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema/003_retention.sql
#   004 narrows the source CHECK and only applies once no adzuna rows remain — Postgres validates
#   a new CHECK against existing rows, so run the purge first on a pre-pivot database.
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema/004_source_check.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema/005_structured_postings.sql

# 4. .env (git-ignored) — see .env.example
#   POSTGRES_PASSWORD=...
#   DATABASE_URL=postgresql://jobmarket:...@localhost:5432/jobmarket
#   WEB3_API_KEY=...        # free, email-gated at web3.career
#   DEEPSEEK_API_KEY=sk-...
#   EVAL_DATABASE_URL=...   # jobmarket_ro @ jobmarket_eval — the frozen snapshot
#   (POSTGRES_PASSWORD and the password embedded in DATABASE_URL must match, or step 3+ fails
#   with "password authentication failed")

# 5. Ingest, then enforce the window.
#   The first run takes ~15 min: Habr needs one HTML request per posting and the
#   client throttles them. Later runs fetch only newly-published ids — seconds.
uv run python -m src.ingestion.load
uv run python -m src.ingestion.purge            # dry run — prints what would go
uv run python -m src.ingestion.purge --apply    # actually deletes
```

**Take a snapshot before the first purge on a corpus you care about** — the deleted rows are not
re-fetchable from the boards. `evals/snapshots/2026-08-12_raw.dump` is the current one; re-snapshot
to a **new date-stamped filename**, never in place:

```bash
docker exec job-market-agent-db-1 pg_dump -U jobmarket -d jobmarket \
  -Fc -Z9 -t raw_postings > evals/snapshots/$(date +%F)_raw.dump
```

Evals run against that snapshot restored into `jobmarket_eval` (`db_meta.role = 'eval'`), reached
via `EVAL_DATABASE_URL` as `jobmarket_ro` — a role with `SELECT` and nothing else, which is what
actually keeps the baseline frozen. Rebuild the gold-set candidate pool with:

```bash
uv run python -m evals.generate_gold_dataset   # → evals/gold_40_candidates.json (git-ignored)
```

Toolchain gate — everything below passes before any commit:

```bash
uv run ruff check src/ evals/ tests/ && uv run mypy src/ tests/ && uv run pytest -q
```

`pytest` needs `pythonpath = ["."]` from `[tool.pytest.ini_options]`: nothing is installed (no
`[build-system]`), so without it only `tests/` lands on `sys.path` and `import src` fails at
collection.

**WSL2 + mirrored networking gotcha:** if step 2 fails with `failed to bind host port ... address
already in use`, something on the **Windows host** already owns 5432 — `networkingMode=mirrored`
means Windows and WSL share the port space. Check `Get-Service *postgres*` in PowerShell; a native
Postgres install (even one not obviously running as "a service" at a glance) is the likely culprit.
Also: if that first `up` fails mid-bind, the container can be left with a broken network sandbox
even after a *later* `docker compose up -d` reports success and the healthcheck goes green —
`NetworkSettings.Networks`/`.Ports` end up empty and the host can't reach it at all. Fix with
`docker compose down && docker compose up -d` to force a real recreate, not a `start` of the
already-broken container.

Step 3 uses the host `psql` directly rather than `docker compose exec` — one less indirection, and
it proves `DATABASE_URL` actually works before the loader depends on it.

**If Ollama is on a Windows host** (the current setup), reach it from WSL at `localhost:11434` with
`networkingMode=mirrored` in `.wslconfig`. Keep `no_proxy` free of glob patterns — `curl` tolerates
`127.*` and `<local>`, but `urllib`/`requests`/`httpx` do not, and localhost calls will silently
take the proxy.

## Project structure

```
pyproject.toml         # deps (uv) + ruff/mypy/pytest config; uv.lock is committed
.python-version        # 3.13 — uv reads this
.env.example           # committed key names, no values; .env is git-ignored
.gitattributes         # force LF (files cross into the Linux Postgres container)
docker-compose.yml     # Postgres 17 + pgvector, healthcheck, pgdata volume, ./init mount
db/schema/             # numbered, re-runnable DDL (001 raw_postings … 008 posting_embeddings)
init/                  # first-boot bootstrap only — vector + pg_trgm
src/
  ingestion/
    hn_client.py       # Algolia HN client: find thread → fetch top-level comments (HNThread)
    remotive_client.py # Remotive API client
    web3_client.py     # Web3.career API client — token-gated, redirect-guarded
    habr_client.py     # Habr Career: paginated cards + per-posting HTML description parse
    retention.py       # WINDOW_DAYS + cut sources, shared by the loader and the purge
    load.py            # per-source pipelines → window filter → idempotent upsert
    purge.py           # deletes cut sources + aged-out rows; dry-run by default, db_meta-guarded
  extraction/
    normalize.py       # pure helpers: html_to_text, enum alias maps, salary math. Model-free.
    schema.py          # the four Pydantic models + five grounding validators. No I/O, no LLM.
    source_adapters.py # (source, raw_text) -> ExtractionInput(text, ground_truth, prefilter)
    transform.py       # fill-down + conversion: PostingExtraction -> NormalizedPosting
    prompt.py          # SYSTEM_PROMPT only — kept apart so prompt edits are a clean diff
    pipeline.py        # resume query, agent, extract -> transform -> persist. The only DB writer.
    backfill.py        # gap-fill repair over stored rows (salary quote + board ground truth)
  storage/
    embed.py           # build_text → Ollama bge-m3 → posting_embeddings (text::vector)
tests/
  test_normalize.py    # parametrized tables over normalize.py's public helpers
  test_transform.py    # resolve_salary: field band vs. quote fallback
  test_source_adapters.py # apply_ground_truth gap-fill (real Habr row)
evals/
  generate_gold_dataset.py  # seeded 40-row gold-set sample from the frozen snapshot
  snapshots/                # frozen dumps — eval inputs, committed
docs/
  ROADMAP.md           # data flow, current state, per-phase checklists, what is next
```

Two schema mechanisms, one job each: `init/` is **bootstrap** (runs once, only when the data
directory is empty) and `db/schema/` is the **re-runnable** path applied by hand. No file belongs in
both — see the 2026-07-26 decision in the roadmap. Inside `extraction/` the imports run **one way**:
`normalize` knows nothing about the models, `schema` and `source_adapters` import `normalize`, and
`transform` imports both. That is why fill-down lives in its own module instead of in `normalize.py`
— it keeps the helpers testable off plain strings. The project is intentionally not an installable
package (no `[build-system]`), so imports are `src.…` from the repo root.

## Scope

This is the **service / infrastructure** project: Postgres, pgvector, a live paginated ingestion
API, FastAPI, Docker, and observability are all **load-bearing** here. The pure retrieval + agent
lab (hybrid search, reranking, hand-rolled agent loop on ChromaDB) lives in the companion
**product-search** project. Together they cover the AI-engineering checklist without duplicating a
skill across both repos.

## Notes

- English-only, international sources — author consumes content in English; portfolio reads
  internationally.
- The embedding model must match at index and query time; changing it means re-embedding.
