# 📋 Sahabat Aksara — Implementation Spec Research Document

> **Tanggal:** 2026-05-28  
> **Status:** Research Phase — Ready for Decision Gate  
> **Proyek:** Platform Belajar Interaktif Pengenalan Huruf (PAUD/TK)

---

## 🎯 Ringkasan Eksekutif

Dokumen ini merangkum hasil penelitian mendalam untuk setiap lapisan teknologi yang dibutuhkan oleh **Sahabat Aksara** — platform edtech interaktif untuk anak usia 4-6 tahun (PAUD/TK) dengan fokus pada:
1. **Tracing/Menulis huruf** (A-Z, a-z, angka)
2. **Evaluasi gambar tulisan tangan secara real-time**
3. **Dashboard Guru** untuk monitoring progress
4. **Login QR** untuk identifikasi siswa

Penelitian mencakup **6 area keputusan kritis** dengan masing-masing opsi, perbandingan, dan rekomendasi.

---

## 1. 🔬 HANDWRITING RECOGNITION & EVALUATION ENGINE

### Konteks Saat Ini
Sistem saat ini menggunakan **OpenCV Template Matching** (`ai_core/pattern_matching.py`):
- Template huruf 'A' di-generate dengan `cv2.putText()`
- Perbandingan menggunakan `cv2.bitwise_and` + `cv2.matchShapes` (Hu Moments)
- Penalti khusus untuk struktur huruf (crossbar detection)
- **Keterbatasan:** Hanya mendukung 1 huruf ('A'), akurasi rendah untuk variasi tulisan anak, tidak scalable

### Opsi yang Diteliti

| # | Pendekatan | Akurasi | Latency | Kompleksitas | Skalabilitas | Cocok untuk Anak? |
|---|-----------|---------|---------|-------------|-------------|------------------|
| **A** | OpenCV Template Matching (current) | 40-60% | <50ms | Rendah | ❌ Buruk | ⚠️ Cukup |
| **B** | CNN Custom (LeNet-style) | 85-92% | 10-30ms | Sedang | ✅ Baik | ✅ Ya |
| **C** | MobileNetV2 / EfficientNet-Lite | 88-95% | 15-40ms | Sedang-Tinggi | ✅ Sangat Baik | ✅ Ya |
| **D** | DTW (Dynamic Time Warping) | 75-85% | <20ms | Rendah-Sedang | ✅ Baik | ✅✅ Sangat Baik |
| **E** | Transformer-based (ViT/TrOCR) | 90-97% | 100-500ms | Tinggi | ✅ Baik | ⚠️ Overkill |
| **F** | **Hybrid: DTW + CNN** | **90-96%** | **30-60ms** | **Tinggi** | **✅ Sangat Baik** | **✅✅ Ideal** |

### Detail Per Opsi

#### Opsi A: OpenCV Template Matching (Baseline)
```python
# Current approach - good for MVP, bad for production
# Pro: Super cepat, mudah dipahami, tanpa training
# Con: Hanya 1 template per huruf, sensitif rotasi/skala, tidak belajar dari data
```
- **Dataset yang dibutuhkan:** Tidak ada (template hardcoded)
- **Inference:** CPU-bound, <50ms per image 64x64
- **Verdict:** ✅ **Pertahankan sebagai fallback**, tapi bukan primary

#### Opsi B: CNN Custom (LeNet/CNN sederhana)
- Arsitektur: 2-3 Conv layers + MaxPool + 2 FC layers
- Dataset: EMNIST (814K samples), atau custom dataset anak Indonesia
- Akurasi reported: **87-92%** pada EMNIST By_Class
- Training time: ~30 menit di GPU consumer
- **Library:** PyTorch / TensorFlow / Keras
- **Verdict:** ✅ **Opsi cost-effective untuk MVP v2**

#### Opsi C: MobileNetV2 / EfficientNet-Lite
- Pre-trained on ImageNet → fine-tune untuk handwriting
- Ukuran model: 5-20MB (mobile-friendly)
- Akurasi: **88-95%** dengan transfer learning
- Support ONNX export untuk inference cepat
- **Verdict:** ✅ **Rekomendasi utama untuk production**

