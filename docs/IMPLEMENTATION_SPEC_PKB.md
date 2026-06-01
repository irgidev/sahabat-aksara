# 🤖 Sahabat Aksara — Implementation Spec PKB

> **Mata Kuliah:** Pengantar Kecerdasan Buatan  
> **Fokus:** Pemodelan AI & Inferensi (Machine Learning, Neural Network, Pattern Recognition)  
> **Tanggal:** 2026-05-29  
> **Status:** Ready for Phase-by-Phase Implementation  
> **Integrasi:** Menerima data matang dari PSD (feature vectors, clean images) → Model AI → Prediksi/Klasifikasi → Kembali ke RPL (tampilkan hasil)

---

## 🎯 Ringkasan Eksekutif

Spec ini mendefinisikan **seluruh workflow AI/ML** di Sahabat Aksara:
1. **Baseline Model** — tingkatkan `pattern_matching.py` yang sudah ada (rule-based + CV)
2. **Machine Learning Klassik** — implementasi algoritma ML tradisional (kNN, SVM, Decision Tree, Naive Bayes, Random Forest)
3. **Neural Network / Deep Learning** — CNN sederhana untuk handwriting recognition
4. **Bayesian Network / Probabilistic** — model probabilistik untuk uncertainty quantification
5. **Ensemble & Hybrid** — gabungkan multiple model untuk akurasi maksimal
6. **Inference Engine** — serve model lewat FastAPI untuk prediksi real-time
7. **Model Evaluation & Comparison** — benchmark semua model secara adil

**Alur PKB:**
```
Data from PSD                AI Models                 Prediction Output
┌──────────────┐           ┌──────────────┐         ┌──────────────┐
│ Feature CSV  │ ──►      │ TRAIN        │ ──►     │ Accuracy     │
│ (100+ fitur) │  train    │ - kNN        │ predict│ Score (0-100)│
│ Clean PNG    │ ──►      │ - SVM        │ ──►     │ Stars (0-3⭐) │
│ 64×64 images │  infer    │ - CNN        │ ──→     │ Feedback     │
│              │           │ - Bayes      │         │ text ("Hebat!")│
└──────────────┘           └──────────────┘         └──────────────┘
       ↑                           ↑                         ↑
       │ PSD                   Training Loop               │ RPL
   Processed Data            ai_core/models/          Canvas + Dashboard
```

---

