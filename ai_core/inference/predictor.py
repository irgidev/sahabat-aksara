"""
PKB-5.3: Unified Predictor API (v2.0-retrained)
==============================================
Single entry point for all AI predictions in Sahabat Aksara.
Wraps HybridHandwritingEngine with additional conveniences:
  - Multiple modes (baseline/ml/cnn/hybrid/auto)
  - Model caching
  - Batch prediction
  - Error recovery
  - Model info endpoint

v2.0 UPDATE: Now uses RETRAINED models (6,064 labeled images):
  - Default ML branch → Stacking Ensemble (79% accuracy) ★
  - Default DL branch → CNN Retrained + MobileNetV2 Transfer Learning
  - Fallbacks to legacy models if retrained unavailable

Usage:
    from ai_core.inference.predictor import UnifiedPredictor
    
    predictor = UnifiedPredictor(mode="hybrid")
    result = predictor.predict("image.png", "A")

    

    predictor.set_mode("cv_only")
"""

import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class UnifiedPredictor:
    """
    Unified Prediction Interface — single entry point for all AI models.
    
    Modes:
      - "hybrid"     : CV + ML + DL ensemble (default, best accuracy)
      - "auto"       : Auto-detect available models, use best combination
      - "cv_only"    : Computer Vision pattern matching only (fastest)
      - "ml_only"    : Classical ML only
      - "dl_only"    : Deep Learning CNN only
      - "baseline"   : Alias for cv_only (backward compat)
    """
    
    def __init__(self, mode="hybrid"):
        self._mode = mode
        self._engine = None
        self._init_time = time.time()
        self._prediction_count = 0
        self._cache = {}
    
    @property
    def mode(self):
        return self._mode
    
    def set_mode(self, mode):
        """Switch prediction mode (invalidates engine cache)."""
        valid_modes = ("hybrid", "auto", "cv_only", "ml_only", "dl_only", "baseline")
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")
        
        old_mode = self._mode
        self._mode = mode
        self._engine = None
        
        print(f"[UnifiedPredictor] Mode changed: {old_mode} → {mode}")
        return self
    
    def _get_engine(self):
        """Lazy-load or return cached engine."""
        if self._engine is None:
            from ai_core.inference.hybrid_engine import HybridHandwritingEngine
            self._engine = HybridHandwritingEngine(mode=self._mode)
            print(f"[UnifiedPredictor] Engine initialized (mode={self._mode})")
        return self._engine
    
    def predict(self, image_path, char_target, use_cache=True):
        """
        Main prediction method.
        
        Args:
            image_path: Path to 64x64 grayscale PNG
            char_target: Target character string ('A'-'Z', 'a'-'z', '0'-'9')
            use_cache: Whether to use prediction cache (default True)
        
        Returns:
            Dict: {
                score (int), stars (int), confidence (str),
                method (str), breakdown (dict), tip (str),
                model_version (str), latency_ms (float),
                status (str), char_target (str),
                models_available (dict)
            }
        """
        self._prediction_count += 1
        

        cache_key = f"{image_path}:{char_target}:{self._mode}"
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key].copy()
            cached["cached"] = True
            return cached
        
        engine = self._get_engine()
        result = engine.evaluate(str(image_path), str(char_target))
        

        if use_cache:
            if len(self._cache) >= 100:

                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[cache_key] = result
        
        return result
    
    def predict_batch(self, image_paths, char_targets):
        """
        Batch prediction for analytics/re-scoring.
        
        Args:
            image_paths: List of image paths
            char_targets: List of target characters (same length)
        
        Returns:
            List of result dicts
        """
        assert len(image_paths) == len(char_targets), \
            "image_paths and char_targets must have same length"
        
        engine = self._get_engine()
        return engine.predict_batch(
            [str(p) for p in image_paths],
            [str(t) for t in char_targets]
        )
    
    def compare_models(self, image_path, char_target):
        """
        Run ALL available models on the same image and return side-by-side comparison.
        Used by /api/models/compare endpoint.
        
        Returns:
            Dict with per-model results + agreement analysis
        """
        from ai_core.inference.hybrid_engine import (
            score_branch_cv, score_branch_ml, score_branch_dl,
            compute_stars, compute_confidence
        )
        
        image_path = str(image_path)
        char_target = str(char_target).upper() if char_target else "A"
        
        comparisons = {}
        

        cv_result = score_branch_cv(image_path, char_target)
        comparisons["cv"] = {
            "score": cv_result.get("score"),
            "method": cv_result.get("method"),
            "stars": compute_stars(cv_result.get("score", 0)) if cv_result.get("score") else 0,
            "status": "ok" if cv_result.get("success") else "error"
        }
        
        ml_result = score_branch_ml(image_path, char_target)
        comparisons["ml"] = {
            "score": ml_result.get("score"),
            "method": ml_result.get("method"),
            "model_used": ml_result.get("model_used"),
            "stars": compute_stars(ml_result.get("score", 0)) if ml_result.get("score") else 0,
            "status": "ok" if ml_result.get("success") else "unavailable"
        }
        
        dl_result = score_branch_dl(image_path, char_target)
        comparisons["dl"] = {
            "score": dl_result.get("score"),
            "method": dl_result.get("method"),
            "confidence_level": dl_result.get("confidence_level"),
            "stars": compute_stars(dl_result.get("score", 0)) if dl_result.get("score") else 0,
            "status": "ok" if dl_result.get("success") else "unavailable"
        }
        

        valid_scores = [v["score"] for v in comparisons.values() 
                       if v.get("score") is not None]
        
        if len(valid_scores) >= 2:
            import numpy as np
            avg_score = np.mean(valid_scores)
            score_range = max(valid_scores) - min(valid_scores)
            agreement = "high" if score_range < 15 else "medium" if score_range < 30 else "low"
        else:
            avg_score = valid_scores[0] if valid_scores else None
            score_range = 0
            agreement = "unknown"
        
        return {
            "comparisons": comparisons,
            "summary": {
                "average_score": round(float(avg_score), 1) if avg_score else None,
                "score_range": int(score_range),
                "agreement_level": agreement,
                "models_responded": sum(1 for v in comparisons.values() if v["status"] == "ok"),
                "total_models": 3,
            },
            "image_path": image_path,
            "char_target": char_target,
        }
    
    def get_model_info(self):
        """Return comprehensive model metadata."""
        engine = self._get_engine()
        base_info = engine.get_model_info()
        
        return {
            **base_info,
            "predictor_version": "2.0.0-retrained",
            "current_mode": self._mode,
            "uptime_seconds": round(time.time() - self._init_time, 1),
            "total_predictions": self._prediction_count,
            "cache_size": len(self._cache),
            "supported_modes": ["hybrid", "auto", "cv_only", "ml_only", "dl_only", "baseline"],
        }
    
    def clear_cache(self):
        """Clear prediction cache."""
        self._cache.clear()






_global_predictor = None


def get_predictor(mode=None):
    """
    Get the global UnifiedPredictor instance.
    Used by FastAPI endpoints to share a single predictor across requests.
    
    Args:
        mode: Override mode (or None to keep current)
    
    Returns:
        UnifiedPredictor instance
    """
    global _global_predictor
    
    if _global_predictor is None:
        env_mode = os.environ.get("AI_MODE", "hybrid")
        effective_mode = mode or env_mode
        _global_predictor = UnifiedPredictor(mode=effective_mode)
    elif mode is not None:
        _global_predictor.set_mode(mode)
    
    return _global_predictor


def reset_predictor():
    """Reset global predictor (useful for testing or hot-reload)."""
    global _global_predictor
    if _global_predictor is not None:
        _global_predictor.clear_cache()
    _global_predictor = None
