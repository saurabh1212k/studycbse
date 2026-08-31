-- ================================================================
-- StudyOS - Supabase Database Schema
-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ================================================================

-- Enable UUID extension (enabled by default on Supabase)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ────────────────────────────────────────────────────────────────
-- 1. USERS
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  email       TEXT UNIQUE NOT NULL,
  class       TEXT NOT NULL DEFAULT '10',
  board       TEXT NOT NULL DEFAULT 'CBSE',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ────────────────────────────────────────────────────────────────
-- 2. SUBJECTS
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subjects (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  color_hex   TEXT NOT NULL DEFAULT '#6366f1',
  UNIQUE (user_id, name)
);


-- ────────────────────────────────────────────────────────────────
-- 3. CHAPTERS
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chapters (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id   UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  chapter_no   INTEGER,
  -- 'not_started' | 'in_progress' | 'completed' | 'revision'
  status       TEXT NOT NULL DEFAULT 'not_started'
               CHECK (status IN ('not_started','in_progress','completed','revision')),
  target_date  DATE,
  notes_url    TEXT,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on every change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS chapters_updated_at ON chapters;
CREATE TRIGGER chapters_updated_at
  BEFORE UPDATE ON chapters
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ────────────────────────────────────────────────────────────────
-- 4. FLASHCARDS  (includes SM-2 SRS fields)
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS flashcards (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chapter_id      UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  front           TEXT NOT NULL,
  back            TEXT NOT NULL,
  source          TEXT DEFAULT 'manual'
                  CHECK (source IN ('youtube', 'pdf', 'manual')),
  -- SM-2 Algorithm Fields
  ease_factor     FLOAT NOT NULL DEFAULT 2.5,
  interval_days   INTEGER NOT NULL DEFAULT 1,
  repetitions     INTEGER NOT NULL DEFAULT 0,
  next_review_at  DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for efficient SRS querying
CREATE INDEX IF NOT EXISTS idx_flashcards_review ON flashcards(next_review_at, chapter_id);


-- ────────────────────────────────────────────────────────────────
-- 5. PAST YEAR QUESTIONS (PYQs)
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pyqs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id    UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  chapter_id    UUID REFERENCES chapters(id) ON DELETE SET NULL,
  year          INTEGER NOT NULL CHECK (year BETWEEN 2014 AND 2030),
  question_text TEXT NOT NULL,
  answer_text   TEXT,
  marks         INTEGER CHECK (marks > 0),
  -- 'MCQ' | 'SAQ' | 'LAQ' | 'CBQ' (Competency Based Question)
  question_type TEXT DEFAULT 'LAQ'
                CHECK (question_type IN ('MCQ','SAQ','LAQ','CBQ')),
  difficulty    TEXT DEFAULT 'medium'
                CHECK (difficulty IN ('easy','medium','hard'))
);

CREATE INDEX IF NOT EXISTS idx_pyqs_subject_year ON pyqs(subject_id, year);


-- ────────────────────────────────────────────────────────────────
-- 6. ATTEMPTS (Student answers + AI grading results)
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attempts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pyq_id          UUID NOT NULL REFERENCES pyqs(id) ON DELETE CASCADE,
  student_answer  TEXT NOT NULL,
  -- JSON structure: { "score": 3, "max_score": 5, "step_feedback": [...], "overall_feedback": "..." }
  ai_feedback     JSONB,
  score_obtained  FLOAT,
  attempted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id, attempted_at DESC);


-- ────────────────────────────────────────────────────────────────
-- 7. STUDY SESSIONS (Focus Timer logs)
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS study_sessions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  chapter_id   UUID REFERENCES chapters(id) ON DELETE SET NULL,
  duration_min INTEGER NOT NULL CHECK (duration_min > 0),
  session_type TEXT NOT NULL DEFAULT 'study'
               CHECK (session_type IN ('study','revision','test')),
  started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ────────────────────────────────────────────────────────────────
-- 8. INGESTION JOBS (YouTube / PDF processing pipeline)
-- ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_jobs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source_type   TEXT NOT NULL CHECK (source_type IN ('youtube','pdf','text')),
  source_url    TEXT,
  chapter_id    UUID REFERENCES chapters(id) ON DELETE SET NULL,
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','processing','done','failed')),
  summary       TEXT,
  cards_created INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ================================================================
-- SEED DATA: Default subjects for a new CBSE Class 10 user
-- (Replace <YOUR_USER_ID> with your actual user UUID from the users table)
-- ================================================================
-- INSERT INTO subjects (user_id, name, color_hex) VALUES
--   ('<YOUR_USER_ID>', 'Mathematics', '#3b82f6'),
--   ('<YOUR_USER_ID>', 'Science',     '#22c55e'),
--   ('<YOUR_USER_ID>', 'SST',         '#f59e0b'),
--   ('<YOUR_USER_ID>', 'English',     '#a855f7'),
--   ('<YOUR_USER_ID>', 'Hindi',       '#ec4899');
