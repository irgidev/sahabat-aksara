# 📋 Sahabat Aksara — Implementation Spec v2

> **Tanggal:** 2026-05-28  
> **Status:** Ready for Implementation  
> **Workflow:** Face Recognition Login + Menu Siswa + Dashboard Guru  
> **Target User:** Anak PAUD/TK (4-6 tahun) & Guru/Pengajar

---

## 🔄 WORKFLOW BARU (User Journey)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SAHABAT AKSARA v2                           │
│                    ─────────────────────                         │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  HOME     │  Landing page dengan 2 pilihan:                   │
│  │  PAGE     │  🎒 "Masuk Siswa"  /  👩‍🏫 "Portal Guru"          │
│  └────┬─────┘                                                    │
│       │                                                          │
│       ├─────────────────┐                                        │
│         │                                   │                      │
│         ▼                                   ▼                      │
│  ┌──────────┐                       ┌──────────────┐              │
│  │ LOGIN    │                       │ LOGIN GURU   │              │
│  │ SISWA    │  📷 Kamera aktif      │ Username +   │              │
│  │ (FaceID) │  → Deteksi wajah     │ Password     │              │
│  │          │  → Auto-login        │ (Supabase    │              │
│  │          │  → "Halo, Budi!" 🎉  │  Auth)       │              │
│  └────┬─────┘                       └──────┬───────┘              │
│       │                                     │                      │
│       ▼                                     ▼                      │
│  ┌──────────┐                       ┌──────────────┐              │
│  │ MENU     │                       │ DASHBOARD    │              │
│  │ SISWA    │  Pilihan latihan:     │ GURU         │              │
│  │          │  ✏️ Belajar Menulis   │               │              │
│  │          │     Huruf             │ • Data Siswa  │              │
│  │          │  (MVP: 1 menu)       │ • Upload Wajah│              │
│  └────┬─────┘                       │ • Monitoring  │              │
│       │                             │ • Laporan     │              │
│       ▼                             │ • Kelola Modul│              │
│  ┌──────────┐                       └──────────────┘              │
│  │ CANVAS   │  Menulis huruf + AI                                  │
│  │ MENULIS  │  evaluasi + bintang + suara                            │
│  └────┬─────┘                                                       │
│       │                                                             │
│       ▼                                                             │
│  Hasil latihan tersimpan → muncul di Dashboard Guru 📊               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏆 KEPUTUSAN TECHNOLOGY STACK

### 1. 🔴 FACE RECOGNITION — `face-api.js` (Browser-Side)

| Opsi | Akurasi | Latency | Ukuran | Lokasi | Verdict |
|------|---------|---------|--------|--------|---------|
| **face-api.js** ⭐ | 95%+ (LFW) | <200ms | ~6MB | Browser | ✅ **TERPILIH** |
| MediaPipe Face | Deteksi saja | <100ms | ~5MB | Browser | ❌ Tanpa recognition |
| Python face_recognition (dlib) | 99.38% | 500ms-2s | 50MB+ | Server | ⚠️ Terlalu berat |
| AWS Rekognition | 99.9% | 1-3s | API | Cloud | ❌ Mahal + latency |
| Azure Face | 99%+ | 500ms-2s | API | Cloud | ❌ Mahal + privacy |

**Mengapa face-api.js?**
- ✅ **Pure browser-side** — tidak ada round-trip ke server saat login (instan untuk anak!)
- ✅ **Privacy** — data wajah tidak keluar dari device saat recognition
- ✅ **TensorFlow.js backend** — pakai GPU kalau ada, fallback ke CPU
- ✅ **1:N recognition** — bisa bandingkan 1 wajah vs N siswa sekaligus
- ✅ **Model kecil** (~6MB total) — acceptable untuk edtech
- ✅ **Offline capable** — setelah model ter-download, bekerja tanpa internet
- ✅ **Well-documented** — banyak contoh production-ready
- ✅ **Anak-friendly** — bisa kasih efek lucu di overlay kamera (kacamata, topi)

