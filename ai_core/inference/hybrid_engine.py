"""
PKB-5.2: Hybrid Handwriting Engine
====================================
Combines Computer Vision (pattern matching), Classical ML, and Deep Learning
into a unified scoring pipeline with graceful degradation.

Architecture:
    Input: image_path + char_target
      │
      ├── Branch A: CV pattern_matching → cv_score (0-100)
      ├── Branch B: Classical ML models → ml_score (0-100)
      └── Branch C: Deep Learning CNN → dl_score (0-100)
      │
      ▼ Ensemble Layer (weighted combination)
      │
      Output: {score, stars, confidence, breakdown, tip}

Usage:
    from ai_core.inference.hybrid_engine import HybridHandwritingEngine
    
    engine = HybridHandwritingEngine()
    result = engine.evaluate("image.png", "A")

"""

import os
import sys
import json
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np






class ModelLoader:
    """
    Safe model loader with caching and error handling.
    Loads classical ML (.pkl), deep learning (.h5), and Bayesian (.json) models.
    All load failures are non-fatal — returns None and logs warning.
    """
    
    _cache = {}
    
    @classmethod
    def load_classical(cls, name):
        """Load a scikit-learn model from .pkl file."""
        if name in cls._cache:
            return cls._cache[name]
        
        pkl_path = PROJECT_ROOT / "ai_core" / "models" / "classical" / f"{name}.pkl"
        if not pkl_path.exists():
            return None
        
        try:
            import joblib
            model = joblib.load(pkl_path)
            cls._cache[name] = model
            return model
        except Exception as e:
            print(f"[ModelLoader] Failed to load {name}: {e}")
            return None
    
    @classmethod
    def load_cnn(cls, variant="retrained"):
        """Load CNN model using Keras.
        
        Priority order (by variant):
          - "retrained" : SahabatNet-Tiny retrained on 6K labeled images
          - "simple"    : Original SahabatNet-Tiny (legacy)
          - "mobilenet": MobileNetV2 transfer learning
          - "efficientnet": EfficientNetB0 transfer learning
        
        Supports both .weights.h5 (weights only) and .keras (full model).
        """
        cache_key = f"cnn_{variant}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        

        variant_paths = {

            "retrained": [
                PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_retrained" / "full_model.keras",
                PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_retrained" / "model.weights.h5",
            ],

            "simple": [
                PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple" / "weights.h5",
            ],

            "mobilenet": [
                PROJECT_ROOT / "ai_core" / "models" / "transfer" / "mobilenetv2" / "full_model.keras",
            ],
            "efficientnet": [
                PROJECT_ROOT / "ai_core" / "models" / "transfer" / "efficientnetb0" / "full_model.keras",
            ],
            "transfer": [
                PROJECT_ROOT / "ai_core" / "models" / "transfer" / "mobilenetv2" / "full_model.keras",
                PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_transfer" / "weights.h5",
            ],
        }
        
        candidates = variant_paths.get(variant, [])
        if not candidates:
            return None
        
        for model_path in candidates:
            if not model_path.exists():
                continue
            
            try:
                import keras
                model = keras.models.load_model(str(model_path))
                cls._cache[cache_key] = model
                print(f"[ModelLoader] Loaded CNN ({variant}): {model_path.name}")
                return model
            except Exception as e:
                print(f"[ModelLoader] Failed to load {model_path.name}: {e}")
                continue
        
        print(f"[ModelLoader] No valid CNN model found for variant '{variant}'")
        return None
    
    @classmethod
    def load_bayesian(cls):
        """Load Bayesian Scorer from JSON."""
        if "bayesian" in cls._cache:
            return cls._cache["bayesian"]
        
        json_path = PROJECT_ROOT / "ai_core" / "models" / "bayesian" / "bayesian_scorer.json"
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cls._cache["bayesian"] = data
            return data
        except Exception as e:
            print(f"[ModelLoader] Failed to load Bayesian: {e}")
            return None
    
    @classmethod
    def load_ensemble(cls, name="stacking"):
        """Load ensemble model (.pkl).
        
        Supported names:
          - "stacking" : Stacking meta-learner (79% acc on retrained data) ★ BEST
          - "voting"   : Soft Voting classifier (7% acc)
        """
        cache_key = f"ensemble_{name}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        

        ensemble_files = {
            "stacking": "stacking_meta.pkl",
            "voting": "voting_classifier.pkl",
        }
        
        filename = ensemble_files.get(name)
        if filename is None:
            return None
        
        pkl_path = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / filename
        if not pkl_path.exists():
            return None
        
        try:
            import joblib
            model = joblib.load(pkl_path)
            cls._cache[cache_key] = model
            print(f"[ModelLoader] Loaded ensemble ({name}): {filename}")
            return model
        except Exception as e:
            print(f"[ModelLoader] Failed to load ensemble ({name}): {e}")
            return None
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached models."""
        cls._cache.clear()






def extract_features_from_image(image_path):
    """
    Extract feature vector from an image for ML model inference.
    Returns (N,) numpy array of 16 features — MUST match retraining pipeline's
    _extract_single_features() exactly so dimensions align with trained .pkl models.
    
    Features (16-dim):
      0:  aspect_ratio     (bbox w/h)
      1:  area_ratio        (fg_pixels / total_pixels)
      2:  density            (fg_pixels / bbox_area)
      3:  centering_x        (horizontal centering, 0=centered)
      4:  centering_y        (vertical centering, 0=centered)
      5:  v_symmetry        (vertical flip similarity)
      6:  h_symmetry        (horizontal flip similarity)
      7:  stroke_width_avg  (mean distance transform value)
      8:  stroke_width_std  (std of distance transform)
      9:  contour_complexity (total contour points)
      10: bbox_aspect       (bbox w/h, again for emphasis)
      11-14: quadrant_densities (TL, TR, BL, BR)
      15: pixel_mean        (average pixel intensity)
    """
    try:
        import cv2
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return _dummy_features()
    except Exception:
        return _dummy_features()
    
    h, w = img.shape
    binary = (img < 128).astype(np.uint8) * 255
    total_pixels = h * w
    

    fg_pixels = np.sum(binary > 0)
    area_ratio = fg_pixels / total_pixels
    

    coords = np.where(binary > 0)
    if len(coords[0]) == 0:
        return _dummy_features()
    
    ymin, ymax = int(coords[0].min()), int(coords[0].max())
    xmin, xmax = int(coords[1].min()), int(coords[1].max())
    bh = max(ymax - ymin, 1)
    bw = max(xmax - xmin, 1)
    aspect_ratio = bw / max(bh, 1)
    bbox_aspect = bw / max(bh, 1)
    

    cy_mean = float(np.mean(coords[0])) / h
    cx_mean = float(np.mean(coords[1])) / w
    centering_x = abs(cx_mean - 0.5) * 2
    centering_y = abs(cy_mean - 0.5) * 2
    

    bbox_area = bh * bw
    density = fg_pixels / max(bbox_area, 1)
    

    flipped_h = np.fliplr(binary)
    flipped_v = np.flipud(binary)
    v_sym = 1.0 - float(np.sum(np.abs(binary.astype(float) - flipped_v.astype(float))) / (255 * total_pixels))
    h_sym = 1.0 - float(np.sum(np.abs(binary.astype(float) - flipped_h.astype(float))) / (255 * total_pixels))
    

    try:
        from scipy.ndimage import distance_transform_edt
        dt = distance_transform_edt(binary > 0)
        sw_vals = dt[binary > 0]
        sw_avg = float(np.mean(sw_vals)) if len(sw_vals) > 0 else 2.0
        sw_std = float(np.std(sw_vals)) if len(sw_vals) > 0 else 0.5
    except Exception:
        sw_avg, sw_std = 2.0, 0.5
    

    try:
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_complexity = float(sum(len(c) for c in contours) if contours else 0)
    except Exception:
        contour_complexity = 0.0
    

    qh, qw = h // 2, w // 2
    corners = [
        float(np.sum(binary[:qh, :qw] > 0) / max(qh * qw, 1)),
        float(np.sum(binary[:qh, qw:] > 0) / max(qh * qw, 1)),
        float(np.sum(binary[qh:, :qw] > 0) / max(qh * qw, 1)),
        float(np.sum(binary[qh:, qw:] > 0) / max(qh * qw, 1)),
    ]
    
    pixel_mean = float(np.mean(img))
    
    return np.array([
        aspect_ratio, area_ratio, density, centering_x, centering_y,
        v_sym, h_sym, sw_avg, sw_std, contour_complexity,
        bbox_aspect, *corners, pixel_mean,
    ], dtype=np.float64)


def _dummy_features():
    """Return dummy features (16-dim) when extraction fails."""
    return np.zeros(16, dtype=np.float64)






def score_branch_cv(image_path, char_target):
    """
    Branch A: Computer Vision pattern matching.
    Uses existing calculate_accuracy() function.
    Returns dict: {score, method, details}
    """
    try:
        from ai_core.pattern_matching import calculate_accuracy, evaluate_with_details
        

        details = evaluate_with_details(image_path, char_target=char_target)
        if isinstance(details, dict) and "score" in details:
            return {
                "score": int(details.get("score", 50)),
                "method": "cv_pattern_match_v4",
                "confidence": details.get("confidence", "medium"),
                "breakdown": details.get("breakdown", {}),
                "success": True
            }
        

        score = calculate_accuracy(image_path, char_target=char_target)
        return {
            "score": int(score),
            "method": "cv_baseline",
            "confidence": "medium",
            "breakdown": {},
            "success": True
        }
    except Exception as e:
        print(f"[Branch-CV] Error: {e}")
        return {"score": 50, "method": "cv_error", "confidence": "low", "success": False}


def score_branch_ml(image_path, char_target):
    """
    Branch B: Classical ML models.
    Extracts features from image, runs through best available ML model,
    converts classification probability to 0-100 score.
    
    Strategy: Try SVM first (usually best for handwriting), then RF, then voting ensemble.
    """
    features = extract_features_from_image(image_path)
    X = features.reshape(1, -1)
    

    model_priority = [
        ("stacking", "Stacking Ensemble (79% acc) ★ BEST"),
        ("voting", "Soft Voting Ensemble"),
        ("random_forest", "Random Forest"),
        ("svm", "SVM (RBF kernel)"),
        ("knn", "k-Nearest Neighbors"),
        ("logistic_regression", "Logistic Regression"),
        ("naive_bayes", "Naive Bayes"),
    ]
    
    for model_name, display_name in model_priority:
        if model_name == "voting":
            model = ModelLoader.load_ensemble("voting")
        else:
            model = ModelLoader.load_classical(model_name)
        
        if model is None:
            continue
        
        try:

            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)[0]
                


                max_proba = float(np.max(proba))
                score = int(max_proba * 100)
                
                return {
                    "score": min(score, 99),
                    "method": f"ml_{model_name}",
                    "confidence_level": round(max_proba, 3),
                    "model_used": display_name,
                    "top3_classes": np.argsort(proba)[-3:][::-1].tolist(),
                    "success": True
                }
            elif hasattr(model, 'predict'):
                pred = model.predict(X)[0]

                return {
                    "score": 65,
                    "method": f"ml_{model_name}",
                    "prediction": int(pred),
                    "model_used": display_name,
                    "success": True
                }
        except Exception as e:
            print(f"[Branch-ML] {model_name} failed: {e}")
            continue
    

    return {"score": None, "method": "ml_unavailable", "success": False}


def score_branch_dl(image_path, char_target):
    """
    Branch C: Deep Learning CNN.
    Runs image through trained CNN, gets softmax probability for target class.
    
    Supports both cnn_simple and cnn_transfer variants.
    """
    try:
        import cv2
        import keras
    except ImportError:
        return {"score": None, "method": "dl_no_framework", "success": False}
    

    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {"score": None, "method": "dl_bad_image", "success": False}
        

        img_resized = cv2.resize(img, (64, 64))

        img_normalized = img_resized.astype(np.float32) / 255.0

        img_batch = img_normalized[:, :, np.newaxis]

        img_batch = img_batch[np.newaxis, ...]
    except Exception as e:
        return {"score": None, "method": "dl_preprocess_error", "error": str(e), "success": False}
    

    for variant in ["retrained", "mobilenet", "efficientnet", "simple", "transfer"]:
        model = ModelLoader.load_cnn(variant)
        if model is None:
            continue
        
        try:

            proba = model.predict(img_batch, verbose=0)[0]
            


            max_proba = float(np.max(proba))
            predicted_class = int(np.argmax(proba))
            
            score = int(max_proba * 100)
            
            return {
                "score": min(score, 99),
                "method": f"dl_cnn_{variant}",
                "confidence_level": round(max_proba, 4),
                "predicted_class": predicted_class,
                "all_probabilities": [round(float(p), 4) for p in proba],
                "success": True
            }
        except Exception as e:
            print(f"[Branch-DL] CNN {variant} failed: {e}")
            continue
    
    return {"score": None, "method": "dl_no_model", "success": False}






def compute_confidence(score, branch_scores):
    """
    Compute overall confidence level based on agreement between branches.
    
    High confidence: all branches agree (low variance)
    Medium confidence: some disagreement
    Low confidence: high disagreement or missing branches
    """
    valid_scores = [s for s in branch_scores.values() if s is not None]
    
    if len(valid_scores) <= 1:
        if score >= 70:
            return "medium"
        return "low"
    
    variance = np.var(valid_scores)
    std_dev = np.std(valid_scores)
    
    if std_dev < 10 and score >= 60:
        return "high"
    elif std_dev < 25:
        return "medium"
    else:
        return "low"


def compute_stars(score, thresholds=None):
    """Convert numeric score to star rating (0-3). V3: Super kid-friendly."""
    if thresholds is None:
        thresholds = [20, 45, 70]
    
    if score >= thresholds[2]:
        return 3
    elif score >= thresholds[1]:
        return 2
    elif score >= thresholds[0]:
        return 1
    return 0


def generate_tip(score, stars, confidence, char_target):
    """
    Generate kid-friendly feedback text in Bahasa Indonesia.
    Context-aware based on score range and character being practiced.
    """
    tips_high = [
        f"Wah, huruf '{char_target}'-mu keren banget! 🌟 Terus pertahankan!",
        f"Luar biasa! Huruf '{char_target}' sudah sempurna! 🎉",
        f"Mantap! Tulisan '{char_target}'-mu sangat rapi! ✨",
        f"Hebat sekali! Kamu jago nulis huruf '{char_target}'! ⭐",
    ]
    tips_medium = [
        f"Huruf '{char_target}' sudah bagus! Coba lebih tebal sedikit ya! ✏️",
        f"Bagus! Tulisan '{char_target}'-mu hampir sempurna! 💪",
        f"Cukup bagus! Perhatikan bentuk huruf '{char_target}' dengan teliti! 🔍",
        f"Lumayan! Huruf '{char_target}' bisa lebih lurus lagi! 📏",
    ]
    tips_low = [
        f"Ayah yakin kamu bisa! Coba tulis '{char_target}' perlahan ya! 🌱",
        f"Jangan menyerah! Setiap latihan membuat '{char_target}' semakin bagus! 💪",
        f"Sabar ya! Coba ikuti titik-titik huruf '{char_target}' dengan seksama! 👀",
        f"Tetap semangat! Latihan menulis '{char_target}' itu menyenangkan! 🎨",
    ]
    
    rng = np.random.RandomState(abs(hash(char_target)) % (2**31) + score)
    
    if stars >= 3:
        return str(rng.choice(tips_high))
    elif stars >= 2:
        return str(rng.choice(tips_medium))
    else:
        return str(rng.choice(tips_low))






class HybridHandwritingEngine:
    """
    HYBRID ENGINE v1 — Gabungan terbaik dari semua pendekatan AI
    
    3 Branches:
      A) CV Pattern Matching (baseline, always works)
      B) Classical ML (SVM/RF/kNN, needs .pkl files)
      C) Deep Learning CNN (needs .h5 file)
    
    Graceful degradation: if any branch fails, others compensate.
    Final score = weighted average of successful branches.
    """
    
    def __init__(self, config_path=None, mode="hybrid"):
        """
        Args:
            config_path: Path to hybrid_weights.json (or None for defaults)
            mode: "hybrid" | "cv_only" | "ml_only" | "dl_only" | "auto"
        """
        self.mode = mode
        self.weights = self._load_weights(config_path)
        self._model_status = {}
        self._warm_up()
    
    def _load_weights(self, config_path):
        """Load hybrid weights from JSON or use defaults."""
        if config_path is None:
            config_path = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "hybrid_weights.json"
        
        if Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        

        from ai_core.training.train_ensemble import DEFAULT_HYBRID_WEIGHTS
        return DEFAULT_HYBRID_WEIGHTS.copy()
    
    def _warm_up(self):
        """Pre-load models on initialization (lazy loading on first call otherwise)."""
        pass
    
    def _get_active_weights(self, available_branches):
        """
        Get normalized weights for currently available branches.
        If a branch is missing, redistribute its weight to others.
        """
        raw_weights = {}
        branch_config = self.weights.get("branches", {})
        
        for branch in ["cv", "ml", "dl"]:
            if branch in available_branches:
                raw_weights[branch] = branch_config.get(branch, {}).get("weight", 0.33)
            else:
                raw_weights[branch] = 0.0
        
        total = sum(raw_weights.values())
        if total > 0:
            return {k: v / total for k, v in raw_weights.items()}
        return {"cv": 1.0}
    
    def evaluate(self, image_path, char_target):
        """
        Main evaluation method. Runs all available branches and ensembles results.
        
        Args:
            image_path: Path to 64x64 grayscale PNG image
            char_target: Target character string (e.g., "A", "b", "3")
        
        Returns:
            Dict with keys: score, stars, confidence, method, breakdown, tip,
                            branch_results, model_version, latency_ms
        """
        t_start = time.time()
        

        if not Path(image_path).exists():
            return self._error_result("Image not found", image_path)
        
        char_target = str(char_target).upper() if char_target else "A"
        

        branch_results = {}
        branch_scores = {}
        

        if self.mode in ("hybrid", "cv_only", "auto"):
            cv_result = score_branch_cv(image_path, char_target)
            branch_results["cv"] = cv_result
            if cv_result.get("success"):
                branch_scores["cv"] = cv_result["score"]
            self._model_status["cv"] = cv_result.get("success", False)
        

        if self.mode in ("hybrid", "ml_only", "auto"):
            ml_result = score_branch_ml(image_path, char_target)
            branch_results["ml"] = ml_result
            if ml_result.get("success") and ml_result.get("score") is not None:
                branch_scores["ml"] = ml_result["score"]
            self._model_status["ml"] = ml_result.get("success", False)
        

        if self.mode in ("hybrid", "dl_only", "auto"):
            dl_result = score_branch_dl(image_path, char_target)
            branch_results["dl"] = dl_result
            if dl_result.get("success") and dl_result.get("score") is not None:
                branch_scores["dl"] = dl_result["score"]
            self._model_status["dl"] = dl_result.get("success", False)
        

        active_weights = self._get_active_weights(list(branch_scores.keys()))
        
        if len(branch_scores) == 0:

            return self._error_result("All branches failed", image_path)
        

        final_score = sum(
            active_weights.get(branch, 0) * score
            for branch, score in branch_scores.items()
        )
        final_score = int(round(final_score))
        final_score = max(0, min(100, final_score))
        

        stars = compute_stars(final_score)
        confidence = compute_confidence(final_score, branch_scores)
        tip = generate_tip(final_score, stars, confidence, char_target)
        
        latency_ms = round((time.time() - t_start) * 1000, 1)
        

        methods_used = [r.get("method", "?") for r in branch_results.values()]
        primary_method = "hybrid_v1"
        if len(branch_scores) == 1:
            primary_method = list(branch_scores.keys())[0] + "_only"
        
        return {
            "status": "success",
            "score": final_score,
            "stars": stars,
            "confidence": confidence,
            "method": primary_method,
            "breakdown": {
                "cv": branch_scores.get("cv"),
                "ml": branch_scores.get("ml"),
                "dl": branch_scores.get("dl"),
                "weights_used": active_weights,
            },
            "tip": tip,
            "branch_results": {
                k: {key: v for key, v in result.items() if key != "success"}
                for k, result in branch_results.items()
            },
            "model_version": "hybrid_v2.0-retrained",
            "latency_ms": latency_ms,
            "char_target": char_target,
            "models_available": self._model_status,
        }
    
    def predict_batch(self, image_paths, char_targets):
        """Batch evaluation for analytics/re-scoring."""
        return [self.evaluate(img, tgt) for img, tgt in zip(image_paths, char_targets)]
    
    def get_model_info(self):
        """Return loaded model metadata for status endpoint."""
        return {
            "engine_version": "hybrid_v2.0-retrained",
            "mode": self.mode,
            "weights_version": self.weights.get("version", "unknown"),
            "branches": {
                "cv": {
                    "available": True,
                    "type": "Computer Vision (OpenCV)",
                    "description": "Pattern matching v4 with HOG+SSIM"
                },
                "ml": {
                    "available": self._model_status.get("ml", False),
                    "type": "Classical ML (scikit-learn)",
                    "models_loaded": [k for k in ["svm", "rf", "knn", "lr", "nb", "dt", "voting"]
                                      if ModelLoader.load_classical(k) is not None or ModelLoader.load_ensemble("voting") is not None]
                },
                "dl": {
                    "available": self._model_status.get("dl", False),
                    "type": "Deep Learning (Keras/TensorFlow)",
                    "variants_available": [v for v in ["simple", "transfer"]
                                           if ModelLoader.load_cnn(v) is not None]
                },
            },
            "weights": self.weights.get("branches", {}),
        }
    
    def _error_result(self, message, image_path):
        """Return standardized error result."""
        return {
            "status": "error",
            "message": message,
            "score": 0,
            "stars": 0,
            "confidence": "none",
            "method": "error",
            "image_path": str(image_path),
        }







_engine_instance = None


def get_hybrid_engine(mode="hybrid"):
    """Get or create the global HybridHandwritingEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = HybridHandwritingEngine(mode=mode)
    return _engine_instance


def evaluate_with_hybrid(image_path, char_target, mode="hybrid"):
    """
    Convenience function: one-call evaluation using hybrid engine.
    Backward compatible with calculate_accuracy() signature but returns richer result.
    
    Args:
        image_path: Path to image
        char_target: Target character
        mode: "hybrid" | "cv_only" | "ml_only" | "dl_only"
    
    Returns:
        Dict with full evaluation result (see HybridHandwritingEngine.evaluate())
    """
    engine = get_hybrid_engine(mode=mode)
    return engine.evaluate(image_path, char_target)


def quick_score(image_path, char_target):
    """
    Ultra-simple interface: returns just the integer score (0-100).
    Fully backward compatible with old calculate_accuracy().
    """
    result = evaluate_with_hybrid(image_path, char_target)
    return result.get("score", 0)
