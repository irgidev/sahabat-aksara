"""
PKB-6.2: Algorithm Documentation Generator
==========================================
Auto-generate comprehensive algorithm documentation for each ML model
used in Sahabat Aksara. Produces a single ALGORITHM_DOCS.md file.

Output:
  - ai_core/docs/ALGORITHM_DOCS.md

Run:
    backend/venv/Scripts/python.exe ai_core/evaluation/generate_algorithm_docs.py
"""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "ai_core" / "docs"


ALGORITHM_DEFINITIONS = [
    {
        "id": "knn",
        "name": "k-Nearest Neighbors (kNN)",
        "category": "Classical ML",
        "type": "instance_based",
        "theory": """


**k-Nearest Neighbors (kNN)** adalah algoritma klasifikasi *lazy learning* yang tidak membangun model eksplisit saat training. Sebaliknya, ia menyimpan seluruh data training dan melakukan klasifikasi berdasarkan kedekatan ke tetangga terdekat.



```
d(x, y) = √Σᵢ(xᵢ - yᵢ)²    (Euclidean Distance)

Classify(x) = majority_class of k nearest neighbors to x
```

Dimana:
- **x** = sample yang akan diklasifikasi (vektor fitur)
- **k** = jumlah tetangga terdekat yang dipertimbangkan
- **d(x,y)** = jarak Euclidean antara x dan y di ruang fitur



1. **Huruf mirip → fitur mirip:** Huruf 'A' yang ditulis oleh anak A dan anak B akan memiliki fitur (Hu moments, HOG, histogram) yang lebih dekat satu sama lain daripada dengan huruf 'B'
2. **Non-parametrik:** Tidak perlu asumsi distribusi data — penting karena goresan anak TK sangat variatif
3. **Interpretable:** Bisa tunjukkan tetangga terdekat sebagai "contoh referensi"


- Lambat untuk dataset besar (O(ND) per prediksi)
- Sensitif terhadap fitur tidak relevan (dimensionality curse)
- Perlu scaling fitur yang baik
""",
        "implementation": """


```python
from sklearn.neighbors import KNeighborsClassifier

model = KNeighborsClassifier(
    n_neighbors=5,
    weights='distance',
    metric='euclidean',
    n_jobs=-1
)
```


- **k=5:** Dipilih via cross-validation (k=3 terlalu noise, k=11 terlalu smooth)
- **Distance weighting:** `distance` memberikan bobot lebih ke tetangga sangat dekat
- **Features used:** ~20 fitur dari PSD (pixel count, aspect ratio, Hu moments, histogram stats)
- **Preprocessing:** StandardScaler sebelum kNN (sangat penting!)
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| Mudah dipahami & diimplementasi | Lambat untuk large dataset |
| Tidak perlu training (lazy) | Memory intensive |
| Non-parametrik (fleksibel) | Sensitif terhadap irrelevant features |
| Bisa update data tanpa retrain | Perlu feature scaling |
| Natural multi-class support | Curse of dimensionality |
""",
        "result_template": {
            "accuracy_estimate": "70-78%",
            "inference_time": "<10ms",
            "best_for": "Baseline ML comparison, small datasets",
            "notes": "Good baseline for classical ML approach"
        }
    },
    {
        "id": "naive_bayes",
        "name": "Gaussian Naive Bayes",
        "category": "Classical ML",
        "type": "probabilistic",
        "theory": """


**Naive Bayes** adalah classifier probabilistik berdasarkan **Teorema Bayes** dengan asumsi independensi ("naive") antar-fitur.



```
P(c|f₁,f₂,...,fₙ) ∝ P(c) × ∏ᵢ P(fᵢ|c)

c* = argmax_c P(c) × ∏ᵢ P(fᵢ|c)
```

Dimana:
- **c** = class (huruf target: A-Z, a-z, 0-9)
- **fᵢ** = fitur ke-i (dari ~20 fitur PSD)
- **P(c)** = prior probability (seberapa umum huruf ini muncul)
- **P(fᵢ|c)** = likelihood (distribusi Gaussian per fitur per class)



Untuk fitur kontinu, GNB mengasumsikan:
```
P(fᵢ|c) = N(fᵢ; μᵢc, σ²ᵢc)

       1         (fᵢ - μᵢc)²
= ───────── exp(─ ─────────────)
   σ√2π           2σ²ᵢc
```

Setiap fitur dimodelkan sebagai distribusi Gaussian dengan mean (μ) dan variance (σ²) yang dipelajari per class.



Asumsi bahwa semua fitur **independen** satu sama lain diberikan class.
Dalam kenyataan asumsi ini **salah** (fitur gambar saling berkorelasi),
tapi Naive Bayes tetap bekerja dengan baik secara praktis!



1. **Super cepat:** Training O(ND), inference O(D) — instant!
2. **Probabilistic output:** Bisa kasih confidence score natural
3. **Handle missing values:** Fitur hilang tidak masalah
4. **Cocok untuk small dataset:** Tidak overfit mudah
""",
        "implementation": """


```python
from sklearn.naive_bayes import GaussianNB

model = GaussianNB(
    var_smoothing=1e-9
)
```


- **var_smoothing=1e-9:** Mencegah division by zero untuk fitur dengan variance mendekati 0
- **Tidak perlu scaling:** GaussianNB invariant terhadap linear transformasi
- **Output:** P(class|x) untuk semua 62 class — bisa digunakan untuk uncertainty quantification
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| Sangat cepat (training + inference) | Asumsi independence jarang benar |
| Probabilistic (confidence score) | Performa kurang jika fitur berkorelasi tinggi |
| Handle missing values | Tidak bisa belajar interaksi fitur |
| Tidak overfit pada small data | Estimasi mungkin underconfident |
| Mudah dijelaskan ke non-teknikal | Feature independence assumption unrealistic |
""",
        "result_template": {
            "accuracy_estimate": "68-75%",
            "inference_time": "<3ms",
            "best_for": "Fast baseline, real-time feedback, uncertainty estimation",
            "notes": "Wajib silabus PKB — probabilitas kondisional"
        }
    },
    {
        "id": "svm",
        "name": "Support Vector Machine (RBF Kernel)",
        "category": "Classical ML",
        "type": "discriminative",
        "theory": """


**Support Vector Machine (SVM)** mencari *hyperplane optimal* yang memisahkan class-class dengan **margin maksimal**.



```
Minimize: ½||w||² + C Σξᵢ
Subject to: yᵢ(w·xᵢ + b) ≥ 1 - ξᵢ   ∀i
            ξᵢ ≥ 0                          ∀i
```

Dimana:
- **w** = normal vector hyperplane pemisah
- **b** = bias term
- **C** = regularization parameter (trade-off margin vs violations)
- **ξᵢ** = slack variable (toleransi misclassification)
- **Support Vectors** = sample tepat di margin boundary



Untuk data non-linearly separable (seperti handwriting!):

```
K(x, y) = exp(-γ ||x - y||²)
```

RBF kernel memproyeksikan data ke ruang dimensi tak hingga,
membuat class yang tidak linearly separable di ruang asli menjadi separable.



1. **Margin maximization:** Robust terhadap noise (penting untuk goresan anak TK!)
2. **Kernel trick:** Bisa menangkap pola kompleks tanpa explicit feature engineering
3. **Sparse solution:** Hanya support vectors yang penting — efisien memory
4. **Strong theoretical foundation:** Convex optimization → global optimum
""",
        "implementation": """


```python
from sklearn.svm import SVC

model = SVC(
    kernel='rbf',
    C=1.0,
    gamma='scale',
    probability=True,
    random_state=42
)
```


- **kernel='rbf':** Non-linear decision boundary untuk pola handwriting kompleks
- **probability=True:** Diperlukan untuk ensemble soft voting (membutuhkan predict_proba)
- **C=1.0:** Balance antara margin lebar vs classification error
- **GridSearchCV range:** C ∈ {0.1, 1, 10}, gamma ∈ {'scale', 'auto'}
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| Margin maximization (robust) | Lambat training untuk large dataset |
| Kernel trick (non-linear) | Sensitive terhadap parameter C, γ |
| Sparse solution (memory efficient) | Tidak scale well ke banyak samples |
| Strong generalization theory | Probability estimates lambat (Platt scaling) |
| Effective di high-dimensional space | Black box (sulit interpretasi) |
""",
        "result_template": {
            "accuracy_estimate": "75-82%",
            "inference_time": "<8ms",
            "best_for": "High accuracy on medium datasets, robust to noise",
            "notes": "Usually best among classical ML models for this task"
        }
    },
    {
        "id": "decision_tree",
        "name": "Decision Tree Classifier",
        "category": "Classical ML",
        "type": "rule_based",
        "theory": """


**Decision Tree** membuat klasifikasi melalui serangkaian aturan if-else yang membentuk struktur pohon. Setiap **internal node** adalah tes pada sebuah fitur, setiap **branch** adalah hasil tes, dan setiap **leaf node** adalah label class.



```
Gini(D) = 1 - Σ(pⱼ)²

Information Gain = Gini(parent) - Σ(|Dᵢ|/|D|) × Gini(Dᵢ)
```

Tree memilih split yang **memaksimalkan information gain** (atau minimize G impurity).



```
IF hu_moment_1 < 0.15 AND pixel_count > 200 AND aspect_ratio < 1.2
  THEN Class = 'A' (confidence: 85%)
ELSE IF hu_moment_3 > 0.4 AND contour_count == 1
  THEN Class = 'I' (confidence: 72%)
...
```



1. **INTERPRETABLE!** — Satu-satunya model yang bisa dijelaskan visual ke guru/siswa
2. **Tidak perlu scaling** — fitur dengan unit berbeda tidak masalah
3. **Menangkap interaksi fitur** — otomatis menemukan kombinasi fitur yang informatif
4. **Fast inference** — O(depth) decisions per prediction
""",
        "implementation": """


```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(
    max_depth=10,
    criterion='gini',
    min_samples_split=5,
    random_state=42
)
```


- **max_depth=10:** Balance antara akurasi dan interpretability (depth > 15 sulit dibaca manusia)
- **Exportable ke PNG:** Tree structure bisa divisualisasikan
- **Feature importance:** Otomatis memberi ranking fitur paling penting
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| ★ INTERPRETABLE (visual rules!) | Mudah overfit (tanpa pruning) |
| Tidak perlu feature scaling | Instable (perubahan data kecil → tree beda) |
| Handle both numerical & categorical | Bias toward features dengan banyak unique values |
| Feature importance built-in | Greedy optimization (tidak global optimum) |
| Super fast inference (<2ms) | Axis-aligned boundaries saja |
""",
        "result_template": {
            "accuracy_estimate": "70-76%",
            "inference_time": "<2ms",
            "best_for": "Interpretability, explainable AI, fast inference",
            "notes": "Best choice when you need to explain WHY to teachers"
        }
    },
    {
        "id": "random_forest",
        "name": "Random Forest Classifier",
        "category": "Classical ML (Ensemble)",
        "type": "ensemble_trees",
        "theory": """


**Random Forest** adalah **ensemble method** yang menggabungkan banyak Decision Tree. Setiap tree dilatih pada **bootstrap sample** (random subset dengan replacement) dan menggunakan **random subset fitur** di setiap split.



```
For each tree t = 1..T:
  1. Sample Dₜ from D with replacement (bootstrap)
  2. Train tree t on Dₜ using random √p features per split
  3. Store tree t

Prediction = majority vote (hard) or average probability (soft) of all trees
```



1. **Variance reduction:** Rata-rata banyak tree mengurangi variance (overfitting)
2. **Decorrelated trees:** Random feature selection membuat tree saling berbeda
3. **Parallelizable:** Setiap tree independent → bisa train parallel
4. **Robust:** Tidak mudah terpengaruh outlier/noise



```
Generalization Error = Bias² + Variance + Irreducible Error

Single Decision Tree: Low Bias, High Variance → Overfit
Random Forest: Same Low Bias, Lower Variance → Better Generalization
""",
        "implementation": """


```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
```


- **n_estimators=100:** Trade-off accuracy vs speed (100 sudah cukup stabil)
- **OOB Score:** Out-of-Bag estimate untuk validasi internal (tanpa hold-out set)
- **Feature importance:** Mean decrease in impurity across all trees
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| High accuracy (ensemble effect) | Lebih lambat dari single tree |
| Robust terhadap overfitting | Kurang interpretable (100+ trees) |
| Built-in feature importance | Memory usage lebih besar |
| Handle missing values | Training time lebih lama |
| Parallelizable | Hyperparameter lebih banyak |
""",
        "result_template": {
            "accuracy_estimate": "77-83%",
            "inference_time": "<12ms",
            "best_for": "High accuracy classical ML, robust performance",
            "notes": "Usually best classical ML model before deep learning"
        }
    },
    {
        "id": "logistic_regression",
        "name": "Logistic Regression (Multinomial)",
        "category": "Classical ML",
        "type": "linear",
        "theory": """


**Logistic Regression** adalah classifier linear yang memodelkan **log-odds** (logit) sebagai fungsi linear dari fitur, kemudian mengubah ke probabilitas via **sigmoid function**.



```
P(y=c|x) = softmax(w_c · x + b_c)

           exp(w_c · x + b_c)
         = ────────────────────
           Σⱼ exp(wⱼ · x + bⱼ)
```

Softmax menormalisasi logit semua class menjadi distribusi probabilitas (sum = 1).



```
L = -Σᵢ Σc yᵢ,c log(P(c|xᵢ))
```

Optimasi via **Gradient Descent** (atau L-BFGS solver di scikit-learn).



1. **Baseline linear:** Memberi lower bound performa — jika LR sudah bagus, data relatif linearly separable
2. **Probabilistic output:** Softmax memberi P(class|x) naturally
3. **Regularized:** L1/L2 regularization mencegah overfitting
4. **Calibrated probabilities:** LR probabilities cenderung well-calibrated
""",
        "implementation": """


```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    multi_class='multinomial',
    solver='lbfgs',
    max_iter=1000,
    C=1.0,
    random_state=42
)
```


- **multi_class='multinomial':** Joint optimization (lebih baik dari one-vs-rest untuk >2 classes)
- **StandardScaler wajib:** LR sangat sensitif terhadap skala fitur
- **Interpretable coefficients:** Koefisien w menunjukkan arah & kekuatan pengaruh fitur
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| Simpel & cepat | Hanya linear decision boundary |
| Well-calibrated probabilities | Underfits pada pola kompleks |
| Interpretable coefficients | Perlu feature scaling |
| Good baseline model | Tidak capture feature interactions |
| Regularization built-in | |
""",
        "result_template": {
            "accuracy_estimate": "70-75%",
            "inference_time": "<2ms",
            "best_for": "Linear baseline, calibrated probabilities, fast inference",
            "notes": "Useful as reference point — if LR beats CNN, something is wrong!"
        }
    },
    {
        "id": "cnn",
        "name": "Convolutional Neural Network (SahabatNet)",
        "category": "Deep Learning",
        "type": "neural_network",
        "theory": """


**CNN (Convolutional Neural Network)** adalah arsitektur neural network yang dirancang khusus untuk data grid seperti gambar. CNN menggunakan **convolution**, **pooling**, dan **activation functions** untuk mengekstrak fitur hierarkis dari pixel mentah.



```
Input(64×64×1)
  ↓ Conv2D(32 filters, 3×3) + BatchNorm + ReLU + MaxPool(2×2) + Dropout(0.25)
  ↓ Conv2D(64 filters, 3×3) + BatchNorm + ReLU + MaxPool(2×2) + Dropout(0.25)
  ↓ Conv2D(128 filters, 3×3) + BatchNorm + ReLU + MaxPool(2×2) + Dropout(0.25)
  ↓ Flatten
  ↓ Dense(256) + BatchNorm + ReLU + Dropout(0.5)
  ↓ Dense(62) + Softmax
Output: P(class) untuk 62 karakter
```



**Convolution:**
```
(I * K)(i,j) = Σₘ Σₙ I(i+m, j+n) · K(m,n)
```
Filter/kernel "sliding" mengekstrak pola lokal (edges, curves, corners).

**Max Pooling:**
```
Pooled(i,j) = max{neighborhood around (i,j)}
```
Downsampling + translational invariance.



1. **Learn features automatically:** Tidak perlu hand-craft fitur (HOG, Hu moments, dll.)
2. **Hierarchical representation:** Layer rendah → edges, layer tengah → shapes, layer tinggi → characters
3. **Translation invariance:** Huruf yang sedikit geser tetap dikenali
4. **State-of-the-art untuk image:** CNN adalah standar industri untuk image classification
""",
        "implementation": """


```python
import tensorflow as tf

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(64, 64, 1)),
    tf.keras.layers.Conv2D(32, (3,3), activation='relu'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.MaxPooling2D((2,2)),
    tf.keras.layers.Dropout(0.25),

    tf.keras.layers.Dense(62, activation='softmax')
])
```


- **Input:** Grayscale 64×64 (normalized 0-1)
- **Optimizer:** Adam (lr=1e-3, decay via ReduceLROnPlateau)
- **Callbacks:** EarlyStopping(patience=5), ModelCheckpoint
- **Data Augmentation:** On-the-fly rotation, shift, zoom, elastic distortion
- **Total params:** ~1.29M (lightweight untuk CPU inference)
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| ★ State-of-the-art accuracy | Membutuhkan banyak data training |
| Automatic feature extraction | Inference lebih lambat (~95ms) |
| Hierarchical representations | Black box (sulit interpretasi) |
| Transfer learning compatible | GPU recommended untuk training |
| Translation/rotation invariant | Overkill untuk very small datasets |
""",
        "result_template": {
            "accuracy_estimate": "80-88%",
            "inference_time": "~95ms (CPU)",
            "best_for": "Maximum accuracy, production deployment",
            "notes": "Best single-model accuracy when sufficient training data available"
        }
    },
    {
        "id": "hybrid",
        "name": "Hybrid Engine (CV + ML + DL)",
        "category": "Ensemble",
        "type": "hybrid",
        "theory": """


**Hybrid Engine** menggabungkan 3 paradigma AI yang berbeda:

```
┌─────────────────────────────────────────────┐
│              HYBRID ENGINE v1               │
├─────────────────────────────────────────────┤
│                                              │
│  Branch A: Computer Vision (pattern_match)   │
│  ├── Skeleton overlap scoring                │
│  ├── Distance field analysis                 │
│  ├── Structural similarity                   │
│  └── HOG descriptor matching                │
│  → cv_score (0-100)                         │
│                                              │
│  Branch B: Classical ML                     │
│  ├── Extract 20-dim feature vector          │
│  ├── Run trained sklearn model(s)            │
│  └── Soft voting ensemble                    │
│  → ml_score (0-100)                         │
│                                              │
│  Branch C: Deep Learning (CNN)              │
│  ├── Preprocess image (64×64 grayscale)     │
│  ├── Forward pass through SahabatNet         │
│  └── P(correct_class) × 100                 │
│  → dl_score (0-100)                         │
│                                              │
│  Ensemble Layer:                             │
│  final = α×cv + β×ml + γ×dl                 │
│  (α=0.25, β=0.40, γ=0.35)                  │
│                                              │
└─────────────────────────────────────────────┘
```



```
Score_hybrid = w_cv × Score_cv + w_ml × Score_ml + w_dl × Score_dl

Dimana:
  w_cv = 0.25  (baseline, always available)
  w_ml = 0.40  (classical ML, reliable)
  w_dl = 0.35  (deep learning, highest potential)
  
  w_cv + w_ml + w_dl = 1.0
```



Jika satu branch gagal (model corrupt, timeout), engine otomatis rebalance:

```
If DL unavailable:
  w_cv' = 0.25 / 0.65 ≈ 0.38
  w_ml' = 0.40 / 0.65 ≈ 0.62
```



1. **Redundancy:** Jika satu pendekatan gagal, lain tetap jalan
2. **Complementarity:** CV tangani shape, ML tangani features, DL tangani patterns
3. **Robustness:** Ensemble selalu outperform single model (secara teori & praktik)
4. **Production-ready:** Fallback chain untuk reliability
""",
        "implementation": """


```python
from ai_core.inference.hybrid_engine import HybridHandwritingEngine
from ai_core.inference.predictor import UnifiedPredictor


engine = HybridHandwritingEngine(
    config_path="ai_core/models/ensemble/hybrid_weights.json",
    mode="hybrid"
)


result = engine.evaluate("image.png", "A")


```


- **Weights configurable** via `hybrid_weights.json` (tanpa recompile)
- **Mode switching:** hybrid/auto/cv_only/ml_only/dl_only/baseline
- **Prediction cache:** FIFO 100 entries untuk response cepat
- **Graceful degradation:** Auto-rebalance jika branch unavailable
""",
        "pros_cons": """## Kelebihan & Kekurangan

| ✅ Kelebihan | ❌ Kekurangan |
|---------------|---------------|
| ★ Highest robustness & accuracy | Latency tertinggi (~150ms) |
| Graceful degradation | Kompleksitas implementasi tinggi |
| Configurable without code change | Butuh semua model tersedia |
| Best of all worlds combined | Debugging lebih sulit |
| Production-ready fallback chain | Memory usage tertinggi |
""",
        "result_template": {
            "accuracy_estimate": "85-90%",
            "inference_time": "~150ms",
            "best_for": "Production deployment, maximum accuracy + reliability",
            "notes": "Recommended default for production use"
        }
    },
]


