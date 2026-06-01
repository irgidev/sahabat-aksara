-- =============================================
--  SAHABAT AKSARA — MIGRATION PELLENGKAP (FIX v3)
--  Run di Supabase SQL Editor
--  Aman di-run berkali-kali
-- =============================================

-- ─── EXTENSIONS ──────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
--  FIX 1: Set default id kalau belum ada
-- =============================================
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_attribute 
        WHERE attrelid = 'profiles'::regclass 
        AND attname = 'id' 
        AND atthasdef
    ) THEN
        ALTER TABLE profiles ALTER COLUMN id SET DEFAULT uuid_generate_v4();
    END IF;
EXCEPTION WHEN undefined_column THEN END;
$$;

-- =============================================
--  FIX 2: Bersihkan data role yang bermasalah SEBELUM set constraint
-- =============================================

-- Update semua role NULL → 'student'
UPDATE profiles SET role = 'student' WHERE role IS NULL;

-- Update role yang tidak valid → 'student'
UPDATE profiles SET role = 'student' WHERE role NOT IN ('student', 'teacher', 'admin');

-- Hapus constraint lama kalau ada (biar bisa recreate bersih)
DO $$ BEGIN
    ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_role_check;
EXCEPTION WHEN undefined_object THEN END;
$$;

-- Sekarang baru buat constraint (aman karena data sudah bersih)
ALTER TABLE profiles ADD CONSTRAINT profiles_role_check 
    CHECK (role IN ('student', 'teacher', 'admin'));

-- Set default role = 'student'
DO $$ BEGIN
    EXECUTE 'ALTER TABLE profiles ALTER COLUMN role SET DEFAULT ''student''';
EXCEPTION WHEN undefined_column THEN END;
$$;

-- =============================================
--  1. TABLE: profiles — tambah kolom yang kurang
-- =============================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    nama TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    kelas TEXT,
    nis TEXT,
    qr_token TEXT UNIQUE,
    face_descriptor JSONB,
    face_image_url TEXT,
    avatar_url TEXT,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS kelas TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS nis TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS qr_token TEXT UNIQUE;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS face_descriptor JSONB;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS face_image_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- =============================================
