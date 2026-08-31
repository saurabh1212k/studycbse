-- 1. Create a user
INSERT INTO users (name, email) VALUES ('Student', 'student@studyos.com') ON CONFLICT DO NOTHING;

-- 2. Add columns
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS pyqs_text TEXT;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS extra_questions TEXT;

-- 3. Insert subjects manually
INSERT INTO subjects (user_id, name, color_hex)
SELECT id, 'Mathematics', '#3b82f6' FROM users LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO subjects (user_id, name, color_hex)
SELECT id, 'Physics', '#eab308' FROM users LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO subjects (user_id, name, color_hex)
SELECT id, 'Chemistry', '#ef4444' FROM users LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO subjects (user_id, name, color_hex)
SELECT id, 'Biology', '#22c55e' FROM users LIMIT 1 ON CONFLICT DO NOTHING;

-- 4. Insert Chapters for Physics
INSERT INTO chapters (subject_id, name, status)
SELECT id, 'Light - Reflection and Refraction', 'not_started' FROM subjects WHERE name = 'Physics' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO chapters (subject_id, name, status)
SELECT id, 'The Human Eye and the Colourful World', 'not_started' FROM subjects WHERE name = 'Physics' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO chapters (subject_id, name, status)
SELECT id, 'Electricity', 'not_started' FROM subjects WHERE name = 'Physics' LIMIT 1 ON CONFLICT DO NOTHING;

-- 5. Insert Chapters for Chemistry
INSERT INTO chapters (subject_id, name, status)
SELECT id, 'Chemical Reactions and Equations', 'not_started' FROM subjects WHERE name = 'Chemistry' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO chapters (subject_id, name, status)
SELECT id, 'Acids, Bases and Salts', 'not_started' FROM subjects WHERE name = 'Chemistry' LIMIT 1 ON CONFLICT DO NOTHING;