## 🏗️ Arsitektur AI/ML PKB

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PKB AI/MLENGINE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 0: DATA INPUT (dari PSD)                                             │
│  ├── all_features.csv               ← 100+ fitur per sample                  │
│  ├── datasets/processed/*.png       ← Clean 64×64 images                    │
│  ├── datasets/augmented/*.png       ← Augmented variants                     │
│  └── exports/train.csv, test.csv    ← Train/test split                       │
│                                                                              │
│  LAYER 1: CLASSICAL ML (Scikit-Learn)                                       │
│  ├── models/classical/                                                        │
│  │   ├── knn_model.pkl              ← k-Nearest Neighbors (distance-based)   │
│  │   ├── svm_model.pkl              ← Support Vector Machine (RBF kernel)    │
│  │   ├── nb_model.pkl               ← Naive Bayes (Gaussian)                │
│  │   ├── dt_model.pkl               ← Decision Tree (interpretable!)         │
│  │   ├── rf_model.pkl               ← Random Forest (ensemble trees)        │
│  │   └── lr_model.pkl               ← Logistic Regression (baseline linear) │
│  │                                                                         │
│  ├── Algoritma yang WAJIB (sesuai silabus PKB):                            │
│  │   ✅ Naive Bayes                    ← Probabilistic classifier            │
│  │   ✅ kNN                            ← Instance-based learning             │
│  │   ✅ Decision Tree                  ← Rule-based, interpretable           │
│  │   ✅ Neural Network / CNN           ← Deep learning untuk image           │
│  │   ⚠️ Bayesian Network (optional)    ← Probabilistic graphical model      │
│  │                                                                         │
│  └── Training:                                                            │
│      ├── train_classical.py             ← Train semua classical models      │
│      ├── evaluate_models.py             ← Benchmark & compare accuracy       │
│      └── cross_validation.py            ← K-Fold CV untuk validasi reliable  │
│                                                                              │
│  LAYER 2: DEEP LEARNING (Neural Network)                                    │
│  ├── models/deep/                                                             │
│  │   ├── cnn_simple/                                                           │
│  │   │   ├── model_architecture.json   ← Definisi arsitektur                 │
│  │   │   ├── weights.h5                ← Trained weights (Keras/TensorFlow)  │
│  │   │   └── training_history.json     ← Loss/accuracy per epoch              │
│  │   │                                                                     │
│  │   └── cnn_transfer/                                                         │
│  │       ├── base_model=MobileNetV2    ← Transfer learning dari ImageNet    │
│  │       ├── weights_finetuned.h5      ← Weights setelah fine-tuning         │
│  │       └── training_log.json                                          │
│  │                                                                         │
│  ├── Arsitektur CNN:                                                          │
│  │   Input(64,64,1) → Conv2D(32) → ReLU → MaxPool →                        │
│  │   Conv2D(64) → ReLU → MaxPool → Flatten → Dense(128) → Dropout →         │
│  │   Dense(62) [26 besar + 26 kecil + 10 angka] → Softmax                   │
│  │                                                                         │
│  └── Training:                                                              │
│      ├── train_cnn.py                  ← Train CNN from scratch              │
│      ├── train_transfer.py             ← Transfer learning pipeline         │
│      └── data_generator.py             ← Image data generator (augment on-fly)│
│                                                                              │
│  LAYER 3: ENSEMBLE & HYBRID                                                  │
│  ├── ensemble/                                                               │
│  │   ├── voting_classifier.pkl         ← Hard/Soft vote dari classical       │
│  │   ├── stacking_ensemble.pkl         ← Meta-learner di atas base models    │
│  │   └── hybrid_config.json            ← Config: weight per model             │
│  │                                                                         │
│  └── hybrid_engine.py                  ← Gabung CV (PSD) + ML (PKB) scores   │
│                                                                              │
│  LAYER 4: INFERENCE ENGINE (Production)                                     │
│  ├── inference/                                                               │
│  │   ├── model_registry.json           ← Daftar model teravailable + version │
│  │   ├── default_model = "hybrid_v1"  ← Model aktif untuk production        │
│  │   └── cache/                        ← Cached predictions (LRU)            │
│  │                                                                         │
│  └── API Integration:                                                      │
│      ├── main.py → /api/evaluate              ← Ganti/extend dengan ML       │
│      ├── main.py → /api/evaluate-ml           ← Endpoint khusus ML          │
│      ├── main.py → /api/models/status          ← Status & benchmark model   │
│      └── main.py → /api/models/compare         ← Bandingkan output model    │
│                                                                              │
│  LAYER 5: EVALUATION & EXPLAINABILITY                                      │
│  ├── evaluation/                                                             │
│  │   ├── benchmark_results.json         ← Akurasi semua model side-by-side  │
│  │   ├── confusion_matrix_*.png         ← Confusion matrix per model        │
│  │   ├── classification_report.json     ← Precision, Recall, F1 per class  │
│  │   └── misclassified_samples/         ← Simpel salah klasifikasi (analisis)│
│  │                                                                         │
│  └── explainability.py                 ← LIME/SHAP explanation (why this?)  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Target Struktur Folder PKB

```
sahabat-aksara/
├── ai_core/                              ← AI CORE MODULE (INTI PKB)
│   ├── pattern_matching.py               ← SUDAH ADA: Rule-based CV engine v3
│   ├──                                   ← (upgrade, jangan hapus!)
│   ├── models/                           ← TRAINED MODEL FILES
│   │   ├── classical/                    ← Scikit-learn pickle files
│   │   │   ├── knn.pkl
│   │   │   ├── svm.pkl
│   │   │   ├── naive_bayes.pkl
│   │   │   ├── decision_tree.pkl
│   │   │   ├── random_forest.pkl
│   │   │   └── logistic_regression.pkl
│   │   │
│   │   ├── deep/                         ← Keras/TensorFlow/PyTorch models
│   │   │   ├── cnn_simple/
│   │   │   │   ├── architecture.json
│   │   │   │   ├── weights.h5
│   │   │   │   └── history.json
│   │   │   └── cnn_transfer/
│   │   │       ├── weights.h5
│   │   │       └── history.json
│   │   │
│   │   └── ensemble/
│   │       ├── voting_classifier.pkl
│   │       ├── stacking_meta.pkl
│   │       └── hybrid_weights.json
│   │
│   ├── training/                          ← TRAINING SCRIPTS
│   │   ├── train_classical.py            ← Train semua classical ML models
│   │   ├── train_cnn.py                  ← Train CNN from scratch
│   │   ├── train_transfer_learning.py    ← Transfer learning (MobileNet/EfficientNet)
│   │   ├── train_bayesian_network.py     ← Bayesian Network (jika diimplementasi)
│   │   ├── train_ensemble.py             ← Gabung model jadi ensemble
│   │   ├── evaluate_all_models.py        ← Benchmark lengkap semua model
│   │   ├── cross_validate.py             ← K-Fold Cross Validation
│   │   └── hyperparameter_search.py      ← Grid/Random search optimal params
│   │
│   ├── inference/                         ← INFERENCE ENGINE
│   │   ├── predictor.py                  ← Unified prediction interface
│   │   ├── hybrid_engine.py              ← Combine CV + ML scores
│   │   ├── model_registry.json           ← Available models catalog
│   │   └── model_loader.py               ← Load model from disk safely
│   │
│   └── evaluation/                        ← EVALUATION & ANALYSIS
│       ├── benchmark.py                   ← Run full benchmark suite
│       ├── generate_confusion_matrix.py   ← Visualisasi confusion matrix
│       ├── classification_report.py      ← Per-class precision/recall/F1
│       ├── error_analysis.py              ← Analisis sample salah klasifikasi
│       └── explain_predictions.py         ← LIME/SHAP explanations
│
├── data_science/datasets/exports/         ← DATA DARI PSD (INPUT)
│   ├── train_features.csv
│   ├── test_features.csv
│   ├── train_labels.csv
│   └── test_labels.csv
│
└── backend/main.py                        ← INTEGRATION: API endpoints
```

---

## 🚞 FASE-FASE IMPLEMENTASI PKB

---

## ✅ FASE PKB-1: Baseline Enhancement (Pattern Matching v4)

**Goal:** Tingkatkan engine AI yang sudah ada (`pattern_matching.py`) menjadi lebih robust dan akurat sebagai **baseline**

**Estimasi:** 2-3 jam

**Depends on:** RPL Fase 4 (evaluasi sudah dynamic multi-huruf)

### Checklist PKB-1:

#### 1.1 Refactor `pattern_matching.py` → Modular Architecture
**File:** `ai_core/pattern_matching.py`

Saat ini semua logic di 1 file ~500 baris. **Refactor menjadi modular:**

```python
# === STRUKTUR BARU (modular) ===

# ai_core/pattern_matching.py (tetap, sebagai facade)
from .preprocessor import preprocess_image
from .template_engine import generate_template
from .scorers import (
    SkeletonScorer,
    DistanceFieldScorer,
    StructuralScorer,
    CompletenessScorer,
    StrokeCountScorer,
)
from .ensemble import WeightedEnsemble

class HandwritingEvaluator:
    """Unified evaluation interface"""
    def __init__(self, config=None):
        self.scorers = [...]
        self.ensemble = WeightedEnsemble(weights=config)
    
    def evaluate(self, image_path, char_target) -> EvaluationResult:
        processed = preprocess_image(image_path)
        template = generate_template(char_target)
        scores = {scorer.name: scorer.score(processed, template) for scorer in self.scorers}
        final_score = self.ensemble.combine(scores)
        return EvaluationResult(score=final_score, breakdown=scores)
```

- [ ] Extract `preprocessor.py` — preprocessing functions (to_binary, skeletonize, normalize)
- [ ] Extract `template_engine.py` — template generation (create_template, create_handwriting_template)
- [ ] Extract `scorers.py` — semua scoring function (skeleton, distance, structural, completeness, stroke)
- [ ] Extract `ensemble.py` — weighted combination logic
- [ ] Keep `pattern_matching.py` as **facade/public API** (backward compatible!)

#### 1.2 Add New Scoring Method: Histogram of Oriented Gradients (HOG)
**File baru:** `ai_core/scorers.py` atau `ai_core/hog_scorer.py`

```python
class HOGScorer:
    """
    HOG-based comparison: bandingkan HOG descriptor user vs template.
    HOG menangkap edge gradient direction — bagus untuk shape matching.
    Menggunakan cv2.HOGDescriptor() built-in.
    """
    def score(user_img, template_img) -> float:
        hog = cv2.HOGDescriptor(_winSize=(64, 64), _blockSize=(16, 16),
                                _blockStride=(8, 8), _cellSize=(8, 8),
                                _nbins=9)
        user_desc = hog.compute(user_img)
        template_desc = hog.compute(template_img)
        # Cosine similarity antara HOG descriptors
        similarity = cosine_similarity(user_desc, template_desc)
        return similarity * 100  # convert to 0-100
```

- [ ] Implementasi HOG scorer
- [ ] Integrate ke ensemble (tambahkan bobot, rebalance existing)

#### 1.3 Add New Scoring Method: Structural Similarity (SSIM)
**File baru:** `ai_core/scorers.py`

```python
class SSIMScorer:
    """
    Structural Similarity Index — membandingkan struktur visual,
    luminance, dan contrast. Lebih "human-like" daripada pixel accuracy.
    """
    def score(user_img, template_img) -> float:
        from skimage.metrics import structural_similarity as ssim
        score = ssim(user_img, template_img, win_size=7, data_range=255)
        return score * 100
```

- [ ] Implementasi SSIM scorer (membutuhkan `scikit-image`)
- [ ] Integrate ke ensemble

#### 1.4 Tuning Ensemble Weights (Data-Driven)
**File:** `ai_core/ensemble.py`

Saat ini bobot hardcoded: 35% skeleton, 25% distance, 20% completeness, 15% structural, 5% stroke.

- [ ] **Tambahkan HOG scorer** (+ SSIM jika memungkinkan)
- [ ] **Rebalance weights** dengan 7 scorer:
  ```
  v3 (current):  S=35%, D=25%, C=20%, St=15%, Sc=5%
  v4 (new):      S=25%, D=15%, C=15%, St=15%, Sc=5%, HOG=15%, SSIM=10%
  ```
- [ ] **Config-driven weights:** load dari JSON file, mudah eksperimen
- [ ] **Per-character tuning:** huruf tertentu mungkin butuh bobot berbeda

#### 1.5 Add Confidence Score & Explanation
**File:** `ai_core/pattern_matching.py`

- [ ] **Return confidence interval**: bukan cuma skor 78, tapi "78 ± 5" (berapa yakin?)
- [ ] **Return explanation breakdown**: 
  ```json
  {
    "score": 78,
    "confidence": "medium",
    "breakdown": {
      "shape_match": "Baik — bentuk dasar cocok (85%)",
      "placement": "Cukup — posisi sedikit miring (-5pts)",
      "completeness": "Bagus — hampir semua bagian terisi (82%)",
      "structure": "Kurang — crossbar 'A' kurang jelas (-8pts)",
      "tip": "Coba buat garis tengah huruf A lebih tebal ya! ✏️"
    }
  }
  ```
- [ ] **Generate kid-friendly feedback text** dalam Bahasa Indonesia

### Deliverable PKB-1:
> `pattern_matching.py` refaktor jadi modular (5 sub-module). 2 scorer baru (HOG, SSIM). Bobot ensemble di-tune. Output sekarang include confidence + penjelasan + tip untuk anak.

---

## 🧠 FASE PKB-2: Classical Machine Learning Models

**Goal:** Train model ML klassik (kNN, Naive Bayes, SVM, Decision Tree, RF) menggunakan fitur dari PSD

**Estimasi:** 4-5 jam

**Depends on:** PSD-2 (fitur sudah diekstrak ke CSV)

### Checklist PKB-2:

#### 2.1 Setup: `training/train_classical.py`
**File baru:** `ai_core/training/train_classical.py`

```python
"""
Train 6 classical ML models untuk handwriting classification.
Input: feature CSV dari PSD (all_features.csv)
Output: trained model files (.pkl) + evaluation metrics
"""

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

MODELS = {
    'knn': {
        'model': KNeighborsClassifier(),
        'param_grid': {'n_neighbors': [3, 5, 7, 11], 'weights': ['uniform', 'distance']},
        'description': 'k-Nearest Neighbors — klasifikasi berdasarkan jarak ke tetangga terdekat'
    },
    'naive_bayes': {
        'model': GaussianNB(),
        'param_grid': {'var_smoothing': [1e-9, 1e-7, 1e-5]},
        'description': 'Naive Bayes — probabilitas kondisional (P(class|features))'
    },
    'svm': {
        'model': SVC(kernel='rbf', probability=True),
        'param_grid': {'C': [0.1, 1, 10], 'gamma': ['scale', 'auto']},
        'description': 'Support Vector Machine — hyperplane separator di high-dimensional space'
    },
    'decision_tree': {
        'model': DecisionTreeClassifier(max_depth=10, random_state=42),
        'param_grid': {'max_depth': [5, 10, 15, None], 'criterion': ['gini', 'entropy']},
        'description': 'Decision Tree — aturan if-else otomatis (INTERPRETABLE!)'
    },
    'random_forest': {
        'model': RandomForestClassifier(n_estimators=100, random_state=42),
        'param_grid': {'n_estimators': [50, 100, 200], 'max_depth': [5, 10, None]},
        'description': 'Random Forest — ensemble dari banyak decision tree'
    },
    'logistic_regression': {
        'model': LogisticRegression(max_iter=1000, multi_class='multinomial'),
        'param_grid': {'C': [0.1, 1, 10]},
        'description': 'Logistic Regression — baseline linear classifier'
    },
}
```

- [ ] Implementasi training loop untuk 6 model
- [ ] **StandardScaler pipeline** (penting! fitur punya unit berbeda: pixel count vs Hu moments vs histogram)
- [ ] **GridSearchCV** untuk hyperparameter tuning per model
- [ ] **Stratified K-Fold CV** (k=5) untuk estimasi akurasi yang reliable
- [ ] Save best model per algorithm ke `ai_core/models/classical/{name}.pkl`
- [ ] Save training log (params, CV score, train time)

#### 2.2 Setup: `training/evaluate_all_models.py`
**File baru:** `ai_core/training/evaluate_all_models.py`

```python
def evaluate_models(X_test, y_test, models_dict) -> dict:
    """
    Return comprehensive metrics per model:
    - accuracy, precision (macro), recall (macro), f1 (macro)
    - inference time (ms) — penting untuk real-time!
    - confusion matrix
    - top-3 confused class pairs (mana yang sering salah?)
    """

def generate_comparison_table(results: dict) -> str:
    """Pretty table: Model | Accuracy | Precision | Recall | F1 | Time(ms)"""

def plot_accuracy_bar_chart(results: dict):
    """Bar chart perbandingan akurasi semua model"""

def find_best_model(results: dict) -> tuple:
    """Return (model_name, metrics) berdasarkan F1-weighted score"""
```

- [ ] Evaluasi semua model di test set (unseen data)
- [ ] Generate **comparison table** + **bar chart**
- [ ] Hitung **inference time** per model (krucial untuk real-time `/api/evaluate`)
- [ ] Generate **confusion matrix** per model (simpan sebagai PNG)
- [ ] Identifikasi **confused pairs** (misal: 'O' sering dikira '0', 'I' dikira 'l')

#### 2.3 Setup: `training/cross_validate.py`
**File baru:** `ai_core/training/cross_validate.py`

- [ ] **Stratified K-Fold** (k=5, k=10) untuk setiap model
- [ ] Report: mean accuracy ± std per fold
- [ ] Deteksi **overfitting**: train_acc >> val_acc?
- [ ] Learning curve plotting: akurasi vs training set size

#### 2.4 Naive Bayes Deep-Dive (Silabus Wajib PKB)
**File:** `ai_core/training/train_bayesian.py` (opsional, bonus)

Karena Naive Bayes adalah **algoritma wajib** di silabus PKB, kita berikan treatment khusus:

```python
class HandwritingNaiveBayes:
    """
    Naive Bayes untuk handwriting recognition.
    
    Penjelasan untuk dokumen/laporan:
    ─────────────────────────────────────
    P(c|f₁,f₂,...,fₙ) ∝ P(c) × ∏ᵢ P(fᵢ|c)
    
    Dimana:
    - c = class (huruf: A-Z, a-z, 0-9 → 62 class)
    - fᵢ = fitur ke-i (dari 100+ fitur PSD)
    - P(c) = prior probability (seberapa umum huruf ini muncul di dataset)
    - P(fᵢ|c) = likelihood (distribusi Gaussian per fitur per class)
    
    "Naive" = asumsi independen antar-fitur (tidak benar tapi bekerja baik!)
    
    Keuntungan untuk Sahabat Aksara:
    - Sangat cepat (training O(N×D), inference O(D))
    - Handle missing values secara natural
    - Probabilistic output → bisa kasih confidence score
    - Mudah dijelaskan ke non-technical user (guru!)
    """
    
    def fit(self, X, y): ...
    def predict(self, X): ...
    def predict_proba(self, X): ...  # Return P(class|x) untuk semua class
```

- [ ] Implementasi custom Naive Bayes dengan penjelasan matematis di docstring
- [ ] Bandingkan `GaussianNB` (sklearn) vs manual implementation
- [ ] Visualisasi **prior vs posterior** untuk 1 sample (edukatif!)

#### 2.5 Decision Tree Visualization (Interpretable AI)
**File:** `ai_core/training/visualize_tree.py`

Decision Tree adalah satu-satunya model yang **bisa dijelaskan secara visual** — ini nilai tambah besar untuk edtech!

- [ ] Export decision tree ke `tree_structure.png` (maksimal depth=4 agar readable)
- [ ] Export rules ke text: `"IF hu_1 < 0.15 AND pixel_count > 200 AND aspect_ratio < 1.2 → Class='A'"`
- [ ] Tampilkan **feature importance** bar chart: fitur mana yang paling menentukan?

### Deliverable PKB-2:
> 6 model classical ML tertrain (.pkl). Benchmark lengkap (akurasi, waktu, confusion matrix). Decision Tree tervisualisasi. Naive Bayes didokumentasikan dengan rumus probabilistic. Best model dipilih berdasarkan F1-score + inference time.

---

## 🔥 FASE PKB-3: Neural Network / Deep Learning (CNN)

**Goal:** Implementasi CNN untuk handwriting recognition — state-of-the-art approach untuk image classification

**Estimasi:** 4-6 jam

**Depends on:** PSD-2 (clean images available), PKB-2 (baseline ML sudah ada untuk comparison)

### Checklist PKB-3:

#### 3.1 Architecture Design: `training/train_cnn.py`
**File baru:** `ai_core/training/train_cnn.py`

```python
"""
CNN Architecture untuk Sahabat Aksara — Handwriting Character Recognition

Arsitektur (custom, lightweight untuk CPU inference):

Model: "SahabatNet-v1"
================================================================
Layer (type)        Output Shape    Param #   Description
================================================================
Input               (64, 64, 1)     0         Grayscale 64×64
Conv2D(32, 3×3)     (62, 62, 32)    320       32 filter, 3×3 kernel
BatchNorm2D         (62, 62, 32)    128       Normalisasi (stabil training)
ReLU                (62, 62, 32)    0         Activation
MaxPool2D(2×2)      (31, 31, 32)    0         Downsample ½
Dropout(0.25)       (31, 31, 32)    0         Regularisasi

Conv2D(64, 3×3)     (29, 29, 64)    18496     64 filter
BatchNorm2D         (29, 29, 64)    256
ReLU                (29, 29, 64)    0
MaxPool2D(2×2)      (14, 14, 64)    0
Dropout(0.25)       (14, 14, 64)    0

Conv2D(128, 3×3)    (12, 12, 128)   73888     128 filter
BatchNorm2D         (12, 12, 128)   512
ReLU                (12, 12, 128)   0
MaxPool2D(2×2)      (6, 6, 128)     0
Dropout(0.25)       (6, 6, 128)     0

Flatten             (4608)          0
Dense(256)          (256)           1179808   Fully connected
BatchNorm1D         (256)           1024
ReLU                (256)           0
Dropout(0.5)       (256)           0

Dense(62)           (62)            15914     OUTPUT: 62 classes
Softmax             (62)            0
================================================================
Total params: ~1.29M (lightweight! Cocok untuk CPU inference)
================================================================
"""

# Alternatif arsitektur (jika dataset sangat kecil <500 samples):
# "SahabatNet-Tiny" — hanya 2 conv layers, ~150K params
```

- [ ] Implementasi CNN architecture (Keras/TF atau PyTorch)
- [ ] **Data generator** dengan on-the-fly augmentation (rotation, shift, zoom, shear)
- [ ] **Training loop** dengan callbacks:
  - [ ] Early stopping (patience=5 epochs)
  - [ ] Model checkpoint (save best val_accuracy)
  - [ ] ReduceLROnPlateau (reduce LR kalau stuck)
  - [ ] CSVLogger (log loss/acc per epoch)
- [ ] Train untuk max 100 epochs
- [ ] Plot **training curves** (loss & accuracy vs epoch)

#### 3.2 Transfer Learning: `training/train_transfer_learning.py`
**File baru:** `ai_core/training/train_transfer_learning.py`

Kalau dataset custom terlalu kecil (<1000 samples), gunakan transfer learning:

```python
"""
Transfer Learning: MobileNetV2 → Fine-tune untuk handwriting

Base model: MobileNetV2 (pre-trained on ImageNet)
- Hanya 3.4M params (sangat lightweight)
- Depthwise separable convolutions (efisien)
- Input: 96×96×3 (resize our 64×64→96×96, grayscale→3 channel)

Strategy:
1. Load MobileNetV2 tanpa top layer (include_top=False)
2. Freeze base layer (trainable=False)
3. Tambah custom head: GlobalAvgPool → Dense(256) → Dropout → Dense(62)
4. Train head saja (10 epochs, LR=1e-3)
5. Unfreeze last 20% base layers
6. Fine-tune seluruh network (10 epochs, LR=1e-5)
"""
```

- [ ] Implementasi transfer learning pipeline
- [ ] Compare: CNN from scratch vs Transfer Learning (mana yang lebih baik?)

#### 3.3 Data Generator: `training/data_generator.py`
**File baru:** `ai_core/training/data_generator.py`

```python
class HandwritingDataGenerator(tf.keras.utils.Sequence):
    """
    Custom data generator yang:
    - Load gambar dari folder on-the-fly (tidak muat semua di RAM)
    - Apply augmentasi random setiap epoch
    - Support train/val/test split
    - Yield batches of (image_array, one_hot_label)
    """
```

- [ ] Implementasi custom data generator
- [ ] Augmentation options: rotation (±15°), width_shift, height_shift, zoom, shear, noise
- [ ] Label encoding: character → integer index (A=0, B=1, ..., Z=25, a=26, ..., z=51, 0=52, ..., 9=61)

#### 3.4 CNN Evaluation & Analysis
**File:** `ai_core/evaluation/benchmark.py` (extend)

- [ ] **Confusion Matrix CNN** (62×62 — large, but informative)
- [ ] **Top-K Accuracy**: top-1, top-3, top-5 (kalau salah tebak, apakah masuk kandidat atas?)
- [ ] **Per-class accuracy**: huruf mana paling mudah/sulit untuk CNN?
- [ ] **Failure case analysis**: tampilkan 20 gambar yang paling salah prediksi CNN + analisis kenapa
- [ ] **Inference time benchmark**: ms per image di CPU (target: <100ms)

### Deliverable PKB-3:
> CNN tertrain (`weights.h5`) dengan akurasi terdokumentasi. Training curves terplot. Confusion matrix 62×62. Comparison: CNN vs Classical ML vs Baseline CV. Inference time <100ms/image di CPU.

---

## 🎲 FASE PKB-4: Bayesian Network & Probabilistic Methods (Bonus Silabus)

**Goal:** Implementasi model probabilistic — Bayesian Network untuk uncertainty quantification

**Estimasi:** 3-4 jam

**Depends on:** PKB-2 (classical ML baseline ada)

### Checklist PKB-4:

#### 4.1 Bayesian Network for Character Recognition
**File baru:** `ai_core/training/train_bayesian_network.py`

```python
"""
Bayesian Network untuk Handwriting Evaluation

Berbeda dengan klasifikasi biasa (hard label: "ini huruf A"),
Bayesian Network memberikan DISTRIBUTION probabilitas:

P(Akurasi | Fitur) = distribusi, bukan angka tunggal

Network Structure:
                  ┌─────────────┐
                  │  Char Target │ (Evidence: guru pilih "A")
                  └──────┬──────┘
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Pixel Count│ │Aspect Ratio│ │Hu Moment 1 │
    └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
          │               │               │
          ▼               ▼               ▼
    ┌─────────────────────────────────────┐
    │         ACCURACY SCORE              │  ← Query target
    │    (discretized: Low/Med/High)      │
    └─────────────────────────────────────┘

Menggunakan:
- pgmpy library (Python library untuk Bayesian Networks)
- Parameter learning dari data (Maximum Likelihood Estimation)
- Inference: Variable Elimination / Belief Propagation
"""

# Alternative (lebih sederhana, tanpa pgmpy):
class BayesianScorer:
    """
    Pendekatan Bayesian sederhana tanpa full BN library:
    
    P(score | features) ∝ P(features | score) × P(score)
    
    - P(score) = Prior dari historical data (histogram akurasi)
    - P(features | score) = Gaussian per fitur per score bucket
    - Posterior = normalisasi produk likelihood × prior
    
    Output: P(Low), P(Medium), P(High) + expected value
    """
```

- [ ] Implementasi Bayesian Scorer (simple approach: Gaussian per feature per score bucket)
- [ ] Atau implementasi full Bayesian Network dengan `pgmpy` (jika tersedia)
- [ ] **Uncertainty quantification**: return confidence interval, bukan point estimate
- [ ] **Prior update**: update prior saat data baru masuk (online learning style)

#### 4.2 Probability Calibration
**File:** `ai_core/training/calibrate_models.py`

Banyak model ML mengeluarkan probabilitas yang **terkalibrasi buruk** (model mengatakan 90% confident tapi ternyata hanya 70% akurat).

- [ ] **Calibration curve** (reliability diagram) per model
- [ ] **Isotonic regression** atau **Platt scaling** untuk kalibrasi ulang
- [ ] **Brier score** evaluasi kualitas probabilitas
- [ ] Pastikan model yang bilang "85% yakin" memang benar ~85% of the time

#### 4.3 Bayesian Model Comparison
**File:** `ai_core/evaluation/compare_bayesian.py`

- [ ] **Bayes Factor** untuk membandingkan 2 model (mana yang lebih supported oleh data?)
- [ ] **Posterior predictive check**: apakah model bisa generate data mirip dengan real?
- [ ] **MAP (Maximum A Posteriori)** estimation sebagai alternatif MLE

### Deliverable PKB-4:
> Bayesian Scorer yang mengeluarkan distribusi probabilitas (bukan point estimate). Kalibration curve menunjukkan reliability model. Dokumentasi matematis untuk laporan PKB.

---

## 🔄 FASE PKB-5: Ensemble, Hybrid Engine & Production Integration

**Goal:** Gabungkan semua model jadi 1 super-engine, integrate ke FastAPI production

**Estimasi:** 4-5 jam

**Depends on:** PKB-1, PKB-2, PKB-3 (semua model sudah terlatih)

### Checklist PKB-5:

#### 5.1 Ensemble Methods: `training/train_ensemble.py`
**File baru:** `ai_core/training/train_ensemble.py`

```python
"""
Ensemble Strategies:

1. VOTING ENSEMBLE (Hard Vote):
   Setiap model prediksi class → majority vote
   Pro: Robust, mudah
   Kontra: Tidak mempertimbangkan confidence

2. VOTING ENSEMBLE (Soft Vote):
   Setiap model keluarkan P(class|x) → rata-rata prob → argmax
   Pro: Lebih akurat, pakai confidence info
   Kontra: Semua model harus support predict_proba()

3. STACKING:
   - Base models: kNN, SVM, RF, CNN (prediksi mereka jadi fitur baru)
   - Meta-learner: Logistic Regression (belajar kombinasi optimal)
   - Pro: Bisa capture interaction antar-model
   Kontra: Lebih kompleks, risk overfitting

4. WEIGHTED ENSEMBLE (Custom):
   - Bobot manual berdasarkan benchmark results
   - Contoh: CNN=40%, RF=20%, SVM=15%, kNN=10%, CV-Baseline=15%
   - Pro: Kontrol penuh, interpretable
   Kontra: Subjektif, perlu tuning manual
"""
```

- [ ] Implementasi **Soft Voting Classifier** (sklearn `VotingClassifier`)
- [ ] Implementasi **Stacking Ensemble** (meta-learner di atas base models)
- [ ] Implementasi **Custom Weighted Ensemble** (config-driven weights)
- [ ] Benchmark ensemble vs best single model

#### 5.2 Hybrid Engine: `inference/hybrid_engine.py` ⭐
**File baru:** `ai_core/inference/hybrid_engine.py`

Ini adalah **mahakarya integrasi PKB** — menggabungkan pendekatan Computer Vision (pattern_matching.py) dengan Machine Learning (trained models):

```python
class HybridHandwritingEngine:
    """
    HYBRID ENGINE v1 — Gabungan terbaik dari semua dunia
    
    ┌─────────────────────────────────────────────────────┐
    │              HYBRID SCORING PIPELINE               │
    ├─────────────────────────────────────────────────────┤
    │                                                      │
    │  Input: image_path (64×64 PNG) + char_target        │
    │           ↓                                         │
    │  ┌──────────────────────────────────────────┐       │
    │  │  BRANCH A: Computer Vision (pattern_match)│       │
    │  │  - Skeleton overlap score                 │       │
    │  │  - Distance field score                   │       │
    │  │  - Structural analysis                   │       │
    │  │  - HOG comparison                       │       │
    │  │  → Sub-total A: cv_score (0-100)         │       │
    │  └───────────────────┬──────────────────────┘       │
    │                      │                               │
    │  ┌───────────────────▼──────────────────────┐       │
    │  │  BRANCH B: Classical ML                   │       │
    │  │  - Load features from image              │       │
    │  │  - Run SVM/kNN/RF prediction             │       │
    │  │  → Sub-total B: ml_score (0-100)         │       │
    │  └───────────────────┬──────────────────────┘       │
    │                      │                               │
    │  ┌───────────────────▼──────────────────────┐       │
    │  │  BRANCH C: Deep Learning (CNN)           │       │
    │  │  - Run image through CNN                  │       │
    │  │  - Get P(correct_class) × 100            │       │
    │  │  → Sub-total C: dl_score (0-100)         │       │
    │  └───────────────────┬──────────────────────┘       │
    │                      │                               │
    │  ┌───────────────────▼──────────────────────┐       │
    │  │  ENSEMBLE LAYER                          │       │
    │  │  final = A×0.30 + B×0.35 + C×0.35        │       │
    │  │  (tunable via hybrid_weights.json)        │       │
    │  └───────────────────┬──────────────────────┘       │
    │                      │                               │
    │  ┌───────────────────▼──────────────────────┐       │
    │  │  OUTPUT                                  │       │
    │  │  {                                       │       │
    │  │    score: 82,                             │       │
    │  │    stars: 3,                              │       │
    │  │    confidence: "high",                    │       │
    │  │    breakdown: {cv:78, ml:85, dl:83},     │       │
    │  │    prediction: "matches target A ✓",     │       │
    │  │    tip: "Bagus! Terus pertahankan!"       │       │
    │  │  }                                       │       │
    │  └──────────────────────────────────────────┘       │
    │                                                      │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config_path="hybrid_weights.json"):
        self.cv_engine = HandwritingEvaluator()       # Branch A
        self.ml_models = ModelLoader.load_all()       # Branch B
        self.cnn_model = load_cnn_weights()           # Branch C
        self.weights = load_json(config_path)         # Ensemble weights
    
    def evaluate(self, image_path, char_target) -> HybridResult:
        # Run 3 branches → ensemble → output
        ...
```

- [ ] Implementasi HybridEngine dengan 3 branch (CV + ML + DL)
- [ ] Configurable weights via JSON
- [ ] Graceful degradation: kalau 1 model gagal, 2 lain tetap jalan
- [ ] Comprehensive output: score, stars, confidence, breakdown, tip

#### 5.3 Unified Predictor API: `inference/predictor.py`
**File baru:** `ai_core/inference/predictor.py`

```python
class UnifiedPredictor:
    """
    Single entry point untuk semua prediksi.
    Dipakai oleh FastAPI endpoint.
    """
    
    def __init__(self, mode="hybrid"):
        # mode: "baseline" | "ml" | "cnn" | "hybrid"
        
    def predict(self, image_path: str, char_target: str) -> PredictionResult:
        """Main prediction method"""
        
    def predict_batch(self, image_paths: list, char_targets: list) -> list:
        """Batch prediction (for analytics/re-scoring)"""
        
    def get_model_info(self) -> dict:
        """Return loaded model metadata"""
```

- [ ] Implementasi unified predictor interface
- [ ] Support multiple modes (switchable tanpa ubah code)
- [ ] Model caching (load once, predict many)
- [ ] Error handling: model file corrupt / missing → fallback to baseline

#### 5.4 Integrate to FastAPI: Update `backend/main.py`
**File:** `backend/main.py` (modify existing `/api/evaluate`)

```python
# TAMBAHKAN DI AWAL FILE:
from ai_core.inference.predictor import UnifiedPredictor

# INITIALIZE SAAT STARTUP:
predictor = UnifiedPredictor(mode="hybrid")  # atau baca dari env

@app.on_event("startup")
async def startup():
    global predictor
    predictor = UnifiedPredictor(mode=os.environ.get("AI_MODE", "hybrid"))

# UPDATE ENDPOINT /api/evaluate:
@app.post("/api/evaluate")
async def evaluate_drawing(request: EvaluationRequest):
    # ... existing normalization code (keep!) ...
    
    # GANTI BAGIAN EVALUASI:
    # OLD: accuracy = calculate_accuracy(filepath, char_target)
    # NEW:
    result = predictor.predict(filepath, char_target)
    accuracy = result.score
    stars = result.stars
    
    # Tambahkan breakdown ke response:
    return {
        "status": "success",
        "accuracy": accuracy,
        "stars": stars,
        "confidence": result.confidence,
        "method": result.method_used,       # "hybrid_v1", "cnn", etc.
        "breakdown": result.breakdown,      # {cv: 78, ml: 85, dl: 83}
        "tip": result.tip,                  # "Terus pertahankan goresannya!"
        "model_version": predictor.get_model_info()["version"],
    }
```

- [ ] Update `/api/evaluate` untuk pakai UnifiedPredictor
- [ ] Tambahkan response fields: `confidence`, `method`, `breakdown`, `tip`, `model_version`
- [ ] Tambahkan endpoint `GET /api/models/status` → model info + benchmark summary
- [ ] Tambahkan endpoint `POST /api/models/compare` → kirim gambar → hasil semua model side-by-side
- [ ] Environment variable `AI_MODE=baseline|ml|cnn|hybrid` untuk switch cepat

#### 5.5 Model Registry & Versioning
**File:** `ai_core/inference/model_registry.json`

```json
{
  "registry": {
    "baseline_v3": {
      "type": "cv",
      "file": "ai_core/pattern_matching.py",
      "version": "3.0",
      "accuracy_estimated": "65-75%",
      "inference_ms": "<50",
      "status": "active_fallback"
    },
    "svm_v1": {
      "type": "classical_ml",
      "file": "ai_core/models/classical/svm.pkl",
      "version": "1.0",
      "accuracy_cv": "78%",
      "inference_ms": "<10",
      "status": "production"
    },
    "cnn_v1": {
      "type": "deep_learning",
      "file": "ai_core/models/deep/cnn_simple/weights.h5",
      "version": "1.0",
      "accuracy_cv": "85%",
      "inference_ms": "<100",
      "status": "production"
    },
    "hybrid_v1": {
      "type": "ensemble",
      "components": ["baseline_v3", "svm_v1", "cnn_v1"],
      "weights": {"cv": 0.30, "ml": 0.35, "dl": 0.35},
      "version": "1.0",
      "accuracy_cv": "87%",
      "inference_ms": "<150",
      "status": "default"
    }
  },
  "last_updated": "2026-05-29"
}
```

- [ ] Create model registry JSON
- [ ] Version tracking untuk setiap model
- [ ] Rollback capability: switch ke previous version kalau baru bermasalah

### Deliverable PKB-5:
> Hybrid Engine produksi siap pakai. 3 branch (CV + ML + DL) digabung. Integrated ke `/api/evaluate`. Response sekarang kaya (confidence, breakdown, tip). Model registry dengan versioning. Switch mode via env var.

---

## 📊 FASE PKB-6: Comprehensive Benchmark & Documentation

**Goal:** Dokumentasikan seluruh hasil experiment PKB — untuk laporan mata kuliah & portfolio

**Estimasi:** 2-3 jam

**Depends on:** PKB-5 (semua model sudah jadi)

### Checklist PKB-6:

#### 6.1 Master Benchmark Report
**File:** `ai_core/evaluation/BENCHMARK_REPORT.md`

- [ ] **Comparison table ALL models:**
  
  | Model | Type | Accuracy | Precision | Recall | F1 | Inference (ms) | Params | Size |
  |-------|------|----------|-----------|--------|-----|----------------|--------|------|
  | Baseline CV v3 | Rule-based | 68% | 65% | 63% | 64% | 45ms | 0 | 0 |
  | kNN | Classical | 72% | 70% | 69% | 69% | 8ms | 0 | 50KB |
  | Naive Bayes | Classical | 71% | 68% | 67% | 67% | 3ms | 0 | 30KB |
  | SVM (RBF) | Classical | 79% | 77% | 76% | 76% | 5ms | 0 | 100KB |
  | Decision Tree | Classical | 74% | 72% | 71% | 71% | 2ms | 0 | 25KB |
  | Random Forest | Classical | 81% | 79% | 78% | 78% | 12ms | 0 | 200KB |
  | Logistic Reg. | Classical | 73% | 71% | 70% | 70% | 2ms | 0 | 15KB |
  | CNN (from scratch) | Deep Learning | 86% | 84% | 83% | 84% | 95ms | 1.3M | 5MB |
  | CNN (Transfer) | Deep Learning | 88% | 86% | 85% | 86% | 110ms | 1.5M | 8MB |
  | **Hybrid (CV+SVM+CNN)** | **Ensemble** | **89%** | **87%** | **87%** | **87%** | **155ms** | **2.8M** | **13MB** |

  *(angka di atas adalah CONTOH — ganti dengan hasil aktual)*

- [ ] **Confusion matrix visualization** per model (top 5 model)
- [ ] **Inference time vs Accuracy scatter plot** (speed-accuracy tradeoff)
- [ ] **Model size comparison** (important for deployment)
- [ ] **Best model recommendation** dengan alasan

#### 6.2 Algorithm Documentation (for PKB Report)
**File:** `ai_core/docs/ALGORITHM_DOCS.md`

Untuk setiap algoritma, dokumentasikan:

```markdown
## 1. k-Nearest Neighbors (kNN)

### Teori
Rumus: Classify(x) = majority_class of k nearest neighbors
Distance: Euclidean d(x,y) = √Σ(xᵢ-yᵢ)²

### Implementasi Sahabat Aksara
- k=5 (setelah tuning)
- Distance metric: Euclidean
- Features used: 100+ dari PSD (HOG, Hu moments, histogram, ...)
- Why it works: Huruf yang mirip akan memiliki fitur mirip di feature space

### Hasil
- Accuracy: XX%
- Strength: [....]
- Weakness: [....]
```

- [ ] Dokumen untuk: kNN, Naive Bayes, SVM, Decision Tree, Random Forest, CNN, Hybrid
- [ ] Setiap algoritma: teori, implementasi spesifik, hasil, analisis

#### 6.3 Experiment Tracking
**File:** `ai_core/experiments.log`

- [ ] Log setiap experiment run: timestamp, params, result, duration
- [ ] Reproducibility: seed fix, version control

#### 6.4 Create Demo/Screenshot for Presentation
- [ ] Screenshot: perbandingan output model untuk gambar yang sama
- [ ] Screenshot: Dashboard menunjukkan hasil hybrid evaluation
- [ ] Diagram: arsitektur hybrid engine (untuk poster/presentasi)

### Deliverable PKB-6:
> Benchmark report lengkap (markdown + charts). Dokumen algoritma per model (siap untuk laporan PKB). Experiment log. Demo screenshot. Semua bukti bahwa PKB sudah terimplementasi dengan benar.

---

## 📋 RINGKASAN FASE PKB

| Fase | Nama | Estimasi | Key Deliverable | Output Artifacts |
|------|------|----------|-----------------|------------------|
| **PKB-1** | Baseline Enhancement | 2-3 jam | pattern_matching v4 modular + HOG + SSIM | Refactored modules, new scorers |
| **PKB-2** | Classical ML | 4-5 jam | 6 model tertrain (.pkl) + benchmark | Models, confusion matrices, tree viz |
| **PKB-3** | Neural Network/CNN | 4-6 jam | CNN tertrain + transfer learning | `weights.h5`, training curves |
| **PKB-4** | Bayesian Network | 3-4 jam | Probabilistic scorer + calibration | Bayesian scorer, calib curves |
| **PKB-5** | Ensemble + Production | 4-5 jam | Hybrid Engine integrated ke API | Hybrid engine, updated `/api/evaluate` |
| **PKB-6** | Benchmark & Docs | 2-3 jam | Complete documentation + report | Benchmark MD, algorithm docs |
| **TOTAL** | | **~19-26 jam** | **Complete AI/ML Workflow** | |

---

## 🔗 Dependency Graph PKB

```
PKB-1 (Baseline v4) ──────────┐  (bisa mulai SEKARANG)
                                 │
PKB-2 (Classical ML) ───────────┤  (butuh fitur dari PSD-2)
                                 │
PKB-3 (CNN/DL) ─────────────────┤  (butuh gambar dari PSD-2)
                                 │
PKB-4 (Bayesian) ───────────────┤  (opsional, bisa paralel dengan PKB-3)
                                 │
PKB-5 (Ensemble + API) ◄────────┼─◄ butuh PKB-1, PKB-2, PKB-3 selesai
                                 │
PKB-6 (Benchmark + Docs) ◄──────┴─ butuh semuanya selesai
```

**Rekomendasi urutan kerja:**
1. **PKB-1** dulu (refactor existing, tidak depend pada apa-apa)
2. **PKB-2 + PKB-3** bersamaan (butuh data yang sama dari PSD)
3. **PKB-4** opsional paralel (bonus points untuk silabus)
4. **PKB-5** gabungkan semuanya
5. **PKB-6** dokumentasi final

---

## 🔗 Integrasi Cross-Mata Kuliah (RPL → PSD → PKB)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                              │
│                                                                          │
│  RPL (Infrastructure)                                                   │
│  ════════════════════                                                   │
│  Canvas.jsx ──stroke coords──▶ main.py /api/evaluate                    │
│  CameraView ──frame──▶ face-api.js ──descriptor──▶ Supabase            │
│  Dashboard.jsx ◀──metrics──▶ main.py /api/dashboard/*                   │
│                                                                          │
│  ↓ Data Mengalir ke PSD ↓                                               │
│                                                                          │
│  PSD (Data Pipeline)                                                    │
│  ═══════════════════                                                     │
│  /api/evaluate ──save PNG──▶ data_science/datasets/processed/           │
│  scripts/preprocess_batch.py ──clean──▶ normalized images               │
│  scripts/extract_features.py ──extract──▶ all_features.csv (100+ cols)  │
│  scripts/augment_data.py ──augment──▶ 10x dataset size                  │
│  notebooks/*EDA*.ipynb ──analyze──▶ insights & visualizations           │
│                                                                          │
│  ↓ Matang Data Mengalir ke PKB ↓                                        │
│                                                                          │
│  PKB (AI/ML Engine)                                                     │
│  ═════════════════                                                      │
│  train_classical.py ──train──▶ models/classical/*.pkl (6 models)        │
│  train_cnn.py ──train──▶ models/deep/cnn_simple/weights.h5              │
│  train_bayesian.py ──train──▶ bayesian scorer (probabilistic)           │
│  train_ensemble.py ──combine──▶ hybrid_weights.json                      │
│  inference/hybrid_engine.py ──unify──▶ UnifiedPredictor                 │
│                                                                          │
│  ↓ Prediksi Kembali ke RPL ↓                                            │
│                                                                          │
│  main.py /api/evaluate ──predictor.predict()──▶ {score, stars, tip}    │
│  Canvas.jsx ◀─result──▶ confetti + TTS "Hebat, 85 bintang 3!"         │
│  Dashboard.jsx ◀─aggregate──▶ chart + analytics (updated real-time)     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack PKB

| Layer | Teknologi | Use Case |
|-------|-----------|----------|
| **Classical ML** | Scikit-learn (sklearn) | kNN, NB, SVM, DT, RF, LR, Voting, Stacking |
| **Deep Learning** | TensorFlow / Keras | CNN architecture, training, inference |
| **Transfer Learning** | Keras Applications (MobileNetV2) | Pre-trained model fine-tuning |
| **Bayesian/Probabilistic** | pgmpy / scipy.stats | Bayesian Network, Gaussian distributions |
| **Image Processing** | OpenCV, NumPy | Preprocessing untuk CNN input |
| **Feature Processing** | Pandas, NumPy | Load/manipulasi feature CSV |
| **Model Persistence** | Joblib (sklearn), HDF5 (Keras) | Save/load trained models |
| **Evaluation** | Scikit-learn metrics, matplotlib, seaborn | Confusion matrix, calibration, reports |
| **Explainability** | LIME / SHAP (optional) | Model interpretation |
| **Hyperopt** | Optuna / scikit-optimize (optional) | Hyperparameter search |
| **Integration** | FastAPI, python-multipart | Serve model via REST API |

---

## 🎓 Mapping ke Silabus PKB

| Topik Silabus PKB | Implementasi di Sahabat Aksara | Fase |
|--------------------|-------------------------------|------|
| **Pengenalan AI & Intelligent Agent** | HybridEngine sebagai intelligent agent | PKB-5 |
| **Problem Solving by Search** | Tidak langsung applicable (bukan puzzle/pathfinding) | — |
| **Knowledge Representation** | Feature engineering sebagai knowledge representation | PSD-2 + PKB-2 |
| **Machine Learning Basics** | Training pipeline, train/test split, cross-validation | PKB-2 |
| **Supervised Learning: Classification** | Seluruh model klasifikasi (62 class: A-Z,a-z,0-9) | PKB-2, PKB-3 |
| **Naive Bayes Classifier** | GaussianNB + custom implementation + probabilistic explanation | PKB-2, PKB-4 |
| **Decision Tree** | DecisionTreeClassifier + tree visualization (interpretable AI) | PKB-2 |
| **k-Nearest Neighbors** | KNeighborsClassifier + distance-based reasoning | PKB-2 |
| **Neural Network / Perceptron** | CNN fully-connected layers (Dense 256 → Dense 62) | PKB-3 |
| **Deep Learning / CNN** | Convolutional neural network untuk image classification | PKB-3 |
| **Bayesian Network / Probabilistic Reasoning** | Bayesian Scorer + uncertainty quantification | PKB-4 |
| **Ensemble Learning** | Voting, Stacking, Custom Weighted Ensemble | PKB-5 |
| **Model Evaluation** | K-Fold CV, confusion matrix, precision/recall/F1, calibration | PKB-2, PKB-6 |
| **Overfitting & Regularization** | Dropout, BatchNorm, EarlyStopping, L2 regularization | PKB-3 |

---

## ⚠️ Risiko PKB & Mitigasi

| Risiko | Probabilitas | Dampak | Mitigasi |
|--------|-------------|--------|----------|
| Dataset terlalu kecil untuk CNN (<500 sample) | Tinggi | CNN overfit / underperform vs classical | Agresif augmentasi, transfer learning, simpulkan arsitektur |
| Imbalance class (huruf populer >> jarang) | Sedang | Model bias ke huruf umum | Class weighting, oversampling minority |
| Inference time CNN terlalu lambat (>500ms) | Sedang | UX jelek (anak menunggu) | Lightweight CNN, model quantization, async eval |
| TensorFlow/PyTorch tidak terinstall | Sedang | Tidak bisa train CNN | Fallback ke classical only, Docker container |
| Model tidak generalize ke anak TK (berbeda dari EMNIST dewasa) | Tinggi | Akurasi rendah di production | Collect real data from siswa, fine-tune continuously |
| Overfitting decision tree (complex tree) | Rendah | Poor generalization | Limit depth, pruning, use RF instead |

---

*Dokumen ini adalah panduan implementasi PKB untuk Sahabat Aksara. Setiap fase memiliki deliverable yang jelas, terintegrasi dengan PSD (data input) dan RPL (output consumption). Semua algoritma wajib silabus PKB tercover.*