**Arsitektur Face Auth:**
```
ENROLLMENT (Guru Dashboard):
  Guru upload foto → [face-api.js di browser / Python backend]
  → Ekstrak face descriptor (128-dimension float vector)
  → Simpan descriptor ke Supabase profiles.face_descriptor
  → Simpan foto asli ke Supabase Storage faces/{id}.jpg

RECOGNITION (Login Siswa):
  Buka halaman → Load face-api.js models (~3-5 detik)
  → Aktifkan kamera (getUserMedia)
  → Detect face setiap frame (ssdMobilenetv1)
  → Generate descriptor dari face yang terdeteksi
  → Bandingkan vs semua descriptor siswa (Euclidean distance)
  → Jika distance < 0.6 → MATCH! → Auto-login
  → Animasi sukacita + suara "Halo, [Nama]!"
```

### 2. 🟢 FRONTEND — Pertahankan & Tingkatkan

| Teknologi | Use Case | Status |
|-----------|----------|--------|
| **React 19 + Vite** | Core framework | ✅ Pertahankan |
| **Tailwind CSS 3** | Styling | ✅ Pertahankan |
| **@phosphor-icons/react** | Icons | ✅ Pertahankan |
| **face-api.js** | Face recognition | 🆕 Tambah |
| **react-webcam** | Camera component | 🆕 Tambah |
| **Framer Motion** | Animasi halus | 🆕 Tambah (ganti CSS manual) |
| **canvas-confetti** | Efek confetti saat berhasil | 🆕 Tambah |
| **howler.js** | Sound effects | 🆕 Tambah |
| **Zustand** | State management global | 🆕 Tambah |

### 3. 🔵 BACKEND — Pertahankan & Perluas

| Teknologi | Use Case | Status |
|-----------|----------|--------|
| **FastAPI + Uvicorn** | API server | ✅ Pertahankan |
| **OpenCV + NumPy** | Image processing | ✅ Pertahankan |
| **Supabase Client** | Database | ✅ Pertahankan |
| **python-multipart** | File upload handling | 🆕 Tambah |
| **Supabase Auth** | Guru authentication | 🆕 Integrasikan |

### 4. 🟣 DATABASE — Supabase (Schema Upgrade)

Lihat bagian **Database Schema** di bawah.

---

## 🗄️ DATABASE SCHEMA (REVISED)

