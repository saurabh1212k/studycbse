-- Run this in the Supabase SQL Editor to seed a test user and practice questions!

-- 1. Create a dummy user
INSERT INTO users (name, email) 
VALUES ('Student', 'student@studyos.com')
ON CONFLICT DO NOTHING;

-- 2. Create a subject linked to the user
INSERT INTO subjects (user_id, name, color_hex)
SELECT id, 'Science', '#22c55e' FROM users LIMIT 1
ON CONFLICT DO NOTHING;

-- 3. Insert Practice Questions (PYQs)
INSERT INTO pyqs (subject_id, year, marks, question_type, difficulty, question_text, answer_text)
SELECT id, 2023, 3, 'SAQ', 'medium', 
'A student added a few pieces of aluminium metal to two test tubes A and B containing aqueous solutions of iron sulphate and copper sulphate respectively. In the second part of her experiment, she added iron metal to another test tube C containing an aqueous solution of aluminium sulphate. 
(a) State the colour change in test tubes A and B.
(b) In which test tube will no reaction occur? Give reason.', 
'(a) In test tube A, the pale green colour of iron sulphate fades and turns colourless. In test tube B, the blue colour of copper sulphate fades and turns colourless. Brown/grey solid deposits are formed in both.
(b) No reaction occurs in test tube C. This is because iron is less reactive than aluminium, so it cannot displace aluminium from aluminium sulphate solution.'
FROM subjects WHERE name = 'Science' LIMIT 1;

INSERT INTO pyqs (subject_id, year, marks, question_type, difficulty, question_text, answer_text)
SELECT id, 2020, 5, 'LAQ', 'hard', 
'Draw a neat labelled diagram of human respiratory system. Explain the mechanism of breathing in human beings.', 
'(Diagram of human respiratory system showing trachea, lungs, bronchi, alveoli, diaphragm - 2 marks)
Mechanism of breathing:
Inhalation: When we breathe in, our ribs are lifted up and outwards, and the diaphragm becomes flattened. The volume of the chest cavity increases, pressure decreases, and air rushes into the lungs. (1.5 marks)
Exhalation: When we breathe out, the ribs move downwards and inwards, and the diaphragm relaxes and arches upwards. The volume of the chest cavity decreases, pressure increases, and air is pushed out of the lungs. (1.5 marks)'
FROM subjects WHERE name = 'Science' LIMIT 1;
