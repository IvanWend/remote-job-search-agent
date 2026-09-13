-- 009_posting_embeddings_hnsw.sql
-- HNSW cosine index on the role embeddings, added once vector_search gives it
-- a query to serve (008 deferred it until search earned its keep).
--
-- vector_cosine_ops is load-bearing: the default vector_ops opclass serves
-- Euclidean (<->), and a cosine (<=>) query against it silently falls back to
-- a seq scan. pgvector won't error on the mismatch — it just won't use the index.
--
-- Index name pattern <table>_<column>_hnsw so \di on posting_embeddings reads
-- as: PK, then the search index. Re-runnable: applying twice is a no-op.

BEGIN;

CREATE INDEX IF NOT EXISTS posting_embeddings_embedding_hnsw
    ON posting_embeddings USING hnsw (embedding vector_cosine_ops);

COMMIT;