#### Opsi D: Dynamic Time Warping (DTW)
- **Online recognition** — bekerja langsung pada stroke coordinates (x,y,t)
- Tidak perlu konversi ke image → lebih natural untuk drawing evaluation
- Bisa memberikan **real-time feedback during drawing**
- Sangat cocok untuk evaluasi **proses** (apakah urutan stroke benar?)
- Akurasi: 75-85% untuk karakter tunggal, bisa dikombinasikan dengan fitur lain
- **Library:** `fastdtw` (Python), `dtw` package
- **Verdict:** ✅✅ **IDEAL untuk evaluasi proses tracing (stroke order)**

#### Opsi E: Transformer-based (TrOCR/ViT)
- State-of-the-art untuk OCR/HWR
- TrOCR (Microsoft): 95%+ akurasi pada benchmark
- **Problem:** Lambat (100-500ms), butuh GPU untuk reasonable latency, overkill untuk single character
- **Verdict:** ❌ **Tidak direkomendasikan untuk fase sekarang** (simpan untuk roadmap jangka panjang)

#### Opsi F: Hybrid DTW + CNN (RECOMMENDED)
- **DTW** untuk evaluasi stroke order + proses (real-time feedback)
- **CNN** untuk evaluasi bentuk visual akhir (post-evaluation)
- Kombinasi memberikan akurasi tertinggi + pengalaman terbaik
- Implementasi: DTW runs client-side during drawing, CNN runs server-side on completion

### 🏆 Rekomendasi: **Phased Approach**

```
FASE 1 (MVP Enhanced):   Template Matching + DTW Stroke Order
                         ↓ Tingkatkan dari 1 huruf → 26 huruf
FASE 2 (Production):     Train CNN (MobileNetV2) dengan dataset anak
                         ↓ Export ONNX, serve via FastAPI + ORT
FASE 3 (Advanced):       Hybrid DTW + CNN untuk maksimal akurasi
                         ↓ Tambahkan reinforcement learning dari feedback guru
```

### Dataset Strategy
| Sumber | Jumlah Sample | Kualitas | Aksi |
|--------|--------------|----------|------|
| EMNIST | 814,255 | Tinggi (dewasa) | Transfer learning base |
| Custom collection (sistem existing) | Growing | Variable | Aktif collect via `/api/evaluate` |
| crowdsourcing dari siswa | Target: 10K+ | Tinggi (target user) | Fase 2 |
| Augmentasi (rotasi, noise, shear) | Unlimited | Synthetic | Boost dataset |

---

## 2. 🎨 CANVAS & DRAWING FRONTEND

### Konteks Saat Ini
- **Raw HTML5 Canvas API** (`Canvas.jsx`)
- Touch + mouse support dasar
- Koordinat dikirim ke backend untuk evaluasi
- **Keterbatasan:** Tidak ada smoothing, tidak ada undo/redo, tidak ada real-time feedback, performa menurun dengan banyak titik

### Library Comparison: Konva.js vs Fabric.js vs Raw Canvas

| Fitur | Raw Canvas (current) | Konva.js + react-konva | Fabric.js |
|-------|---------------------|----------------------|-----------|
| React Integration | Manual (`useRef`) | ✅ Native (`react-konva`) | ✅ Wrapper tersedia |
| Performance | ✅ Paling cepat | ✅ Sangat baik (custom renderer) | ⚠️ Baik |
| Object Model | ❌ Tidak ada | ✅ Node tree (Stage>Layer>Shape) | ✅ Object-oriented |
| Event Handling | Manual | ✅ Built-in (click, drag, touch) | ✅ Built-in |
| Undo/Redo | Manual implement | ✅ Mudah (serialize state) | ✅ Built-in |
| Stroke Smoothing | Manual | ✅ Plugin/tersedia | ✅ Built-in |
| Export (JSON/PNG) | Manual (`toDataURL`) | ✅ `toDataURL()`, `toJSON()` | ✅ Built-in |
| Animation Support | Manual (`requestAnimFrame`) | ✅ Built-in tween | ⚠️ Terbatas |
| Mobile Touch | Manual handling | ✅ Optimized | ✅ Good |
| Bundle Size | 0KB | ~45KB gzipped | ~80KB gzipped |
| Learning Curve | Tinggi | Rendah-Sedang | Sedang |

### 🏆 Rekomendasi: **Konva.js + react-konva**

**Alasan:**
1. **React-native integration** — `react-konva` adalah official React wrapper
2. **Performance** — custom rendering engine, ideal untuk real-time drawing
3. **Node-based architecture** — memudahkan layer management (guide layer, drawing layer, feedback layer)
4. **Active community** — docs lengkap, demo interaktif, StackOverflow support
5. **Ideal untuk use case ini** — freehand drawing + object manipulation + animations

