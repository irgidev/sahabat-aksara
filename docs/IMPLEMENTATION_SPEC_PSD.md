# 📊 Sahabat Aksara — Implementation Spec PSD

> **Mata Kuliah:** Pengantar Sains Data  
> **Fokus:** Pipeline Data, Computer Vision & Analitik  
> **Tanggal:** 2026-05-29  
> **Status:** Ready for Phase-by-Phase Implementation  
> **Integrasi:** Menerima input dari RPL (Canvas/UI) → mengolah data → meneruskan ke PKB (AI Model)

---

## 🎯 Ringkasan Eksekutif

Spec ini mendefinisikan **seluruh workflow Data Science** di Sahabat Aksara:
1. **Data Collection** — menangkap coretan siswa dari Canvas menjadi dataset terstruktur
2. **Data Preprocessing** — membersihkan, menormalisasi, mengekstrak fitur dari gambar
3. **Feature Engineering** — mengubah raw pixel menjadi fitur yang bermakna
4. **Exploratory Data Analysis (EDA)** — memahami pola data lewat visualisasi
5. **Dashboarding / Data Storytelling** — menyajikan insight ke Guru lewat chart & metrik
6. **Computer Vision Pipeline** — face detection, image processing, descriptor extraction

**Alur Data PSD:**
```
Raw Input (Canvas)          Processed Data           Insights (Dashboard)
┌──────────────┐           ┌──────────────┐         ┌──────────────┐
│ Stroke coords │ ──►      │ 64×64 PNG    │ ──►     │ Chart        │
│ (x,y points)  │ normalize│ Grayscale    │ aggregate│ Metric Cards │
│ Webcam frame  │ ──►      │ Face desc.   │ ──►     │ Activity Feed│
│                │ extract  │ (128-dim)    │ analyze │ Reports      │
└──────────────┘           └──────────────┘         └──────────────┘
       ↑                           ↑                         ↑
       │ RPL                       │ PSD                      │ RPL+PSD
   Frontend Capture           AI Core Process           Dashboard Display
```

---