```sql
-- ============================================
-- SAHABAT AKSARA v2 — SUPABASE SCHEMA
-- ============================================

-- 1. PROFILES (Extended)
-- Menyimpan data siswa DAN guru
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nama TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
    
    -- Face Recognition Data
    face_image_url TEXT,           -- URL foto wajah di Supabase Storage
    face_descriptor FLOAT8[],       -- Vector 128-D dari face-api.js (normalized)
    face_enrolled_at TIMESTAMPTZ,   -- Kapan wajah didaftarkan
    face_enrolled_by UUID REFERENCES profiles(id), -- Guru yang mendaftarkan
    
    -- Auth (untuk guru)
    email TEXT UNIQUE,
    password_hash TEXT,            -- Hashed password (Supabase Auth handles this)
    
    -- Info tambahan siswa
    avatar_url TEXT,
    kelas TEXT,                    -- Contoh: "TK-A", "TK-B"
    nis TEXT UNIQUE,               -- Nomor induk siswa
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. LESSONS (Extended)
-- Modul/huruf yang bisa dipelajari
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,           -- "Huruf A", "Angka 1", dll
    category TEXT NOT NULL DEFAULT 'alphabet', -- alphabet | number | vowel
    char_target CHAR(1),           -- Target karakter (NULL untuk modul campuran)
    difficulty INT DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
    order_index INT NOT NULL,      -- Urutan tampilan di menu
    svg_guide TEXT,                -- SVG path untuk tracing guide
    template_image_url TEXT,       -- URL gambar template huruf
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. STUDENT PROGRESS (Extended)
-- Setiap kali siswa menyelesaikan latihan
CREATE TABLE student_progress (
    id BIGSERIAL PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    lesson_id INT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    
    -- Evaluasi hasil
    accuracy INT NOT NULL CHECK (accuracy BETWEEN 0 AND 100),
    stars INT NOT NULL DEFAULT 0 CHECK (stars BETWEEN 0 AND 3),
    time_taken_ms INT,            -- Berapa lama mengerjakan (ms)
    
    -- Data gambar
    image_url TEXT,               -- URL gambar tulisan di Storage
    stroke_data JSONB,            -- Raw stroke coordinates (for future analysis)
    
    -- Metadata
    device_info TEXT,              -- User agent / device type
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes untuk performa query dashboard
CREATE INDEX idx_progress_student ON student_progress(student_id);
CREATE INDEX idx_progress_lesson ON student_progress(lesson_id);
CREATE INDEX idx_progress_created ON student_progress(created_at DESC);

-- 4. INITIAL SEED DATA
-- Guru default
INSERT INTO profiles (id, nama, role, email, kelas) VALUES 
('00000000-0000-0000-0000-000000000001', 'Bu Anita', 'teacher', 'anita@sahabataksara.id', 'TK-A');

-- Siswa contoh (dengan face descriptor placeholder)
INSERT INTO profiles (nama, role, kelas, nis) VALUES 
('Budi Santoso', 'student', 'TK-A', '2024001'),
('Siti Aminah', 'student', 'TK-A', '2024002'),
('Reza Pratama', 'student', 'TK-B', '2024003');

-- Lessons seed (MVP: alfabet A-E dulu)
INSERT INTO lessons (title, category, char_target, order_index) VALUES
('Huruf A', 'alphabet', 'A', 1),
('Huruf B', 'alphabet', 'B', 2),
('Huruf C', 'alphabet', 'C', 3),
('Huruf D', 'alphabet', 'D', 4),
('Huruf E', 'alphabet', 'E', 5);
```

---

## 📁 ARSITEKTUR FILE (TARGET)

```
sahabat-aksara/
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # Entry point
│   │   ├── App.jsx                  # Router + Auth state
│   │   ├── index.css                # Global styles + Tailwind
│   │   ├── lib/
│   │   │   ├── supabase.js          # Supabase client
│   │   │   └── face-api.js         # face-api helper functions
│   │   ├── stores/
│   │   │   └── useAuthStore.js      # Zustand: global auth state
│   │   ├── components/
│   │   │   ├── Home.jsx             # Landing: pilih Siswa/Guru
│   │   │   ├── LoginSiswa.jsx       # 🆕 Face recognition login
│   │   │   ├── LoginGuru.jsx        # 🆕 Username/password login
│   │   │   ├── MenuSiswa.jsx        # 🆕 Pilihan menu latihan
│   │   │   ├── Canvas.jsx           # Canvas menulis (upgrade)
│   │   │   ├── Dashboard.jsx        # Dashboard guru (upgrade besar)
│   │   │   └── ui/                  # 🆕 Reusable UI components
│   │   │       ├── CameraView.jsx   # Webcam wrapper + face overlay
│   │   │       ├── GlassCard.jsx    # Glass-morphism card
│   │   │       ├── StarRating.jsx   # Animated star display
│   │   │       └── LoadingScreen.jsx
│   │   └── assets/
│   │       └── sounds/              # 🆕 Sound effects (MP3)
│   │           ├── success.mp3
│   │           ├── click.mp3
│   │           └── whoosh.mp3
│   ├── public/
│   │   └── models/                  # 🆕 face-api.js model files
│   │       ├── ssd_mobilenetv1.model.json
│   │       ├── ssd_mobilenetv1.group1-shard1of1
│   │       ├── face_landmark_68.model.json
│   │       ├── face_landmark_68.group1-shard1of1
│   │       ├── face_recognition.model.json
│   │       └── face_recognition.group1-shard1of1
│   └── package.json
│
├── backend/
│   ├── main.py                      # FastAPI app (expanded endpoints)
│   ├── auth.py                      # 🆕 Guru auth logic
│   ├── face.py                      # 🆕 Face enrollment endpoint
│   ├── ai_core/
│   │   └── pattern_matching.py     # AI evaluation engine
│   └── requirements.txt
│
├── ai_core/
│   └── pattern_matching.py          # Shared AI module
│
├── data_science/
│   ├── datasets/                    # Collected handwriting samples
│   └── notebooks/                   # Future ML experiments
│
├── docs/
│   ├── IMPLEMENTATION_SPEC_V2.md    # ← DOKUMEN INI
│   ├── IMPLEMENTATION_SPEC_RESEARCH.md  # Research lama (reference)
│   └── paud.html                    # Wireframe lama
│
└── supabase_schema.sql              # Updated schema
```