### Fitur yang Harus Ada di Canvas Baru

```
┌─────────────────────────────────────────┐
│  CANVAS FEATURE MATRIX                  │
├─────────────────────────────────────────┤
│  ✅ Stroke smoothing (Chaikin/RDP)      │
│  ✅ Pressure-sensitive thickness        │
│  ✅ Real-time stroke guide overlay      │
│  ✅ Progressive difficulty system       │
│  ✅ Undo/Redo (min 10 steps)            │
│  ✅ Multi-color palette                 │
│  ✅ Eraser mode                         │
│  ✅ Touch-optimized (prevent scroll)    │
│  ✅ Auto-save draft (localStorage)      │
│  ✅ Export stroke data (JSON)           │
│  ✅ Animation feedback (stars, shake)   │
│  ✅ Sound effects (TTS praise)          │
│  ⚠️ Real-time shape hinting (DTW)      │ ← Fase 2
│  ⚠️ Stroke order validation             │ ← Fase 2
└─────────────────────────────────────────┘
```

### Stroke Smoothing Algorithm
- **Ramer-Douglas-Peucker (RDP)** untuk reduksi titik (performa)
- **Chaikin's corner cutting** untuk smoothness visual
- **Combination:** RDP dulu (kurangi 300 titik → 50), lalu Chaikin (smooth curve)

---

## 3. 🏗️ ARCHITEKTUR PLATFORM

### Tech Stack Comparison

| Lapisan | Opsi 1 (Current++) | Opsi 2 (Fullstack) | Opsi 3 (Mobile-first) |
|---------|-------------------|--------------------|---------------------|
| Frontend | **React + Vite** | Next.js 15 | React Native / Expo |
| Canvas | Konva.js + react-konva | Konva.js | react-native-sketch / Expo |
| Backend | **FastAPI (Python)** | API Routes (Next.js) | FastAPI / Firebase Functions |
| AI/ML | Python (native) | Edge (terbatas) | Python server / TF Lite |
| Database | **Supabase (PostgreSQL)** | Supabase / Vercel Postgres | Supabase / Firestore |
| Auth | Supabase Auth | NextAuth / Supabase | Supabase Auth / Firebase Auth |
| Realtime | Supabase Realtime | Pusher / Ably | Supabase Realtime |
| Storage | Supabase Storage | Vercel Blob / S3 | Supabase / Firebase Storage |
| Deploy FE | **Vercel** | Vercel | Expo EAS |
| Deploy BE | **Railway / Render** | N/A | Railway / Google Cloud |

### 🏆 Rekomendasi: **Opsi 1 (React + FastAPI + Supabase)**

**Alasan mempertahankan arsitektur current:**
1. **FastAPI native Python** = seamless dengan ML/AI ecosystem (PyTorch, ONNX, OpenCV, numpy)
2. **Decoupled frontend/backend** = independent scaling
3. **Supabase** = PostgreSQL (ACID), auth, storage, realtime dalam satu platform
4. **Cost effective** untuk skala 30-50 sekolah di Indonesia

### Architecture Diagram (Target)

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   REACT + VITE   │────▶│    FASTAPI       │────▶│    SUPABASE      │
│   (Vercel)       │◀────│   (Railway)      │◀────│   (Cloud)        │
│                  │     │                  │     │                  │
│ • react-konva    │     │ • /api/evaluate  │     │ • PostgreSQL     │
│ • Tailwind CSS   │     │ • /api/login-qr  │     │ • Auth           │
│ • Phosphor Icons │     │ • /api/stats     │     │ • Storage        │
│ • Framer Motion  │     │ • /api/lessons   │     │ • Realtime       │
│ • Vite PWA       │     │ • WebSocket      │     │ • Edge Functions │
└──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   AI/ML ENGINE   │
                        │                  │
                        │ • ONNX Runtime   │
                        │ • CNN Model      │
                        │ • DTW Algorithm  │
                        │ • OpenCV Utils   │
                        └──────────────────┘
