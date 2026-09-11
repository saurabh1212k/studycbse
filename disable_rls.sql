-- ================================================================
-- Run this ONCE in the Supabase SQL Editor (Dashboard -> SQL Editor)
-- Fixes: app showing empty data / "row-level security policy" errors
-- ================================================================

-- 1. Disable Row-Level Security on all tables
--    (safe for this single-user app; the anon key is the only client)
ALTER TABLE users          DISABLE ROW LEVEL SECURITY;
ALTER TABLE subjects       DISABLE ROW LEVEL SECURITY;
ALTER TABLE chapters       DISABLE ROW LEVEL SECURITY;
ALTER TABLE flashcards     DISABLE ROW LEVEL SECURITY;
ALTER TABLE pyqs           DISABLE ROW LEVEL SECURITY;
ALTER TABLE attempts       DISABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs DISABLE ROW LEVEL SECURITY;

-- 2. Make sure the default user exists (the app attaches everything to it)
INSERT INTO users (name, email)
VALUES ('Student', 'student@studyos.com')
ON CONFLICT (email) DO NOTHING;

-- 3. Done. The Streamlit app and Telegram bot will now read/write normally.
--    If subjects/chapters are still empty, also run phase4_migration.sql,
--    then scripts/split_sst.py and scripts/split_lang.py.
