-- 1. Modify the chapters table to support the new Curriculum Vault
ALTER TABLE chapters 
ADD COLUMN IF NOT EXISTS pyqs_text TEXT,
ADD COLUMN IF NOT EXISTS extra_questions TEXT;

-- 2. Fetch the user ID (assuming single user)
DO $$
DECLARE
    uid UUID;
    sub_math UUID;
    sub_phy UUID;
    sub_chem UUID;
    sub_bio UUID;
    sub_sst UUID;
    sub_eng UUID;
    sub_hin UUID;
BEGIN
    -- First, ensure at least one user exists
    INSERT INTO users (name, email) VALUES ('Student', 'student@studyos.com') ON CONFLICT DO NOTHING;
    
    SELECT id INTO uid FROM users LIMIT 1;
    
    IF uid IS NULL THEN
        RAISE NOTICE 'No user found. Please create a user first.';
        RETURN;
    END IF;

    -- 3. Insert Subjects
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'Mathematics', '#3b82f6') ON CONFLICT DO NOTHING RETURNING id INTO sub_math;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'Physics', '#eab308') ON CONFLICT DO NOTHING RETURNING id INTO sub_phy;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'Chemistry', '#ef4444') ON CONFLICT DO NOTHING RETURNING id INTO sub_chem;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'Biology', '#22c55e') ON CONFLICT DO NOTHING RETURNING id INTO sub_bio;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'SST', '#f97316') ON CONFLICT DO NOTHING RETURNING id INTO sub_sst;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'English', '#8b5cf6') ON CONFLICT DO NOTHING RETURNING id INTO sub_eng;
    INSERT INTO subjects (user_id, name, color_hex) VALUES (uid, 'Hindi', '#ec4899') ON CONFLICT DO NOTHING RETURNING id INTO sub_hin;

    -- If returning didn't catch them because they already exist, fetch them
    IF sub_math IS NULL THEN SELECT id INTO sub_math FROM subjects WHERE name = 'Mathematics' AND user_id = uid LIMIT 1; END IF;
    IF sub_phy IS NULL THEN SELECT id INTO sub_phy FROM subjects WHERE name = 'Physics' AND user_id = uid LIMIT 1; END IF;
    IF sub_chem IS NULL THEN SELECT id INTO sub_chem FROM subjects WHERE name = 'Chemistry' AND user_id = uid LIMIT 1; END IF;
    IF sub_bio IS NULL THEN SELECT id INTO sub_bio FROM subjects WHERE name = 'Biology' AND user_id = uid LIMIT 1; END IF;

    -- 4. Seed Physics Chapters
    INSERT INTO chapters (subject_id, name, status) VALUES
    (sub_phy, 'Light - Reflection and Refraction', 'not_started'),
    (sub_phy, 'The Human Eye and the Colourful World', 'not_started'),
    (sub_phy, 'Electricity', 'not_started'),
    (sub_phy, 'Magnetic Effects of Electric Current', 'not_started')
    ON CONFLICT DO NOTHING;

    -- 5. Seed Chemistry Chapters
    INSERT INTO chapters (subject_id, name, status) VALUES
    (sub_chem, 'Chemical Reactions and Equations', 'not_started'),
    (sub_chem, 'Acids, Bases and Salts', 'not_started'),
    (sub_chem, 'Metals and Non-metals', 'not_started'),
    (sub_chem, 'Carbon and its Compounds', 'not_started')
    ON CONFLICT DO NOTHING;

    -- 6. Seed Biology Chapters
    INSERT INTO chapters (subject_id, name, status) VALUES
    (sub_bio, 'Life Processes', 'not_started'),
    (sub_bio, 'Control and Coordination', 'not_started'),
    (sub_bio, 'How do Organisms Reproduce?', 'not_started'),
    (sub_bio, 'Heredity', 'not_started'),
    (sub_bio, 'Our Environment', 'not_started')
    ON CONFLICT DO NOTHING;
    
    -- 7. Seed Math Chapters (Sample)
    INSERT INTO chapters (subject_id, name, status) VALUES
    (sub_math, 'Real Numbers', 'not_started'),
    (sub_math, 'Polynomials', 'not_started'),
    (sub_math, 'Pair of Linear Equations in Two Variables', 'not_started'),
    (sub_math, 'Quadratic Equations', 'not_started'),
    (sub_math, 'Arithmetic Progressions', 'not_started'),
    (sub_math, 'Triangles', 'not_started'),
    (sub_math, 'Coordinate Geometry', 'not_started'),
    (sub_math, 'Introduction to Trigonometry', 'not_started'),
    (sub_math, 'Some Applications of Trigonometry', 'not_started'),
    (sub_math, 'Circles', 'not_started'),
    (sub_math, 'Areas Related to Circles', 'not_started'),
    (sub_math, 'Surface Areas and Volumes', 'not_started'),
    (sub_math, 'Statistics', 'not_started'),
    (sub_math, 'Probability', 'not_started')
    ON CONFLICT DO NOTHING;

END $$;