```

---

## 4. 💾 DATABASE & BACKEND AS A SERVICE (BaaS)

### Supabase vs Firebase vs PostgreSQL Direct

| Kriteria | **Supabase** ⭐ | Firebase | PostgreSQL Direct |
|----------|----------------|----------|-------------------|
| **Database** | PostgreSQL (full SQL) | Firestore (NoSQL) | PostgreSQL |
| **Query Language** | SQL (powerful) | NoSQL queries | SQL |
| **Relations/Joins** | ✅ Native | ❌ Emulation | ✅ Native |
| **ACID Transactions** | ✅ Full | ❌ Limited | ✅ Full |
| **Auth** | ✅ GoTrue (flexible) | ✅ Firebase Auth | Manual |
| **Realtime** | ✅ PostgreSQL replication | ✅ Native | Manual (pg_notify) |
| **Storage** | ✅ S3-compatible | ✅ Google Cloud | Manual (S3) |
| **Edge Functions** | ✅ Deno-based | ✅ Cloud Functions | N/A |
| **Offline Sync** | ⚠️ Growing | ✅ Mature | Manual |
| **Open Source** | ✅ Self-host possible | ❌ Proprietary | ✅ |
| **Free Tier** | Generous (500MB DB) | Generous (1GB Firestore) | N/A |
| **Indonesia Latency** | ⚠️ AWS us-east (default) | ✅ Multi-region | Depends |
| **Cost @ Scale** | Predictable | Can spike | Most predictable |

### 🏆 Rekomendasi: **Tetap Supabase** (dengan catatan)

**Mengapa Supabase menang untuk Sahabat Aksara:**
1. **SQL native** = complex queries untuk analytics guru (avg scores, trends, rankings)
2. **Relations** = profiles → student_progress → lessons (foreign keys!)
3. **Open source** = bisa self-host jika perlu compliance data (Indonesian data residency)
4. **Python SDK** = seamless dengan FastAPI backend
5. **Dashboard** = built-in table editor untuk non-technical staff

**Catatan untuk produksi:**
- Pertimbangkan **Supabase self-hosted** di cloud Indonesia (IDCloudHost/Nutanix) untuk latensi rendah
- Atau gunakan **pgbouncer** untuk connection pooling di high-concurrency

### Schema Evolution (dari current)

```sql
-- EXTENDED SCHEMA for Production
-- Current: profiles, lessons, student_progress (basic)

-- 1. Users & Roles
tables: profiles (extend with: school_id, class_id, parent_phone, avatar_url)
tables: schools (id, name, address, subscription_tier)
tables: classes (id, school_id, grade_level, teacher_id)

-- 2. Curriculum  
tables: lessons (extend with: difficulty_level, stroke_order_json, template_image_url)
tables: modules (id, name, order, category: alphabet|number|vowel|consonant)
tables: characters (id, char, category, stroke_guide_svg)

-- 3. Progress & Analytics
tables: student_progress (extend with: attempt_number, time_taken, stroke_data_json, feedback_given)
tables: lesson_attempts (id, student_id, lesson_id, accuracy, stars, session_id)
tables: daily_activity (id, student_id, date, total_practice, avg_accuracy)

-- 4. Gamification
tables: achievements (id, name, description, icon, condition_json)
tables: student_achievements (student_id, achievement_id, unlocked_at)
tables: streaks (student_id, current_streak, longest_streak, last_practice_date)