## 🏗️ Arsitektur Data Pipeline PSD

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PSD DATA PIPELINE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LAYER 1: DATA ACQUISITION (Collection)                                  │
│  ├── Canvas.jsx          → Stroke coordinates (x,y,t)                   │
│  ├── CameraView.jsx      → Webcam frames (face detection)               │
│  ├── face-api.js         → Face descriptors (128-dim vector)            │
│  └── Output              → data_science/datasets/ + Supabase Storage    │
│                                                                          │
│  LAYER 2: DATA PREPROCESSING (Cleaning & Normalization)                 │
│  ├── main.py /evaluate   → Coords → Bounding box → Scale → 64×64 PNG   │
│  ├── pattern_matching.py → Binary threshold → Skeletonize → Normalize   │
│  └── Output              → Clean grayscale images, ready for analysis   │
│                                                                          │
│  LAYER 3: FEATURE EXTRACTION (Engineering)                              │
│  ├── Image features     → Pixel count, aspect ratio, centroid          │
│  ├── Shape features     → Contour area, perimeter, solidity             │
│  ├── Histogram features → Intensity distribution (64-bin histogram)     │
│  ├── Hu Moments         → 7 invariant moments (shape signature)         │
│  ├── HOG features       → Histogram of Oriented Gradients               │
│  └── Output              → Structured feature vectors per sample         │
│                                                                          │
│  LAYER 4: ANALYTICS & VISUALIZATION (Dashboarding)                      │
│  ├── Dashboard.jsx      → Recharts (BarChart, Line, Pie)               │
│  ├── /api/dashboard/*   → Aggregated metrics, trends, reports           │
│  ├── notebooks/         → Jupyter EDA, experiment tracking              │
│  └── Output              → Charts, tables, insights untuk Guru           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Target Struktur Folder PSD

```
sahabat-aksara/
├── data_science/                          ← PSD WORKSPACE (INTI)
│   ├── datasets/                          ← RAW DATA LAKE
│   │   ├── raw/                           ← Original screenshots (jika perlu)
│   │   ├── processed/                     ← Normalized 64×64 PNG (output /api/evaluate)
│   │   │   ├── stroke_*.png               ← Sudang ada ~25+ file
│   │   │   └── ...                        ← Terus bertambah setiap latihan
│   │   ├── features/                      ← Extracted feature vectors (CSV/NPY)
│   │   │   ├── all_features.csv           ← Seluruh fitur per sample
│   │   │   ├── image_features.csv         ← Fitur image saja
│   │   │   └── shape_features.csv         ← Fitur shape/contour saja
│   │   └── labels.csv                     ← Ground truth labels (char_target, accuracy)
│   │
│   ├── notebooks/                         ← JUPYTER NOTEBOOKS (EDA & EXPERIMENT)
│   │   ├── 01_data_exploration.ipynb      ← EDA: distribusi data, sample preview
│   │   ├── 02_preprocessing_pipeline.ipynb ← Preprocessing: clean, normalize, augment
│   │   ├── 03_feature_engineering.ipynb   ← Ekstraksi fitur: HOG, Hu, histogram
│   │   ├── 04_visualization_dashboard.ipynb ← Re-create dashboard charts di notebook
│   │   ├── 05_character_analysis.ipynb    ← Analisis per karakter: mana yang sulit?
│   │   └── 06_student_profiling.ipynb     ← Profiling siswa: siapa yang butuh bantuan?
│   │
│   ├── scripts/                           ← PYTHON SCRIPTS (AUTOMATED PIPELINE)
│   │   ├── build_dataset.py               ← Scan datasets/ → generate feature CSV
│   │   ├── preprocess_batch.py            ← Batch preprocessing: resize, threshold, clean
│   │   ├── augment_data.py                ← Augmentasi: rotate, noise, shear, blur
│   │   ├── extract_features.py            ← Ekstrak semua fitur dari folder gambar
│   │   ├── generate_statistics.py         ← Hitung statistik deskriptif seluruh data
│   │   └── export_for_training.py         ← Export dataset siap pakai untuk PKB (train/test split)
│   │
│   └── reports/                           ← GENERATED REPORTS (OUTPUT)
│       ├── eda_report.html                ← Auto-generated EDA report
│       ├── data_quality_report.json       ← Data quality metrics
│       ├── character_difficulty.json      ← Tingkat kesulitan per huruf
│       └── student_insights.json          ← Insight per siswa
│
├── frontend/src/                           ← FRONTEND PSD COMPONENTS
│   ├── components/
│   │   ├── Canvas.jsx                     ← Data acquisition interface (sudah ada, upgrade)
│   │   ├── CameraView.jsx                 ← CV data capture (sudah ada)
│   │   └── Dashboard.jsx                  ← Visualisasi analytics (sudah ada, enrich)
│   └── lib/
│       └── face-api.js                    ← Feature extraction wajah (sudah ada)
│
└── backend/
    └── main.py                            ← API endpoints data processing (upgrade)
```

---

## 🚞 FASE-FASE IMPLEMENTASI PSD

---

## ✅ FASE PSD-1: Data Collection Pipeline (Pengumpulan Data)

**Goal:** Pastikan setiap latihan siswa terekam sebagai data terstruktur yang bisa dianalisis

**Estimasi:** 2-3 jam

**Depends on:** RPL Fase 4 (Canvas sudah jalan)

### Checklist PSD-1:

#### 1.1 Enhance `/api/evaluate` — Rich Data Capture
**File:** `backend/main.py`

Saat ini endpoint hanya simpan gambar + akurasi. **Tambahkan:**

- [ ] **Simpan stroke metadata ke `student_progress.stroke_data`:**
  ```json
  {
    "point_count": 147,
    "bounding_box": { "width": 234, "height": 189 },
    "canvas_size": { "w": 600, "h": 400 },
    "duration_ms": 4500,
    "color_used": "#1e293b",
    "device_type": "mobile|tablet|desktop"
  }
  ```
- [ ] **Simpan normalized image path** ke Supabase Storage (sudah ada, pastikan konsisten)
- [ ] **Tambahkan timestamp presisi** (`created_at` dengan timezone Asia/Jakarta)
- [ ] **Tambahkan `session_id`** untuk kelompokkan latihan satu sesi
- [ ] **Log version algorithm** (`algorithm_version: "v3-skeleton"`) untuk tracking perubahan

#### 1.2 Enhance `Canvas.jsx` — Metadata Collection
**File:** `frontend/src/components/Canvas.jsx`

- [ ] **Track waktu mulai-selesai** (berapa lama siswa menulis?)
- [ ] **Hitung jumlah titik** (point count — indikator ketelitian vs cepat-cepat)
- [ ] **Detect device type** (mobile/tablet/desktop — untuk analisis UX)
- [ ] **Kirim metadata tambahan** bersama koordinat stroke ke `/api/evaluate`
- [ ] **Auto-save draft** ke `localStorage` (kalau browser tertutup tidak hilang)

#### 1.3 Organize `data_science/datasets/`
**Folder:** `data_science/datasets/`

- [ ] **Buat subfolder structure:**
  ```
  datasets/
  ├── raw/              ← Screenshots mentah (jika mau keep original)
  ├── processed/        ← 64×64 normalized grayscale (output dari /api/evaluate)
  │   ├── A/            ← Group by character
  │   ├── B/
  │   └── ...
  └── exports/          ← Dataset siap export (zip untuk training)
  ```
- [ ] **Update `/api/evaluate`:** simpan ke `processed/{char_target}/` bukan root
- [ ] **Generate `dataset_manifest.json`:** index semua file dengan metadata

#### 1.4 Build `scripts/build_dataset.py` — Dataset Builder
**File baru:** `data_science/scripts/build_dataset.py`

```python
# Fungsi-fungsi utama:
def scan_datasets_folder() -> list:
    """Scan semua PNG di datasets/, return metadata"""

def group_by_character(files: list) -> dict:
    """Group files berdasarkan huruf target"""

def compute_dataset_statistics(groups: dict) -> dict:
    """Hitung: total samples per char, avg file size, dll"""

def generate_manifest(output_path: str):
    """Generate dataset_manifest.json"""

def validate_data_integrity(manifest: dict) -> dict:
    """Cek: file corrupt? duplikat? missing label?"""
```

- [ ] Scan otomatis folder `datasets/`
- [ ] Group by character target
- [ ] Hitung statistik dasar (count per char, size distribution)
- [ ] Generate `dataset_manifest.json`
- [ ] Validasi integritas data (file corrupt, missing)

### Deliverable PSD-1:
> Setiap kali siswa menulis di Canvas → data lengkap tersimpan (gambar + metadata) → terorganisir di `data_science/datasets/` → `dataset_manifest.json` selalu update.

---

## 🔧 FASE PSD-2: Preprocessing & Cleaning Pipeline

**Goal:** Bersihkan dan normalisasi data gambar agar konsisten untuk analisis & modeling

**Estimasi:** 3-4 jam

**Depends on:** PSD-1 (data sudah terkumpul)

### Checklist PSD-2:

#### 2.1 Build `scripts/preprocess_batch.py` — Batch Preprocessing
**File baru:** `data_science/scripts/preprocess_batch.py`

```python
# Pipeline steps (sequential):
def load_image(path: str) -> np.ndarray:
    """Load PNG, handle error"""

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert ke grayscale kalau RGB"""

def apply_threshold(img: np.ndarray, method='otsu') -> np.ndarray:
    """Binarisasi: Otsu's adaptive atau fixed threshold"""

def remove_noise(img: np.ndarray, method='morphological') -> np.ndarray:
    """Remove noise specks: morphological opening"""

def normalize_size(img: str, target_size=64) -> np.ndarray:
    """Resize ke target size dengan aspect ratio preservation"""

def center_content(img: np.ndarray) -> np.ndarray:
    """Center content di canvas (crop to bounding box + pad)"""

def invert_if_needed(img: np.ndarray) -> np.ndarray:
    """Pastikan foreground = white, background = black"""

def run_full_pipeline(input_path: str, output_path: str) -> dict:
    """Jalankan semua step, return processing log"""
```

- [ ] Implementasi 7 langkah preprocessing di atas
- [ ] Support batch processing (seluruh folder)
- [ ] Logging setiap step (before/after image disimpan untuk debugging)
- [ ] Handle edge case: gambar kosong (blank canvas), gambar full-white

#### 2.2 Build `scripts/augment_data.py` — Data Augmentation
**File baru:** `data_science/scripts/augment_data.py`

Augmentasi penting karena **dataset anak TK biasanya kecil (<1000 sample)**. Augmentasi memperbesar dataset secara synthetic.

```python
# Augmentation techniques (untuk handwriting):
def rotate(img, angle_range=(-15, 15)):
    """Rotasi kecil (-15° sampai +15°) — simulasi miring menulis"""

def translate(img, px_range=(-3, 3)):
    """Geser sedikit — simulasi posisi tidak sempurna"""

def scale(img, scale_range=(0.85, 1.15)):
    """Scale sedikit — simulasi ukuran tulisan bervariasi"""

def elastic_distortion(img, alpha=30, sigma=4):
    """Distorsi elastis — simulasi goresan tidak stabil (anak TK!)"""

def add_noise(img, noise_type='gaussian', intensity=0.02):
    """Tambah noise — simulasi kamera jelek / compression artifact"""

def blur(img, kernel_range=(1, 3)):
    """Blur sedikit — simulasi fokus tidak sempurna"""

def change_thickness(img, dilation_range=(-2, 2)):
    """Ubah ketebalan stroke — simulasi tekanan berbeda"""

def augment_sample(img, num_variants=10) -> list:
    """Generate N variant dari 1 sample (random combo)"""
```

- [ ] Implementasi 7 teknik augmentasi
- [ ] Generate 10x variant per sample (1 gambar asli → 11 total)
- [ ] Simpan ke folder `datasets/augmented/` dengan naming `{original}_{aug_id}.png`
- [ ] Log augmentasi params ke CSV (traceability)

#### 2.3 Build `scripts/extract_features.py` — Feature Extraction Engine ⭐
**File baru:** `data_science/scripts/extract_features.py`

Ini adalah **inti PSD** — mengubah gambar menjadi fitur numerik yang bisa dianalisis dan dimasukkan ke model ML.

```python
# === GROUP 1: BASIC IMAGE FEATURES ===
def extract_basic_features(img_bin) -> dict:
    """
    - pixel_count: jumlah piksel foreground (ketebalan/ukuran tulisan)
    - foreground_ratio: % piksel yang bukan background
    - aspect_ratio: rasio width/height bounding box
    - fill_ratio: % bounding box yang terisi (density)
    - centroid: pusat mass tulisan (x, y) — kiri/kanan/atas/bawah bias
    """

# === GROUP 2: SHAPE/CONTOUR FEATURES ===
def extract_contour_features(img_bin) -> dict:
    """
    - contour_count: jumlah kontur terpisah (goresan terputus?)
    - max_contour_area: area kontur terbesar
    - total_perimeter: total keliling semua kontur
    - solidity: area / convex_hull_area (1.0 = solid, <1.0 = cekung)
    - extent: area / bounding_box_area
    - eccentricity: kebulatan (0=circular, 1=elongated)
    - compactness: 4*pi*area / perimeter^2
    """

# === GROUP 3: HU MOMENTS (Shape Signature) ===
def extract_hu_moments(img_bin) -> dict:
    """
    - hu1 s.d. hu7: 7 moment invariant (scale, rotation, translation invariant!)
    - Ini adalah SIGNATURE bentuk yang unik per karakter
    - Sangat berguna untuk klasifikasi huruf
    """

# === GROUP 4: HISTOGRAM FEATURES ===
def extract_histogram_features(img_gray) -> dict:
    """
    - hist_mean: rata-rata intensitas
    - hist_std: deviasi intensitas (variasi ketebalan?)
    - hist_skewness: kemiringan distribusi
    - hist_kurtosis: keruncingan distribusi
    - hist_entropy: entropy ( kompleksitas/keacakan)
    - hist_64bin: 64-bin histogram intensitas (64 dimensi!)
    """

# === GROUP 5: TEXTURE FEATURES (optional, advanced) ===
def extract_texture_features(img_gray) -> dict:
    """
    - glcm_contrast: kontras (Local Binary Pattern / GLCM)
    - glcm_homogeneity: homogenitas
    - glcm_energy: energi tekstur
    - lbp_hist: Local Binary Pattern histogram (256-dim)
    """

# === MASTER FUNCTION ===
def extract_all_features(image_path: str, char_target: str = None) -> dict:
    """
    Jalankan SEMUA extractor → combine ke 1 dictionary flat
    Output: ~100+ fitur numerik per gambar
    """
```

- [ ] Implementasi 5 grup fitur extractor (total ~100+ fitur)
- [ ] Output ke CSV: 1 baris = 1 gambar, kolom = fitur-fitur
- [ ] Include metadata columns: filename, char_target, source_student, timestamp
- [ ] Handle error gracefully: gambar kosong → fitur = 0 atau NaN

#### 2.4 Build `scripts/generate_statistics.py` — Descriptive Statistics
**File baru:** `data_science/scripts/generate_statistics.py`

```python
def compute_class_statistics(feature_csv: str) -> dict:
    """Per karakter: mean, std, min, max, median, quartiles"""

def compute_correlation_matrix(feature_csv: str) -> np.ndarray:
    """Korelasi antar-fitur — mana yang paling informatif?"""

def detect_outliers(feature_csv: str, method='iqr') -> list:
    """Deteksi outlier sample (gambar aneh/corrupt)"""

def generate_data_quality_report(dataset_path: str) -> dict:
    """
    - Total samples
    - Samples per class (character) balance
    - Missing values per feature
    - Outlier count
    - Feature distributions summary
    """
```

- [ ] Statistik deskriptif per karakter (central tendency, spread)
- [ ] Matriks korelasi antar-fitur
- [ ] Deteksi outlier & anomali
- [ ] Data quality report (balance check, missing values)

### Deliverable PSD-2:
> Jalankan `preprocess_batch.py` → data bersih. Jalankan `augment_data.py` → dataset berkembang 10x. Jalankan `extract_features.csv` → file CSV dengan 100+ fitur siap analisis. Jalankan `generate_statistics.py` → laporan kualitas data.

---

## 📊 FASE PSD-3: Exploratory Data Analysis (EDA) Notebooks

**Goal:** Pahami data lewat visualisasi di Jupyter Notebook — temukan insight, pola, anomali

**Estimasi:** 3-4 jam

**Depends on:** PSD-2 (fitur sudah diekstrak ke CSV)

### Checklist PSD-3:

#### 3.1 Notebook: `01_data_exploration.ipynb` — EDA Dasar
**File:** `data_science/notebooks/01_data_exploration.ipynb`

- [ ] **Load dataset manifest** + feature CSV
- [ ] **Sample visualization:** tampilkan 20 gambar random dari dataset (grid 4×5)
- [ ] **Distribusi data per karakter:** bar chart — berapa sample per huruf?
- [ ] **Class imbalance check:** apakah ada huruf yang jarang/tidak ada samasekali?
- [ ] **Distribusi akurasi:** histogram — umumnya siswa dapat skor berapa?
- [ ] **Distribusi per siswa:** siswa mana yang paling aktif latihan?
- [ ] **Image size analysis:** ukuran file, resolusi variance
- [ ] ** Kesimpulan awal:** apa yang menarik dari data?

#### 3.2 Notebook: `02_preprocessing_pipeline.ipynb` — Preprocessing Demo
**File:** `data_science/notebooks/02_preprocessing_pipeline.ipynb`

- [ ] **Show before/after** setiap preprocessing step (visual comparison grid)
- [ ] **Thresholding comparison:** fixed vs Otsu vs Adaptive — mana yang terbaik untuk handwriting anak?
- [ ] **Augmentation showcase:** tampilkan 1 gambar + 10 variannya side-by-side
- [ ] **Quality metrics:** PSNR/SSIM sebelum vs sesudah preprocessing
- [ ] **Recommendation:** preprocessing config terbaik untuk dataset ini

#### 3.3 Notebook: `03_feature_engineering.ipynb` — Analisis Fitur
**File:** `data_science/notebooks/03_feature_engineering.ipynb`

- [ ] **Feature distribution:** histogram untuk top-20 fitur penting
- [ ] **Box plot per karakter:** fitur mana yang paling membedakan 'A' vs 'B' vs 'C'?
- [ ] **Correlation heatmap:** fitur mana yang redundan (highly correlated)?
- [ ] **PCA visualization:** project 100+ fitur ke 2D — apakah karakter terkluster secara alami?
- [ ] **t-SNE visualization:** cluster map huruf-huruf — pola grouping (vokal vs konsonan, dsb)
- [ ] **Feature importance ranking:** mana 10 fitur paling diskriminatif?

#### 3.4 Notebook: `04_visualization_dashboard.ipynb` — Recreate Dashboard Charts
**File:** `data_science/notebooks/04_visualization_dashboard.ipynb`

- [ ] **Recreate semua chart Dashboard Guru** di notebook (sebagai source of truth):
  - [ ] Bar chart: latihan per hari (7 hari terakhir)
  - [ ] Metric cards: total siswa, total latihan, rata-rata akurasi
  - [ ] Top performers table
  - [ ] Activity feed timeline
- [ ] **Tambah chart yang belum ada di Dashboard** (candidate untuk Fase PSD-5):
  - [ ] Heatmap: akurasi per siswa × per huruf (matrix)
  - [ ] Radar chart: profil kemampuan siswa (motorik, ketelitian, kecepatan)
  - [ ] Trend line: perkembangan akurasi siswa dari waktu ke waktu
  - [ ] Pie chart: distribusi stars (⭐ vs ⭐⭐ vs ⭐⭐⭐)
  - [ ] Box plot: distribusi akurasi per kelas (TK-A vs TK-B)

#### 3.5 Notebook: `05_character_analysis.ipynb` — Analisis Kesulitan Karakter
**File:** `data_science/notebooks/05_character_analysis.ipynb`

- [ ] **Ranking kesulitan huruf:** sort by rata-rata akurasi (terendah = paling sulit)
- [ ] **Analisis per kategori:** Huruf Besar vs Kecil vs Angka — mana yang lebih sulit?
- [ ] **Common mistake pattern:** untuk huruf sulit, load sample gambar → analisis visual apa salahnya
  - Contoh: Huruf 'F' sering salah → apakah lupa garis bawah? Terlalu miring?
- [ ] **Stroke order analysis (jika data available):** urutan goresan benar atau tidak?
- [ ] **Rekomendasi:** urutan pengajaran berdasarkan data (dari mudah → sulit)

#### 3.6 Notebook: `06_student_profiling.ipynb` — Profiling Siswa
**File:** `data_science/notebooks/06_student_profiling.ipynb`

- [ ] **Student clustering:** group siswa berdasarkan pola performanya (pandai, rata-rata, butuh bantuan)
- [ ] **Individual learning curve:** plot akurasi siswa dari waktu ke waktu — ada progress?
- [ ] **At-risk detection:** siswa yang akurasinya stagnan/menurun → flag untuk guru
- [ ] **Learning speed:** berapa latihan sampai master sebuah huruf?
- [ ] **Personalized recommendation:** untuk setiap siswa, huruf apa yang harus dilatih lagi?

### Deliverable PSD-3:
> 6 Jupyter notebooks lengkap dengan visualisasi, analisis, dan kesimpulan. Setiap notebook bisa di-run independen. Temuan insight didokumentasikan dengan jelas.

---

## 📈 FASE PSD-4: Dashboard Analytics Enhancement (Data Storytelling)

**Goal:** Perkaya Dashboard Guru dengan visualisasi lanjutan berbasis temuan EDA

**Estimasi:** 3-4 jam

**Depends on:** PSD-3 (insight sudah ditemukan)

### Checklist PSD-4:

#### 4.1 New Endpoint: `/api/dashboard/heatmap`
**File:** `backend/main.py`

- [ ] **Return matrix data:** baris = siswa, kolom = huruf, nilai = avg akurasi
- [ ] Query: `SELECT AVG(accuracy) FROM student_progress JOIN lessons ON ... GROUP BY student_id, lesson_id`
- [ ] Handle siswa yang belum pernah mencoba suatu huruf (null → 0 atau '-')
- [ ] Cache result (query agak berat, update setiap 5 menit)

#### 4.2 New Endpoint: `/api/dashboard/student-trend/{student_id}`
**File:** `backend/main.py`

- [ ] **Return time series:** tanggal + rata-rata akurasi harian untuk 1 siswa
- [ ] Support window: 7 hari, 30 hari, semua waktu
- [ ] Hitung moving average (7-day smooth) untuk trend yang lebih jelas
- [ ] Detect trend: improving, stagnant, declining (simple linear regression slope)

#### 4.3 New Endpoint: `/api/dashboard/character-rankings`
**File:** `backend/main.py`

- [ ] **Ranking huruf dari mudah→sulit** berdasarkan rata-rata akurasi semua siswa
- [ ] Include: count attempts, avg accuracy, avg stars, avg time taken
- [ ] Group by category: huruf besar, huruf kecil, angka

#### 4.4 New Endpoint: `/api/dashboard/class-comparison`
**File:** `backend/main.py`

- [ ] **Perbandingan antar kelas** (TK-A vs TK-B): total latihan, avg akurasi, active students
- [ ] Support filter by date range

#### 4.5 Enhance `Dashboard.jsx` — New Chart Components
**File:** `frontend/src/components/Dashboard.jsx`

Tambahkan tab/section baru di Dashboard:

- [ ] **Heatmap Akurasi** (Recharts custom atau library heatmap):
  - X-axis: Huruf (A-Z, a-z, 0-9)
  - Y-axis: Nama Siswa
  - Color: merah (rendah) → kuning → hijau (tinggi)
  - Tooltip: "Budi Santoso — Huruf F: 45% (3 latihan)"
  
- [ ] **Trend Line Siswa** (setelah klik nama siswa):
  - Line chart: akurasi vs tanggal
  - Garis trend (linear regression)
  - Anotasi: "📈 Meningkat 12% dari minggu lalu!"
  
- [ ] **Ranking Kesulitan Huruf**:
  - Horizontal bar chart: huruf diurut dari avg akurasi terendah
  - Color code per kategori (besar=biru, kecil=hijau, angka=oranye)
  
- [ ] **Pie Chart Distribusi Stars**:
  - 3 bintang vs 2 bintang vs 1 bintang vs 0 bintang
  - Persentase + count
  
- [ ] **Perbandingan Kelas** (jika >1 kelas):
  - Grouped bar chart: TK-A vs TK-B per metrik

#### 4.6 Export Report Functionality
**File:** `frontend/src/components/Dashboard.jsx`

- [ ] **Tombol "Export Laporan"** → download JSON/CSV lengkap semua data
- [ ] **Tombol "Cetak"** → print-friendly layout dashboard
- [ ] **Opsional: PDF auto-report** menggunakan `jspdf` atau html2canvas

### Deliverable PSD-4:
> Dashboard Guru memiliki 5+ chart baru (heatmap, trend, ranking, pie, comparison). Semua endpoint API baru berfungsi. Guru bisa export data. Visualisasi menceritakan *story* tentang perkembangan siswa.

---

## 🔄 FASE PSD-5: Automated Pipeline & Reporting (Production PSD)

**Goal:** Jalankan seluruh pipeline PSD secara otomatis — dari collection → preprocessing → insight

**Estimasi:** 2-3 jam

**Depends on:** PSD-2, PSD-3, PSD-4

### Checklist PSD-5:

#### 5.1 Build `scripts/export_for_training.py` — Train/Test Splitter
**File baru:** `data_science/scripts/export_for_training.py`

```python
def train_test_split(features_csv: str, test_ratio=0.2, stratify=True) -> tuple:
    """
    Split dataset ke train (80%) dan test (20%).
    Stratified: menjaga proporsi per karakter sama di train & test.
    Output: train_features.csv, test_features.csv, train_labels.csv, test_labels.csv
    """
```

- [ ] Stratified split (proporsi karakter seimbang)
- [ ] Support multiple ratios: 80/20, 70/30, 60/40
- [ ] Save ke `datasets/exports/` dengan timestamp
- [ ] Generate split report (class distribution before/after split)

#### 5.2 Scheduler / Trigger System
**File:** `backend/main.py` atau script terpisah

- [ ] **Endpoint manual trigger:** `POST /api/psd/run-pipeline` → jalankan full pipeline
  - Step 1: Scan datasets/ → build manifest
  - Step 2: Preprocess batch (new files only)
  - Step 3: Extract features → update CSV
  - Step 4: Compute statistics → update report
- [ ] **Auto-trigger:** jalankan pipeline otomatis setelah N latihan baru (configurable)
- [ ] **Pipeline status endpoint:** `GET /api/psd/status` → last run, duration, records processed

#### 5.3 Auto-Report Generator
**File:** `data_science/scripts/generate_reports.py`

- [ ] **Generate weekly report** (JSON + HTML summary):
  - Total latihan minggu ini vs minggu lalu (% change)
  - Siswa paling improved + paling perlu perhatian
  - Huruf paling sulit minggu ini
  - Rekomendasi guru (data-driven)
- [ ] **Save ke `reports/weekly_YYYY-MM-DD.json`**
- [ ] **Display di Dashboard Guru** (section "Laporan Mingguan")

#### 5.4 Data Quality Monitor
**File:** `backend/main.py` (endpoint)

- [ ] **`GET /api/psd/data-quality`** → real-time data quality metrics:
  - Total samples in dataset
  - Samples per character (detect imbalance)
  - Last ingestion timestamp
  - Augmentation ratio (real vs augmented count)
  - Any anomalies detected

### Deliverable PSD-5:
> Pipeline PSD fully automated. Satu klik → data baru diproses → fitur diekstrak → statistik diupdate → report digenerate. Dashboard menunjukkan data quality real-time.

---

## 📋 RINGKASAN FASE PSD

| Fase | Nama | Estimasi | Key Deliverable | Output |
|------|------|----------|-----------------|--------|
| **PSD-1** | Data Collection | 2-3 jam | Metadata capture + organized dataset | `dataset_manifest.json`, folder structure |
| **PSD-2** | Preprocessing & Features | 3-4 jam | Clean data + 100+ fitur CSV | `all_features.csv`, augmented images |
| **PSD-3** | EDA Notebooks | 3-4 jam | 6 Jupyter notebooks dengan insight | `.ipynb` files + visualizations |
| **PSD-4** | Dashboard Enhancement | 3-4 jam | 5+ chart baru di Dashboard Guru | New endpoints + UI components |
| **PSD-5** | Automated Pipeline | 2-3 jam | Full auto pipeline + reporting | Scheduler, reports, quality monitor |
| **TOTAL** | | **~13-18 jam** | **Complete Data Science Workflow** | |

---

## 🔗 Dependency Graph PSD

```
PSD-1 (Collection) ─────────────────────────────┐
  ↓                                              │
PSD-2 (Preprocess + Features) ──────────────────┤
  ↓                                              │
PSD-3 (EDA Notebooks) ◄─────────────────────────┤
  ↓                                              │
PSD-4 (Dashboard Enhancement) ◄─────────────────┤
  ↓                                              │
PSD-5 (Automated Pipeline) ◄────────────────────┘
```

**Catatan:** PSD-1 bisa dimulai **sekarang** (hanya perlu enhance yang sudah ada). PSD-2 butuh data dari PSD-1. PSD-3 butuh fitur dari PSD-2. PSD-4 butuh insight dari PSD-3. PSD-5 butuh semuanya jadi.

---

## 🔧 Tech Stack PSD

| Layer | Teknologi | Use Case |
|-------|-----------|----------|
| **Image Processing** | OpenCV (cv2), NumPy, SciPy, scikit-image | Preprocessing, skeletonization, feature extraction |
| **Augmentation** | NumPy, OpenCV (geometric transforms), scipy | Data augmentation |
| **Feature Extraction** | OpenCV (Hu moments, contours), scikit-image (HOG, LBP) | 100+ fitur per sample |
| **Statistics** | Pandas, NumPy, SciPy | Descriptive stats, correlation, outlier detection |
| **Visualization (Notebook)** | Matplotlib, Seaborn, Plotly | EDA charts, heatmaps, interactive plots |
| **Visualization (Dashboard)** | Recharts (React) | Production charts di Dashboard Guru |
| **Dimensionality Reduction** | Scikit-learn (PCA, t-SNE) | Cluster visualization |
| **Data Format** | CSV, numpy (.npy), JSON | Feature storage, manifest, reports |
| **Notebook** | Jupyter Lab / VS Code extension | Interactive EDA |

---

## ⚠️ Risiko PSD & Mitigasi

| Risiko | Probabilitas | Dampak | Mitigasi |
|--------|-------------|--------|----------|
| Dataset terlalu kecil (<100 sample) | Tinggi | Analisis tidak signifikan | Agresif augmentation (10-15x), transfer learning |
| Imbalance parah (huruf populer vs tidak) | Sedang | Model bias | Stratified sampling, class weighting |
| Gambar corrupt/noise (siswa coret sembarang) | Tinggi | Fitur misleading | Quality filter: deteksi blank/spam images |
| Fitur redundant (high correlation) | Rendah | Dimensionality curse | PCA / feature selection sebelum modeling |
| Notebook lambat (banyak gambar) | Rendah | Productivity down | Resize preview thumbnails, cache di memory |

---

*Dokumen ini adalah panduan implementasi PSD untuk Sahabat Aksara. Setiap fase memiliki deliverable yang jelas dan bisa di-test secara independen. Integrasi dengan RPL (sudah jadi) dan PKB (spec terpisah) terjadi di layer data.*
