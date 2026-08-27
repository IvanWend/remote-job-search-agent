-- 007_derived_fields.sql
-- Records which columns of a role did NOT come from the model's own field output.
--
-- Two things now write a field the model did not: the salary quote, re-parsed
-- when the model omitted salary_period or split "$300-450K" into 300 and
-- 450000; and the board's own JSON, for the fields held out of the prompt on
-- Habr, Web3 and Remotive. Both are better data than the NULL they replace, and
-- both would be scored as the model's answer without this column.
-- Re-runnable: applying twice is a no-op.

BEGIN;

ALTER TABLE structured_postings
    ADD COLUMN IF NOT EXISTS derived_fields TEXT[] NOT NULL DEFAULT '{}';

COMMIT;