-- 5. Teacher Tools
tables: teacher_notes (id, teacher_id, student_id, content, created_at)
tables: announcements (id, school_id, teacher_id, content, target_class)
```

---

## 5. 🚀 DEPLOYMENT & INFRASTRUCTURE

### Platform Comparison

| Platform | Frontend | Backend (Python/ML) | Free Tier | Paid Start | Best For |
|----------|----------|--------------------|-----------|-----------|----------|
| **Vercel** | ✅ Ideal | ⚠️ Only Node.js | ✅ Generous | $20/mo | React/Next.js frontend |
| **Render** | ✅ Good | ✅ **Native support** | ✅ 750h free | $7/mo | Full-stack with Python |
| **Railway** | ⚠️ Via Docker | ✅ **Excellent DX** | ❌ Removed (2024) | $5/mo | Microservices, databases |
| **Fly.io** | ✅ Via Docker | ✅ **Global edge** | ✅ 3 shared VMs | ~$5/mo | Low-latency global |
| **IDCloudHost** | ✅ VPS | ✅ Full control | ~Rp50rb/bln | ~Rp200rb/bln | **Indonesia-based** |

### 🏆 Rekomendasi: **Hybrid Deployment**

```
PRODUCTION SETUP:
┌────────────────────────────────────────────────────┐
│                                                    │
│  FRONTEND:  Vercel (CDN-global, auto-SSL, deploy)  │
│              ↓ PWA + Service Worker                │
│                                                    │
│  BACKEND:   Render / Railway (FastAPI + uvicorn)   │
│              ↓ Auto-deploy from GitHub              │
│              ↓ Gunicorn workers (2-4 cores)         │
│                                                    │
│  AI/ML:     Same server (ONNX Runtime, CPU first)   │
│              ↓ GPU instance jika perlu (Render)     │
│                                                    │
│  DATABASE:  Supabase Cloud (or self-hosted ID)      │
│              ↓ Point-in-time recovery               │
│                                                    │
│  STORAGE:  Supabase Storage (S3-backed)             │
│              ↓ Student drawings, templates          │
│                                                    │
│  MONTHLY COST ESTIMATE:                             │
│  • Vercel:        $0-20/mo  (Pro tier)             │
│  • Render:        $7-25/mo   (Starter+)             │
│  • Supabase:      $0-25/mo   (Pro tier)             │
│  • TOTAL:         ~$25-70/mo for 30-50 schools      │
│  ≈ Rp 400.000 - 1.100.000/bulan                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Alternatif Budget (Indonesia):**
- **IDCloudHost / Niagahoster VPS** (Rp 200-500K/bulan) untuk self-hosted semua
- Trade-off: manual maintenance, tapi full control + low latency

---

## 6. 🎮 GAMIFICATION & ENGAGEMENT

### Research Findings

Berdasarkan penelitian tentang gamifikasi dalam edtech anak-anak:

**Elemen yang TERBUKTI efektif untuk usia 4-6:**
1. **Immediate Feedback** — suara/animasi langsung setelah action (< 500ms)
2. **Stars/Reward System** — visual reward yang jelas (⭐⭐⭐)
3. **Progress Visualization** — bar, pohon yang tumbuh, karakter yang berkembang
4. **Sound Effects** — TTS praise ("Luar biasa!"), celebratory sounds
5. **Streaks** — konsistensi harian (flame icon seperti Duolingo)
6. **Avatars** — personalisasi karakter (pakaian, aksesori dari reward)
7. **Story/Narrative** — misi "menolong karakter" dengan menulis huruf

**Elemen yang KURANG efektif / berisiko untuk usia 4-6:**
- ❌ Leaderboards (bisa demotivasi anak yang tertinggal)
- ❌ Timer/pressure (menyebabkan anxiety)
- ❌ Complex point systems (terlalu abstrak)
- ❌ Punishment/penalti (negative reinforcement kurang efektif)

### Gamification System Design untuk Sahabat Aksara

```
┌──────────────────────────────────────────────┐
│  GAMIFICATION LOOP                           │
│                                              │
│  [Siswa mulai latihan]                       │
│       ↓                                      │
│  [Tracing huruf dengan panduan]              │
│       ↓                                      │
│  [Real-time hint (DTW)] ← Fase 2            │
│       ↓                                      │
│  [Selesai → Evaluasi (CNN)]                 │
│       ↓                                      │
│  ├── Accuracy ≥ 90%: 3⭐ + sound "Hebat!"   │
│  ├── Accuracy ≥ 70%: 2⭐ + sound "Bagus!"   │
│  ├── Accuracy ≥ 50%: 1⭐ + "Ayo coba lagi"  │
│  └── Accuracy < 50%: 0⭐ + gentle guidance  │
│       ↓                                      │
│  [Update progress bar modul]                 │
│       ↓                                      │
│  [Cek achievement unlock?]                  │
│       ↓                                      │
│  [Update streak harian]                      │
│       ↓                                      │
│  [Sync ke dashboard guru (realtime)]         │
│                                              │
└──────────────────────────────────────────────┘

ACHIEVEMENT EXAMPLES:
🏆 "Pertama Kali" — menulis huruf pertama kali
🔥 "Bersemangat!" — 7 hari streak
⭐ "Bintang Tiga" — dapat 3 bintang 10x berturut
📚 "Ahli Alfabet" — selesai semua huruf A-Z
🎨 "Seniman Kecil" — coba 5 warna berbeda
🚀 "Super Cepat" — selesai dalam waktu singkat
```

