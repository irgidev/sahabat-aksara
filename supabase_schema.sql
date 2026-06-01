-- Supabase Schema for SahabatAksara

-- 1. Create Profiles Table
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nama TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    qr_token TEXT UNIQUE NOT NULL
);

-- 2. Create Lessons Table
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    char_target CHAR(1) NOT NULL,
    category TEXT NOT NULL
);

-- 3. Create Student Progress Table
CREATE TABLE student_progress (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    lesson_id INT REFERENCES lessons(id) ON DELETE CASCADE,
    accuracy INT NOT NULL,
    stars INT NOT NULL,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert dummy data for testing
INSERT INTO profiles (id, nama, role, qr_token) 
VALUES ('11111111-1111-1111-1111-111111111111', 'Budi Santoso', 'student', 'QR_BUDI_123');

INSERT INTO lessons (id, char_target, category)
VALUES (1, 'A', 'Alfabet');