--  2. TABLE: lessons
-- =============================================
CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    char_target CHAR(1) NOT NULL,
    category TEXT NOT NULL,
    template_image_url TEXT,
    difficulty INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE lessons ADD COLUMN IF NOT EXISTS template_image_url TEXT;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS difficulty INT DEFAULT 1;
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- =============================================
--  3. TABLE: student_progress
-- =============================================
CREATE TABLE IF NOT EXISTS student_progress (
    id BIGSERIAL PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    lesson_id INT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    accuracy INT NOT NULL CHECK (accuracy >= 0 AND accuracy <= 100),
    stars INT NOT NULL CHECK (stars >= 0 AND stars <= 3),
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
--  4. INDEXES
-- =============================================
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_kelas ON profiles(kelas);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_student_progress_student ON student_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_lesson ON student_progress(lesson_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_created ON student_progress(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons(category);

-- =============================================
--  5. RLS
-- =============================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_progress ENABLE ROW LEVEL SECURITY;

DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN SELECT policyname, tablename FROM pg_policies WHERE tablename IN ('profiles','lessons','student_progress') LOOP
        EXECUTE format('DROP POLICY %I ON %I', r.policyname, r.tablename);
    END LOOP;
END $$;

CREATE POLICY profiles_select_public ON profiles FOR SELECT USING (true);
CREATE POLICY profiles_insert_auth ON profiles FOR INSERT WITH CHECK (true);
CREATE POLICY profiles_update_auth ON profiles FOR UPDATE USING (true);

CREATE POLICY lessons_select_public ON lessons FOR SELECT USING (true);

CREATE POLICY student_progress_select_public ON student_progress FOR SELECT USING (true);
CREATE POLICY student_progress_insert_auth ON student_progress FOR INSERT WITH CHECK (true);

-- =============================================
--  6. SEMUA INSERT PAKAI UUID EKSPLISIT + ON CONFLICT
-- =============================================

-- Guru account
INSERT INTO profiles (id, email, nama, role, kelas) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'anita@sahabataksara.id',
    'Bu Anita',
    'teacher',
    'TK-A'
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    nama = EXCLUDED.nama,
    role = EXCLUDED.role,
    kelas = EXCLUDED.kelas;

-- Siswa contoh
INSERT INTO profiles (id, nama, role, kelas, nis, qr_token) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Budi Santoso', 'student', 'TK-A', '2024001', 'QR_BUDI_123'),
    ('22222222-2222-2222-2222-222222222222', 'Siti Aminah', 'student', 'TK-A', '2024002', 'QR_SITI_456'),
    ('33333333-3333-3333-3333-333333333333', 'Reza Pratama', 'student', 'TK-B', '2024003', 'QR_REZA_789')
ON CONFLICT (id) DO UPDATE SET
    nama = EXCLUDED.nama,
    role = EXCLUDED.role,
    kelas = EXCLUDED.kelas,
    nis = EXCLUDED.nis,
    qr_token = EXCLUDED.qr_token;

-- Huruf besar A-Z
INSERT INTO lessons (char_target, category) VALUES
    ('A', 'besar'),  ('B', 'besar'),  ('C', 'besar'),  ('D', 'besar'),
    ('E', 'besar'),  ('F', 'besar'),  ('G', 'besar'),  ('H', 'besar'),
    ('I', 'besar'),  ('J', 'besar'),  ('K', 'besar'),  ('L', 'besar'),
    ('M', 'besar'),  ('N', 'besar'),  ('O', 'besar'),  ('P', 'besar'),
    ('Q', 'besar'),  ('R', 'besar'),  ('S', 'besar'),  ('T', 'besar'),
    ('U', 'besar'),  ('V', 'besar'),  ('W', 'besar'),  ('X', 'besar'),
    ('Y', 'besar'),  ('Z', 'besar')
ON CONFLICT DO NOTHING;

-- Huruf kecil a-z
INSERT INTO lessons (char_target, category) VALUES
    ('a', 'kecil'),  ('b', 'kecil'),  ('c', 'kecil'),  ('d', 'kecil'),
    ('e', 'kecil'),  ('f', 'kecil'),  ('g', 'kecil'),  ('h', 'kecil'),
    ('i', 'kecil'),  ('j', 'kecil'),  ('k', 'kecil'),  ('l', 'kecil'),
    ('m', 'kecil'),  ('n', 'kecil'),  ('o', 'kecil'),  ('p', 'kecil'),
    ('q', 'kecil'),  ('r', 'kecil'),  ('s', 'kecil'),  ('t', 'kecil'),
    ('u', 'kecil'),  ('v', 'kecil'),  ('w', 'kecil'),  ('x', 'kecil'),
    ('y', 'kecil'),  ('z', 'kecil')
ON CONFLICT DO NOTHING;

-- Angka 0-9
INSERT INTO lessons (char_target, category) VALUES
    ('0', 'angka'),  ('1', 'angka'),  ('2', 'angka'),  ('3', 'angka'),
    ('4', 'angka'),  ('5', 'angka'),  ('6', 'angka'),  ('7', 'angka'),
    ('8', 'angka'),  ('9', 'angka')
ON CONFLICT DO NOTHING;

-- =============================================
--  VERIFIKASI:
--  SELECT * FROM profiles;
--  SELECT count(*) as total_lessons FROM lessons;
--  SELESAI ✅
-- =============================================

-- ════════════════════════════════════════════════════════════
-- FIX Fase 3: Tambah DELETE policy untuk profiles & student_progress
-- Jalankan di Supabase SQL Editor
-- ════════════════════════════════════════════════════════════

CREATE POLICY profiles_delete_auth ON profiles FOR DELETE USING (true);
CREATE POLICY student_progress_delete_auth ON student_progress FOR DELETE USING (true);

-- ════════════════════════════════════════════════════════════
-- FASE 6: PRODUCTION RLS POLICIES (Secure)
-- Jalankan di Supabase SQL Editor saat siap deploy ke production.
-- Saat development, policy USING(true) masih dipakai.
-- ════════════════════════════════════════════════════════════

-- NOTE: Untuk aktifkan production RLS, jalankan blok ini,
--       lalu hapus/disable policy "public" di atas.

/*
-- ─── PRODUCTION: profiles ──────────────────────────────
-- Hapus policy public yang terlalu longgar
DROP POLICY IF EXISTS profiles_select_public ON profiles;
DROP POLICY IF EXISTS profiles_insert_auth ON profiles;
DROP POLICY IF EXISTS profiles_update_auth ON profiles;
DROP POLICY IF EXISTS profiles_delete_auth ON profiles;

-- Semua user terautentikasi bisa baca profil
CREATE POLICY profiles_select_authenticated ON profiles FOR SELECT
  USING (auth.role() = 'authenticated');

-- Guru/admin bisa insert siswa baru
CREATE POLICY profiles_insert_teachers ON profiles FOR INSERT
  WITH CHECK (
    auth.role() = 'authenticated'
    AND (
      -- Guru membuat siswa baru (role=student)
      (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin')))
      OR
      -- User mendaftarkan diri sendiri
      (id = auth.uid())
    )
  );

-- Guru bisa update siswa, user bisa update diri sendiri
CREATE POLICY profiles_update_own_or_teacher ON profiles FOR UPDATE
  USING (
    auth.role() = 'authenticated'
    AND (
      id = auth.uid()
      OR EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin'))
    )
  );

-- Guru bisa hapus siswa
CREATE POLICY profiles_delete_teachers ON profiles FOR DELETE
  USING (
    auth.role() = 'authenticated'
    AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin'))
  );

-- ─── PRODUCTION: lessons ──────────────────────────────
-- Lessons adalah data referensi — semua authenticated bisa baca
DROP POLICY IF EXISTS lessons_select_public ON lessons;

CREATE POLICY lessons_select_authenticated ON lessons FOR SELECT
  USING (auth.role() = 'authenticated');

-- Hanya guru/admin yang bisa modifikasi lessons
CREATE POLICY lessons_modify_admin ON lessons FOR ALL
  USING (auth.role() = 'authenticated')
  WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin'))
  );

-- ─── PRODUCTION: student_progress ─────────────────────
DROP POLICY IF EXISTS student_progress_select_public ON student_progress;
DROP POLICY IF EXISTS student_progress_insert_auth ON student_progress;
DROP POLICY IF EXISTS student_progress_delete_auth ON student_progress;

-- Siswa bisa baca progress sendiri, guru bisa baca semua
CREATE POLICY progress_select_own_or_teacher ON student_progress FOR SELECT
  USING (
    auth.role() = 'authenticated'
    AND (
      student_id = auth.uid()
      OR EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin'))
    )
  );

-- Siswa bisa insert progress sendiri (via canvas evaluasi)
CREATE POLICY progress_insert_self ON student_progress FOR INSERT
  WITH CHECK (
    auth.role() = 'authenticated'
    AND student_id = auth.uid()
  );

-- Guru bisa hapus progress (moderasi), siswa tidak
CREATE POLICY progress_delete_teachers ON student_progress FOR DELETE
  USING (
    auth.role() = 'authenticated'
    AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('teacher', 'admin'))
  );
*/
