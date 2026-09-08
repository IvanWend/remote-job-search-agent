-- 008_posting_embeddings.sql
-- One 1024-dim vector per role, keyed on (raw_posting_id, role_index) — not
-- structured_postings.id, which persist's DELETE-then-INSERT retires on every
-- re-extract. The composite FK references 005's UNIQUE (raw_posting_id,
-- role_index), not the PK.
--
-- ON DELETE CASCADE is the re-extract self-heal: persist deletes a posting's
-- roles before re-inserting them, the cascade drops the stale embeddings, and
-- embed.py's WHERE NOT EXISTS re-embeds on the next run.
--
-- vector(1024) matches bge-m3's dense output. The HNSW cosine index is deferred
-- to the vector_search step, where it first earns its keep.
-- Re-runnable: applying twice is a no-op.

BEGIN;

CREATE TABLE IF NOT EXISTS posting_embeddings (
    raw_posting_id BIGINT,
    role_index     INT,
    embedding      vector(1024),
    embedded_text  TEXT,
    embedded_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (raw_posting_id, role_index),
    FOREIGN KEY (raw_posting_id, role_index)
    REFERENCES structured_postings (raw_posting_id, role_index) ON DELETE CASCADE
);

COMMIT;