---

## 🚀 IMPLEMENTASI FASE PER FASE

---

## FASE 1: FOUNDING — Home Page Baru + Login Guru

**Goal:** Halaman landing yang jelas + Login guru yang benar-benar berfungsi

**Estimasi:** 2-3 jam

### Checklist FASE 1:

#### 1.1 Home Page Redesign (`Home.jsx`)
- [ ] **2 kartu besar**: "🎒 Masuk Siswa" dan "👩‍🏫 Portal Guru"
- [ ] Desain tetap pastel + glass-morphism (pertahankan identity visual)
- [ ] Animasi hover yang playful untuk kartu siswa
- [ ] Clean/professional untuk kartu guru
- [ ] Navigasi ke `LoginSiswa` atau `LoginGuru`

#### 1.2 Login Guru (`LoginGuru.jsx`) — **BARU**
- [ ] Form: Email + Password
- [ ] Integrasi **Supabase Auth** (`supabase.auth.signInWithPassword`)
- [ ] Error handling: "Email atau password salah"
- [ ] Loading state saat proses
- [ ] Redirect ke Dashboard jika sukses
- [ ] Tombol "Kembali ke Home"

#### 1.3 Dashboard Guru — Basic Revamp (`Dashboard.jsx`)
- [ ] **Sidebar navigasi** yang fungsional (bukan mock):
  - Dashboard (ringkasan)
  - Data Siswa (daftar siswa)
  - Upload Wajah (**baru** — preview FASE 3)
  - Laporan Nilai
  - Pengaturan
- [ ] Header dengan info guru (nama, foto, logout button)
- [ ] Metric cards pakai data **real dari API** `/api/stats`
- [ ] Logout functionality (`supabase.auth.signOut`)

#### 1.4 Backend — Auth Endpoints
- [ ] `POST /api/login-guru` — validate credentials via Supabase Auth
- [ ] `GET /api/me` — get current user info
- [ ] `POST /api/logout` — invalidate session
- [ ] Update `/api/stats` — query real data dari Supabase

#### 1.5 State Management (`useAuthStore.js` — Zustand) — **BARU**
```javascript
// Global auth state — accessible from any component
{
  user: null | { id, nama, role, ... },
  isAuthenticated: false,
  isLoading: true,
  login: (userData) => void,
  logout: () => void,
}
```

#### 1.6 Routing (`App.jsx`)
- [ ] Conditional rendering berdasarkan auth state:
  - Not authenticated → `<Home />`
  - Role = student → `<MenuSiswa />` (nanti FASE 2)
  - Role = teacher → `<Dashboard />`

### Deliverable FASE 1:
> User bisa buka home → klik Portal Guru → login email/password → masuk Dashboard Guru dengan data real. Logout berfungsi.

---

## FASE 2: Face Recognition Login Siswa