def generate_algorithm_docs(output_path=None):
    """Generate complete ALGORITHM_DOCS.md from definitions."""
    
    if output_path is None:
        output_path = DOCS_DIR / "ALGORITHM_DOCS.md"
    
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    lines = []
    lines.append("# 🧠 Sahabat Aksara — Algorithm Documentation")
    lines.append("")
    lines.append("> **Project:** EdTech PAUD/TK — AI-Powered Handwriting Learning")
    lines.append("> **Mata Kuliah:** Pengantar Kecerdasan Buatan (PKB)")
    lines.append("> **Generated:** Auto-generated by PKB-6.2 Algorithm Docs Generator")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Daftar Algoritma")
    lines.append("")
    lines.append("| # | Algoritma | Kategori | Tipe | Akurasi (est.) | Latensi |")
    lines.append("|---|-----------|----------|------|----------------|--------|")
    
    for i, algo in enumerate(ALGORITHM_DEFINITIONS):
        rt = algo["result_template"]
        lines.append(
            f"| {i+1} | [{algo['name']}](#{algo['id']}) | "
            f"{algo['category']} | {algo['type'].replace('_', ' ')} | "
            f"{rt['accuracy_estimate']} | {rt['inference_time']} |"
        )
    
    lines.append("")
    lines.append("---")
    lines.append("")
    

    for algo in ALGORITHM_DEFINITIONS:
        aid = algo["id"]
        lines.append(f"""<a id="{aid}"></a>


> **Kategori:** {algo['category']} | **Tipe:** {algo['type'].replace('_', ' ')}

{algo['theory']}

{algo['implementation']}

{algo['pros_cons']}



| Metrik | Nilai |
|--------|-------|
| Akurasi | {rt['accuracy_estimate']} |
| Inference Time | {rt['inference_time']} |
| Best For | {rt['best_for']} |
| Catatan | {rt['notes']} |

---
""")
    
    content = "\n".join(lines)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Algorithm docs generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_algorithm_docs()