### Sound & Animation Stack
| Teknologi | Use Case | Library |
|-----------|----------|---------|
| **Web Speech API (TTS)** | Praise in Bahasa Indonesia | Browser-native |
| **Howler.js** | Sound effects (pop, whoosh, celebrate) | `howler` npm |
| **Framer Motion** | UI animations (shake, bounce, confetti) | `framer-motion` |
| **canvas-confetti** | Celebration effect (3 stars) | `canvas-confetti` |
| **Lottie** | Complex animated stickers/rewards | `lottie-react` |

---

## 7. 📱 PWA & OFFLINE CAPABILITY

### Mengapa Penting untuk Sahabat Aksara?
- Target user: PAUD/TK di **seluruh Indonesia** (termasuk daerah dengan internet tidak stabil)
- Guru mungkin perlu akses dashboard tanpa internet
- Siswa perlu tetap bisa latihan meski offline (sync nanti)

### PWA Implementation Plan

```
PWA FEATURES FOR SAHABAT AKSARA:

✅ SERVICE WORKER:
   - Cache shell app (HTML/CSS/JS bundles)
   - Cache strategy: Stale-While-Revalidate for API responses
   - Background sync untuk hasil evaluasi offline

✅ OFFLINE DRAWING:
   - Canvas tetap functional (client-side only)
   - Simpan stroke data ke IndexedDB
   - Queue evaluasi untuk saat online kembali

✅ MANIFEST:
   - Name: "Sahabat Aksara"
   - Display: standalone (fullscreen)
   - Theme color: #87CEEB (pastel sky)
   - Icons: maskable + standard sizes

⚠️ OFFLINE LIMITATIONS:
   - Evaluasi AI (CNN) memerlukan server → queue mode
   - Login QR perlu camera + network → cache auth token
   - Dashboard guru → tampilkan cached data + indicator "offline"
```

### Tech Stack untuk PWA
- **Vite PWA Plugin** (`vite-plugin-pwa`) — Workbox generation otomatis
- **IndexedDB** via `idb` library — menyimpan offline drafts
- **Network Information API** — detect connection quality

---

## 8. 🇮🇩 INDONESIA-SPECIFIC CONSIDERATIONS

### Lokalisasi
| Aspek | Implementasi |
|-------|-------------|
| **Bahasa** | Full Indonesian UI + TTS (`lang="id-ID"`) |
| **Huruf** | Latin A-Z + a-z + Angka 0-9 (+ roadmap: aksara Jawa/Bali?) |
| **Nama siswa** | Unicode support untuk nama Indonesia (multi-word, apostrophe) |
| **Timezone** | `Asia/Jakarta` (WIB), `Asia/Makassar` (WITA), `Asia/Jayapura` (WIT) |
| **Number format** | Indonesian locale (`id-ID`: 1.234,56) |
| **Currency** | Rupiah (Rp) untuk subscription tiers |

### Infrastructure Indonesia
| Provider | Use Case | Estimasi Cost |
|----------|----------|--------------|
| **CDN**: Cloudflare | Global CDN + caching | Free tier cukup |
| **Domain**: .co.id / .sch.id | Trust factor | ~Rp 100-300rb/thn |
| **Self-host option**: IDCloudHost | Full control, low latency | Rp 200-500rb/bln |
| **Payment**: Midtrans / Xendit | Subscription payment | 2-5% per transaction |

---

## 📊 DECISION MATRIX SUMMARY

| # | Keputusan | Opsi Terbaik | Confidence | Priority |
|---|-----------|-------------|------------|----------|
| 1 | Recognition Engine | **Phased: Template→CNN+DTW Hybrid** | 🟢 High | P0 |
| 2 | Canvas Library | **Konva.js + react-konva** | 🟢 High | P0 |
| 3 | Frontend Framework | **React + Vite (pertahankan)** | 🟢 High | P0 |
| 4 | Backend Framework | **FastAPI (pertahankan)** | 🟢 High | P0 |
| 5 | BaaS/Database | **Supabase (pertahankan)** | 🟢 Medium-High | P0 |
| 6 | Deployment FE | **Vercel** | 🟢 High | P1 |
| 7 | Deployment BE | **Render (free tier) / Railway** | 🟡 Medium | P1 |
| 8 | ML Inference | **ONNX Runtime + FastAPI** | 🟢 High | P1 |
| 9 | Gamification | **Stars + Streak + TTS + Confetti** | 🟢 High | P1 |
| 10 | PWA/Offline | **Vite PWA Plugin + IndexedDB** | 🟢 High | P2 |
| 11 | State Management | **Zustand / TanStack Query** | 🟡 Medium | P1 |