**Goal:** Siswa TK bisa login hanya dengan mendekatkan wajah ke kamera

**Estimasi:** 4-6 jam (paling kompleks karena face-api.js setup)

### Checklist FASE 2:

#### 2.1 Setup face-api.js — **BARU**
- [ ] Install: `npm install face-api.js react-webcam`
- [ ] Download model files ke `public/models/`:
  - `ssd_mobilenetv1` (face detection — 5.4MB)
  - `face_landmark_68` (landmark detection — 2.0MB)
  - `face_recognition` (descriptor extraction — 6.2MB)
- [ ] Buat `src/lib/face-api.js` — helper utility:
  ```javascript
  // Fungsi-fungsi utama:
  async loadModels()           // Load 3 models (panggil sekali di App mount)
  async detectFace(videoEl)    // Return detection result + descriptor
  async getDescriptor(img)     // Extract 128-D vector dari satu gambar
  async findBestMatch(descriptor, knownDescriptors) // Bandingkan vs database
  ```

#### 2.2 Component: CameraView (`components/ui/CameraView.jsx`) — **BARU**
- [ ] Wrapper around `react-webcam`
- [ ] Fullscreen camera view dengan rounded corners (glass style)
- [ ] Face detection overlay (kotak hijau saat wajah terdeteksi)
- [ ] Fun animations: scanning effect, corner brackets
- [ ] Loading indicator saat model belum siap ("Memuat deteksi wajah...")
- [ ] Error handling: kamera tidak diizinkan, tidak ada kamera
- [ ] Props: `onFaceDetected`, `onMatchFound`, `knownFaces`

#### 2.3 Login Siswa (`LoginSiswa.jsx`) — **BARU**
- [ ] **Langkah 1**: Loading screen ("Sedang mempersiapkan...")
- [ ] **Langkah 2**: Camera aktif + face detection realtime
- [ ] Visual feedback:
  - ❌ Tidak ada wajah: "Dekatkan wajahmu ke kamera 📷"
  - 🔍 Mendeteksi: kotak hijau + "Mendeteksi..."
  - ✅ Teridentifikasi: animasi celebration + "Halo, [Nama]! 👋"
  - ⚠️ Tidak dikenal: "Wajahmu belum terdaftar. Minta guru untuk mendaftarkan!"
- [ ] Auto-login setelah match (2 detik delay untuk animasi)
- [ ] Sound effect saat berhasil: happy chime
- [ ] Timeout: kembali ke home setelah 30 detik tidak ada activity

#### 2.4 Backend: Face Descriptor API
- [ ] `GET /api/students/faces` — return all enrolled students with their descriptors
  ```json
  [
    { "id": "uuid", "nama": "Budi Santoso", "face_descriptor": [0.1, -0.2, ...] },
    ...
  ]
  ```
- [ ] Cache response (descriptors jarang berubah)

#### 2.5 Face Matching Logic (Client-side)
```javascript
// Di LoginSiswa.jsx / face-api helper:
const MATCH_THRESHOLD = 0.6;  // Euclidean distance < 0.6 = match

async function recognizeFace(descriptor) {
  const response = await fetch('/api/students/faces');
  const knownStudents = await response.json();
  
  let bestMatch = null;
  let bestDistance = Infinity;
  
  for (const student of knownStudents) {
    if (!student.face_descriptor) continue;
    const distance = euclideanDistance(descriptor, student.face_descriptor);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestMatch = student;
    }
  }
  
  if (bestDistance < MATCH_THRESHOLD) {
    return { matched: true, student: bestMatch, confidence: bestDistance };
  }
  return { matched: false };
}
```

#### 2.6 App.jsx Integration
- [ ] Panggil `loadModels()` saat app pertama kali load (splash screen)
- [ ] Routing update: siswa yang sudah login → `<MenuSiswa />`

