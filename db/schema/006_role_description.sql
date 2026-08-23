-- 006_role_description.sql
-- Adds the one free-text field structured_postings was missing.
--
-- Phase 3 embeds the ROLE row, and a multi-role posting shares one raw_text:
-- without a per-role span the five roles of a "we're hiring five people" HN
-- comment embed identically and vector_search returns five copies of the same
-- hit. Inheritable like the other eight, so a single-role posting fills down
-- from the posting body and only multi-role postings pay for a span each.
-- Re-runnable: applying twice is a no-op.

BEGIN;

ALTER TABLE structured_postings
    ADD COLUMN IF NOT EXISTS description TEXT;

COMMIT;