---

## 🗺️ ROADMAP IMPLEMENTASI

```
PHASE 0 — FOUNDATION (Minggu 1-2)
├── Refactor Canvas: Raw Canvas → react-konva
├── Add stroke smoothing (RDP + Chaikin)
├── Extend template matching ke 26 huruf
├── Setup Vite PWA plugin
└── [DELIVERABLE] Canvas yang jauh lebih smooth + 26 huruf

PHASE 1 — MVP ENHANCED (Minggu 3-5)
├── Train CNN sederhana (EMNIST transfer learning)
├── Export model ke ONNX
├── Integrate ONNX Runtime ke FastAPI
├── Implement DTW untuk stroke order validation
├── Extended database schema
├── Basic gamification (stars, sounds, simple animations)
└── [DELIVERABLE] Evaluasi AI untuk 26 huruf A-Z

PHASE 2 — PRODUCTION READY (Minggu 6-9)
├── Hybrid evaluation (DTW realtime + CNN post-eval)
├── Teacher dashboard revamp (realtime charts)
├── QR login production flow (camera integration)
├── Achievement/streak system
├── Offline mode (service worker + IndexedDB)
├── Progress tracking analytics
└── [DELIVERABLE] Production-ready platform

PHASE 3 — SCALE (Minggu 10-12)
├── Multi-school support
├── Teacher content management (buat modul custom)
├── Advanced analytics (per-class, per-school reports)
├── Deployment optimization (CDN, caching)
├── User testing dengan PAUD nyata
└── [DELIVERABLE] Pilot dengan 2-3 sekolah
```

---

## 📚 SOURCES & REFERENSI

### Handwriting Recognition
- Cohen, G. et al. (2017). "EMNIST: an extension of MNIST to handwritten letters" — arXiv:1702.05373
- MDPI Applied Sciences (2019). "A Survey of Handwritten Character Recognition with MNIST and EMNIST"
- Springer Neural Computing and Applications (2024). "Offline English handwritten character recognition using ELBP-based sequential CNN"
- ResearchGate: "Dynamic Time Warping Algorithm for Recognition of Multi-Stroke On-Line Handwritten Characters"
- ScienceDirect: "Dynamic time warping: A new method in the study of poor handwriting"

### Canvas & Drawing
- Konva.js Official Docs: https://konvajs.org/docs/
- "Konva.js vs Fabric.js: Choosing Your Canvas Companion" — Oreate AI Blog
- "React: Comparison of JS Canvas Libraries (Konvajs vs Fabricjs)" — DEV Community
- "Why Konva? When to Use Konva.js" — Konva Docs

### EdTech Architecture
- DEV Community: "How We Built an EdTech Platform That Scaled to 250K Daily Users"
- DEV Community: "EdTech Platform Architecture, Lessons from Real Builds"
- Successive Tech: "Comprehensive Guide to EdTech App Development in 2024"
- WeAreBrain: "The best tech stack for EdTech platforms in 2026"

### Deployment & Infrastructure
- Microsoft Azure Blog: "Scaling-up PyTorch inference: Serving billions of daily NLP inferences with ONNX Runtime"
- PyImageSearch: "FastAPI Docker Deployment: Preparing ONNX AI Models for AWS Lambda"
- AgileSoft: "FastAPI, Docker, AWS: AI Production Deployment 2026"

### Gamification
- OpenLMS: "Gamification in Education: How to Use It"
- Park University: "The Gamification of Learning: Engaging Students through Technology"
- Yu-Kai Chou: "10 Best Gamified Education Apps"
- GIANTY: "How Gamification Helps Boost User Engagement (2025)"

### PWA & Offline
- MDN: "Offline and background operation — Progressive Web Apps"
- Google Codelabs: "Progressive Web Apps: Going Offline"
- MagicBell: "Offline-First PWAs: Service Worker Caching Strategies"

### Supabase vs Firebase
- Bytebase: "Supabase vs. Firebase: a Complete Comparison in 2026"
- Leanware: "Best Practices for Supabase: Security, Scaling & Maintainability"
- Rocket Blog: "Firebase Vs Supabase Comparison: Features, Pricing And More"

---

*Dokumen ini digenerate dari penelitian web mendalam pada tanggal 28 Mei 2026. Semua rekomendasi harus divalidasi dengan team sebelum implementasi.*