### Deliverable FASE 2:
> Buka Home → klik Masuk Siswa → kamera aktif → dekatkan wajah → terdeteksi → auto-login → masuk Menu Siswa. Jika wajah belum terdaftar, pesan error yang ramah.

---

## FASE 3: Enrollemnt Wajah Siswa (di Dashboard Guru)

**Goal:** Guru bisa mendaftarkan wajah siswa lewat dashboard

**Estimasi:** 2-3 jam

### Checklist FASE 3:

#### 3.1 Manajemen Data Siswa (`Dashboard.jsx` — tab "Data Siswa")
- [ ] **Tabel daftar siswa**: Nama, Kelas, Status Wajah (✅ Terdaftar / ❌ Belum), Aksi
- [ ] **Tambah siswa baru**: Form (Nama, Kelas, NIS)
- [ ] **Upload foto wajah**:
  - [ ] Click to upload / drag & drop
  - [ ] Preview foto
  - [ ] Crop/focus pada area wajah (hint: "Pastikan wajah terlihat jelas")
  - [ ] Proses ekstraksi face descriptor (client-side via face-api.js)
  - [ ] Upload foto ke Supabase Storage: `faces/{student_id}.jpg`
  - [ ] Simpan descriptor + URL ke tabel `profiles`
  - [ ] Success confirmation: "Wajah [Nama] berhasil didaftarkan! ✅"
  - [ ] Error: "Tidak ada wajah terdeteksi di foto. Coba foto lain."
- [ ] Hapus siswa (soft delete / archive)
- [ ] Edit data siswa

#### 3.2 Backend: Student CRUD + Face Enrollment
- [ ] `GET /api/students` — list all students (with face status)
- [ ] `POST /api/students` — create new student
- [ ] `PUT /api/students/:id` — update student info
- [ ] `POST /api/students/:id/enroll-face` — receive face descriptor + upload image
  ```json
  // Request body (multipart):
  {
    "image": <file>,              // Foto wajah original
    "descriptor": [0.1, -0.2, ...] // 128-D vector dari face-api.js
  }
  // Response:
  { "status": "success", "face_image_url": "...", "message": "Wajah terdaftar!" }
  ```

#### 3.3 Component: FaceEnrollmentForm (`components/ui/FaceEnrollmentForm.jsx`) — **BARU**
- [ ] Photo upload widget
- [ ] face-api.js integration: extract descriptor dari uploaded photo
- [ ] Visual feedback: face detection box on uploaded image
- [ ] Validation: exactly 1 face detected (error if 0 or 2+ faces)

### Deliverable FASE 3:
> Guru login → buka tab "Data Siswa" → lihat daftar siswa → upload foto wajah → sistem ekstrak descriptor → simpan → siswa bisa login pakai wajah.

---

## FASE 4: Menu Siswa + Canvas Enhancement

**Goal:** Setelah login, siswa melihat menu latihan dan bisa mulai menulis

**Estimasi:** 3-4 jam

### Checklist FASE 4:

#### 4.1 Menu Siswa (`MenuSiswa.jsx`) — **BARU**
- [ ] **Header**: Avatar siswa + nama + sapaan ("Halo, Budi! 🎨")
- [ ] **Grid menu latihan** (kartu-kartu besar, colorful):
  - [ ] Kartu: "✏️ Belajar Menulis Huruf" (MVP — 1 menu)
  - [ ] Desain playful: icon besar, rounded, hover effect (scale + shadow)
  - [ ] Setiap kartu punya progress indicator (misal: "Huruf A: ⭐⭐⭐")
- [ ] **Tombol Logout** (subtle, pojok kanan atas — icon saja)
- [ ] Sound effect saat hover kartu (opsional, menyenangkan)
- [ ] Responsive: grid 1 kolom di mobile, 2-3 kolon di tablet

#### 4.2 Canvas Upgrade (`Canvas.jsx`)
- [ ] **Dynamic lesson loading**: terima `lessonId` sebagai prop → load huruf target dari DB
- [ ] **Multi-huruf support**: ganti dari hardcoded 'A' ke dynamic character
- [ ] **Back button** → kembali ke Menu Siswa (bukan Home)
- [ ] **Enhanced tools**:
  - [ ] Undo button (minimal 1 step backwards)
  - [ ] Clear canvas confirmation
  - [ ] Color palette yang lebih besar (cocok untuk jari anak)
- [ ] **Evaluation flow upgrade**:
  - [ ] Kirim `lesson_id` ke backend bersama koordinat
  - [ ] Pattern matching dynamic (load template sesuai huruf)
  - [ ] Star rating bertingkat: ≥90%=3⭐, ≥70%=2⭐, ≥50%=1⭐, <50%=0⭐
  - [ ] Confetti effect saat 3 bintang (`canvas-confetti`)
  - [ ] Speech synthesis: pesan berbeda per tingkat bintang
- [ ] **Auto-advance**: setelah berhasil, tombol "Huruf Selanjutnya →"

#### 4.3 Backend: Multi-Huruf Evaluation
- [ ] Update `pattern_matching.py`: accept `char_target` parameter
- [ ] Generate template dinamis (bukan hanya 'A')
- [ ] Support huruf kapital A-Z untuk MVP
- [ ] Update `/api/evaluate` endpoint: accept `lesson_id`, look up `char_target`

#### 4.4 Database: Seed lebih banyak lessons
- [ ] Insert huruf A-Z ke tabel `lessons`
- [ ] Setiap huruf punya `svg_guide` atau `template_image_url`

### Deliverable FASE 4:
> Siswa login via wajah → lihat Menu Siswa → klik "Belajar Menulis Huruf" → pilih/tampil huruf A → tulis di canvas → diklik "Cek" → dievaluasi → dapat bintang → bisa lanjut huruf berikutnya. Hasil tersimpan dan muncul di Dashboard Guru.

---

## FASE 5: Dashboard Guru — Monitoring & Laporan

**Goal:** Guru bisa monitoring perkembangan siswa secara real-time

**Estimasi:** 3-4 jam

### Checklist FASE 5:

#### 5.1 Dashboard Overview (Tab Dashboard)
- [ ] **Metric cards (REAL DATA)**:
  - [ ] Total Siswa Aktif (query COUNT dari profiles where role=student)
  - [ ] Total Latihan Hari Ini (COUNT student_progress hari ini)
  - [ ] Rata-rata Akurasi Kelas (AVG accuracy)
  - [ ] Siswa Belum Latihan (count siswa tanpa progress minggu ini)
- [ ] **Chart perkembangan**:
  - [ ] Bar chart: latihan per hari (7 hari terakhir)
  - [ ] Library: `recharts` (React charting, lightweight)
  - [ ] Tooltip interaktif
- [ ] **Activity feed**:
  - [ ] 10 latihan terakhir: "Budi menulis Huruf A → 85% ⭐⭐⭐ — 5 menit lalu"
  - [ ] Auto-refresh setiap 10 detik (polling)

#### 5.2 Tab: Laporan Nilai
- [ ] **Table semua progress siswa**:
  - [ ] Kolom: Nama Siswa, Huruf, Akurasi, Bintang, Waktu, Tanggal
  - [ ] Filter: per siswa, per huruf, per tanggal range
  - [ ] Sort: by date, by accuracy
  - [ ] Pagination
- [ ] **Detail siswa** (click nama):
  - [ ] Riwayat latihan lengkap siswa tersebut
  - [ ] Rata-rata akurasi per huruf (heatmap-style?)
  - [ ] Trend line: apakah membaik dari waktu ke waktu

#### 5.3 Tab: Data Siswa (dari FASE 3, diperkuat)
- [ ] Search/filter siswa
- [ ] Status indicator: last active, total latihan, avg score
- [ ] Quick actions: upload wajah, lihat detail, non-aktifkan

#### 5.4 Realtime Updates
- [ ] Gunakan **Supabase Realtime** subscriptions:
  ```javascript
  // Subscribe to new student_progress rows
  supabase
    .channel('progress-updates')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'student_progress' }, payload => {
      // Update dashboard metrics live!
      addNewActivityEntry(payload.new);
    })
    .subscribe();
  ```
- [ ] Indicator "Live" yang berkedip di header

#### 5.5 Backend: Analytics Endpoints
- [ ] `GET /api/dashboard/summary` — all metric card data in 1 query
- [ ] `GET /api/dashboard/activity` — recent activity feed (paginated)
- [ ] `GET /api/dashboard/student/:id/detail` — individual student analytics
- [ ] `GET /api/dashboard/reports` — full report with filters

### Deliverable FASE 5:
> Guru buka Dashboard → lihat metrik real-time → buka Laporan Nilai → filter & sort data → klik siswa → lihat detail perkembangan individu. Data update otomatis saat siswa sedang latihan.

---

## 📋 RINGKASAN SEMUA FASE

| Fase | Deskripsi | Estimasi | Key Deliverable |
|------|-----------|----------|-----------------|
| **1** | Home + Login Guru + Dashboard Basic | 2-3 jam | Guru bisa login & lihat dashboard |
| **2** | Face Recognition Login Siswa | 4-6 jam | Siswa login pakai wajah |
| **3** | Enrollment Wajah (Dashboard Guru) | 2-3 jam | Guru daftarkan wajah siswa |
| **4** | Menu Siswa + Canvas Multi-huruf | 3-4 jam | Siswa bisa latihan A-Z |
| **5** | Dashboard Monitoring Lengkap | 3-4 jam | Guru monitoring real-time |
| **TOTAL** | | **~14-20 jam** | **Full workflow MVP** |

---

## 🎯 PRIORITAS DEPENDENCY

```
FASE 1 (Foundation)
  ↓ harus selesai dulu
FASE 2 (Face Login)  ──────── PARALEL dengan sebagian FASE 3?
  ↓
FASE 3 (Enrollment)  ←── Bisa dimulai setelah FASE 1 (butuh dashboard)
  ↓
FASE 4 (Menu + Canvas) ←── Butuh FASE 2 (siswa harus bisa login)
  ↓
FASE 5 (Full Dashboard) ←── Butuh FASE 4 (ada data latihan)
```

**Rekomendasi urutan kerja:**
1. **FASE 1** dulu (foundation — semua bergantung di sini)
2. **FASE 2 + FASE 3** bersamaan (face login + enrollment saling terkait)
3. **FASE 4** (butuh hasil FASE 2)
4. **FASE 5** (butuh data dari FASE 4)

---

## ⚠️ RISIKO & MITIGASI

| Risiko | Probabilitas | Dampak | Mitigasi |
|--------|-------------|--------|----------|
| Model face-api.js lambat di device lama | Sedang | Login lama | Loading animation yang fun, pre-load di background |
| False positive (salah kenali wajah) | Rendah-Sedang | Siswa salah login | Threshold ketat (0.6), konfirmasi visual (tampilkan nama) |
| False negative (tidak kenali wajah) | Sedang | Siswa frustasi | Pencahayaan hint, retry otomatis 3x, fallback ke manual? |
| Kamera tidak permission | Sedang | Tidak bisa login | Clear instructions, link ke browser settings |
| Supabase free tier limit | Rendah (MVP) | App down | Efficient queries, caching, monitor usage |
| OpenCV pattern matching tidak akurat | Tinggi (known) | Evaluasi jelek | Pertahankan untuk MVP, rencana CNN di FASE berikutnya |

---

*Dokumen ini adalah panduan implementasi untuk Sahabat Aksara v2. Setiap fase memiliki deliverable yang jelas dan bisa di-test secara independen.*
