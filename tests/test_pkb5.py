"""
Test Suite: PKB-5 — Ensemble, Hybrid Engine & Production Integration
=====================================================================
Covers:
  PKB-5.1 Ensemble Methods (Soft Voting, Stacking, Custom Weights)
  PKB-5.2 Hybrid Engine (3-branch evaluation, graceful degradation)
  PKB-5.3 Unified Predictor API (multi-mode, batch, compare)
  PKB-5.4 FastAPI Integration (/api/evaluate enhanced, /api/models/status, /api/models/compare)
  PKB-5.5 Model Registry (JSON structure, versioning)

Run:
    backend/venv/Scripts/python.exe tests/test_pkb5.py -v
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))






def _make_test_image(path):
    """Create a minimal 64x64 test image."""
    import cv2
    img = np.zeros((64, 64), dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (54, 54), 255, -1)
    cv2.imwrite(str(path), img)
    return path


import numpy as np
TEST_IMAGE = PROJECT_ROOT / "data_science" / "datasets" / "processed" / "A" / "_test_pkb5.png"


def _setup_test_image():
    """Ensure test image exists."""
    TEST_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    if not TEST_IMAGE.exists():
        _make_test_image(TEST_IMAGE)
    return str(TEST_IMAGE)






class TestEnsembleTraining:
    """PKB-5.1: Ensemble training pipeline outputs."""

    def test_voting_classifier_exists(self):
        """Voting classifier .pkl file should exist after training."""
        pkl = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "voting_classifier.pkl"
        assert pkl.exists(), f"Missing: {pkl}"

    def test_stacking_ensemble_exists(self):
        """Stacking ensemble .pkl file should exist after training."""
        pkl = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "stacking_meta.pkl"
        assert pkl.exists(), f"Missing: {pkl}"

    def test_hybrid_weights_json_exists(self):
        """Hybrid weights config JSON should exist."""
        json_path = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "hybrid_weights.json"
        assert json_path.exists(), f"Missing: {json_path}"

    def test_hybrid_weights_structure(self):
        """Hybrid weights JSON should have correct structure.
        
        Supports both formats:
          - Retrained (flat): {cv_baseline, ml_ensemble, dl_cnn, version, ...}
          - Legacy (nested): {version, branches: {cv: {weight}, ml: {weight}, dl: {weight}}}
        """
        json_path = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "hybrid_weights.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "version" in data
        
        if "branches" in data:

            assert "cv" in data["branches"]
            assert "ml" in data["branches"]
            assert "dl" in data["branches"]
            total_w = sum(b.get("weight", 0) for b in data["branches"].values())
        else:

            assert "cv_baseline" in data or any(k.startswith("cv") for k in data)
            assert "ml_ensemble" in data or any(k.startswith("ml") for k in data)
            assert "dl_cnn" in data or any(k.startswith("dl") for k in data)
            total_w = sum(v for k, v in data.items() 
                       if k in ("cv_baseline", "ml_ensemble", "dl_cnn"))
        
        assert 0.9 < total_w < 1.1, f"Weights sum to {total_w}, expected ~1.0"

    def test_hybrid_weights_has_thresholds(self):
        """Should contain star and confidence thresholds (optional in v2)."""
        json_path = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "hybrid_weights.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        

        if "star_thresholds" in data:
            assert len(data["star_thresholds"]) == 3
        if "confidence_thresholds" in data:
            assert isinstance(data["confidence_thresholds"], dict)

    def test_training_report_exists(self):
        """Ensemble training report should be generated."""
        report = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "training_report.json"
        assert report.exists()

    def test_voting_classifier_loadable(self):
        """Voting classifier should be loadable with joblib."""
        import joblib
        pkl = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "voting_classifier.pkl"
        model = joblib.load(pkl)
        assert model is not None

        assert hasattr(model, "estimators_") or hasattr(model, "estimators")

    def test_stacking_loadable(self):
        """Stacking ensemble should be loadable with joblib."""
        import joblib
        pkl = PROJECT_ROOT / "ai_core" / "models" / "ensemble" / "stacking_meta.pkl"
        model = joblib.load(pkl)
        assert model is not None






class TestHybridEngine:
    """PKB-5.2: HybridHandwritingEngine core functionality."""

    def _get_engine(self):
        from ai_core.inference.hybrid_engine import HybridHandwritingEngine
        return HybridHandwritingEngine(mode="auto")

    def test_engine_instantiates(self):
        """Hybrid engine should instantiate without error."""
        engine = self._get_engine()
        assert engine is not None
        assert engine.mode == "auto"

    def test_evaluate_returns_dict(self):
        """evaluate() should return a dict with required keys."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        assert isinstance(result, dict)
        assert "score" in result
        assert "stars" in result
        assert "confidence" in result
        assert "method" in result

    def test_score_range(self):
        """Score should be in [0, 100]."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        assert 0 <= result["score"] <= 100

    def test_stars_range(self):
        """Stars should be in [0, 3]."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        assert 0 <= result["stars"] <= 3

    def test_confidence_is_valid(self):
        """Confidence should be one of valid levels."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        assert result["confidence"] in ("high", "medium", "low", "none")

    def test_breakdown_has_branches(self):
        """Breakdown should have cv/ml/dl keys."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        breakdown = result.get("breakdown", {})
        assert "cv" in breakdown
        assert "ml" in breakdown
        assert "dl" in breakdown

    def test_tip_is_string(self):
        """Tip should be a non-empty string (Bahasa Indonesia)."""
        img = _setup_test_image()
        engine = self._get_engine()
        result = engine.evaluate(img, "A")
        
        tip = result.get("tip", "")
        assert isinstance(tip, str)
        assert len(tip) > 0

    def test_cv_branch_always_works(self):
        """CV branch should always succeed (it's the baseline)."""
        img = _setup_test_image()
        from ai_core.inference.hybrid_engine import score_branch_cv
        
        result = score_branch_cv(img, "A")
        assert result["success"] is True
        assert isinstance(result["score"], int)

    def test_model_info_returns_dict(self):
        """get_model_info() should return structured dict."""
        engine = self._get_engine()
        info = engine.get_model_info()
        
        assert isinstance(info, dict)
        assert "engine_version" in info
        assert "mode" in info
        assert "branches" in info

    def test_graceful_degradation_bad_image(self):
        """Engine should handle missing image gracefully."""
        engine = self._get_engine()
        result = engine.evaluate("/nonexistent/path.png", "A")
        
        assert result["status"] == "error"

    def test_batch_prediction(self):
        """predict_batch should work with multiple images."""
        img = _setup_test_image()
        engine = self._get_engine()
        
        results = engine.predict_batch([img, img], ["A", "B"])
        assert len(results) == 2
        for r in results:
            assert "score" in r






class TestUnifiedPredictor:
    """PKB-5.3: UnifiedPredictor API."""

    def _get_predictor(self):
        from ai_core.inference.predictor import UnifiedPredictor
        return UnifiedPredictor(mode="auto")

    def test_predictor_instantiates(self):
        """Predictor should instantiate without error."""
        pred = self._get_predictor()
        assert pred is not None
        assert pred.mode == "auto"

    def test_predict_returns_result(self):
        """predict() should return full result dict."""
        img = _setup_test_image()
        pred = self._get_predictor()
        result = pred.predict(img, "A")
        
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "score" in result

    def test_mode_switching(self):
        """set_mode() should change mode and invalidate cache."""
        pred = self._get_predictor()
        assert pred.mode == "auto"
        
        pred.set_mode("cv_only")
        assert pred.mode == "cv_only"
        

        try:
            pred.set_mode("invalid_mode")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_compare_models(self):
        """compare_models() should return per-model comparison."""
        img = _setup_test_image()
        pred = self._get_predictor()
        result = pred.compare_models(img, "A")
        
        assert "comparisons" in result
        assert "summary" in result
        assert "cv" in result["comparisons"]
        assert "ml" in result["comparisons"]
        assert "dl" in result["comparisons"]

    def test_compare_summary_fields(self):
        """Compare summary should have analysis fields."""
        img = _setup_test_image()
        pred = self._get_predictor()
        result = pred.compare_models(img, "A")
        
        summary = result["summary"]
        assert "agreement_level" in summary
        assert "models_responded" in summary
        assert summary["agreement_level"] in ("high", "medium", "low", "unknown")

    def test_get_model_info(self):
        """get_model_info() should return predictor metadata."""
        pred = self._get_predictor()
        info = pred.get_model_info()
        
        assert "predictor_version" in info
        assert "current_mode" in info
        assert "supported_modes" in info
        assert "total_predictions" in info

    def test_cache_works(self):
        """Second predict with same args should use cache."""
        img = _setup_test_image()
        pred = self._get_predictor()
        
        r1 = pred.predict(img, "A", use_cache=True)
        r2 = pred.predict(img, "A", use_cache=True)
        
        assert r1.get("cached") is None
        assert r2.get("cached") is True

    def test_clear_cache(self):
        """clear_cache() should empty the cache."""
        pred = self._get_predictor()
        img = _setup_test_image()
        pred.predict(img, "A", use_cache=True)
        assert len(pred._cache) > 0
        
        pred.clear_cache()
        assert len(pred._cache) == 0

    def test_batch_predict(self):
        """predict_batch() should process multiple items."""
        img = _setup_test_image()
        pred = self._get_predictor()
        
        results = pred.predict_batch([img, img], ["A", "B"])
        assert len(results) == 2
        assert all("score" in r for r in results)






class TestFastAPIIntegration:
    """PKB-5.4: FastAPI endpoint integration."""

    def test_models_status_route_exists(self):
        """/api/models/status route should be registered."""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        assert "/api/models/status" in routes

    def test_models_compare_route_exists(self):
        """/api/models/compare route should be registered."""
        import main
        routes = [r.path for r in main.app.routes if hasattr(r, 'path')]
        assert "/api/models/compare" in routes

    def test_models_status_endpoint(self):
        """GET /api/models/status should return model status."""
        from starlette.testclient import TestClient
        import main
        client = TestClient(main.app)
        
        resp = client.get("/api/models/status")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "status" in data
        assert "predictor_available" in data or "baseline" in data

    def test_models_status_has_branches(self):
        """Model status should list CV/ML/DL branches."""
        from starlette.testclient import TestClient
        import main
        client = TestClient(main.app)
        
        resp = client.get("/api/models/status")
        data = resp.json()
        
        if data.get("predictor_available"):
            assert "branches" in data
            assert "cv" in data["branches"]
            assert "ml" in data["branches"]
            assert "dl" in data["branches"]

    def test_evaluate_endpoint_enhanced(self):
        """/api/evaluate should now include PKB-5 fields."""
        from starlette.testclient import TestClient
        import main
        client = TestClient(main.app)
        

        resp = client.post("/api/evaluate", json={
            "strokeCoordinates": [
                {"x": 20, "y": 20}, {"x": 44, "y": 20},
                {"x": 44, "y": 44}, {"x": 20, "y": 44}, {"x": 20, "y": 20}
            ],
            "char_target": "A",
            "lesson_id": 1,
            "student_id": "00000000-0000-0000-0000-000000000000",
        })
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["status"] == "success"
        assert "accuracy" in data
        assert "stars" in data

        assert "algorithm_version" in data

    def test_evaluate_response_has_tip_or_explanation(self):
        """Evaluate response should include tip (PKB-5) or explanation (PKB-1)."""
        from starlette.testclient import TestClient
        import main
        client = TestClient(main.app)
        
        resp = client.post("/api/evaluate", json={
            "strokeCoordinates": [
                {"x": 15, "y": 15}, {"x": 49, "y": 15},
                {"x": 49, "y": 49}, {"x": 15, "y": 49}, {"x": 15, "y": 15}
            ],
            "char_target": "B",
        })
        data = resp.json()
        
        has_tip = "tip" in data
        has_explanation = "explanation" in data
        assert has_tip or has_explanation, "Response should have either 'tip' or 'explanation'"

    def test_backend_syntax_valid(self):
        """main.py should compile without syntax errors."""
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "backend/main.py"), doraise=True)






class TestModelRegistry:
    """PKB-5.5: Model registry JSON structure."""

    def test_registry_file_exists(self):
        """model_registry.json should exist."""
        reg = PROJECT_ROOT / "ai_core" / "inference" / "model_registry.json"
        assert reg.exists(), f"Missing: {reg}"

    def test_registry_has_required_keys(self):
        """Registry should have top-level structure."""
        reg_path = PROJECT_ROOT / "ai_core" / "inference" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "registry" in data
        assert "active_model" in data
        assert "last_updated" in data
        assert "total_models" in data

    def test_registry_has_all_models(self):
        """Registry should list all 14 model entries."""
        reg_path = PROJECT_ROOT / "ai_core" / "inference" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        registry = data["registry"]
        expected_keys = [
            "baseline_v4", "svm_v1", "random_forest_v1", "knn_v1",
            "logistic_regression_v1", "naive_bayes_v1", "decision_tree_v1",
            "cnn_simple_v1", "cnn_transfer_v1", "bayesian_v1",
            "voting_ensemble_v1", "stacking_ensemble_v1", "hybrid_v1",
        ]
        for key in expected_keys:
            assert key in registry, f"Missing registry entry: {key}"

    def test_registry_entries_have_metadata(self):
        """Each registry entry should have type, version, status."""
        reg_path = PROJECT_ROOT / "ai_core" / "inference" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for name, entry in data["registry"].items():
            assert "type" in entry, f"{name} missing 'type'"
            assert "version" in entry, f"{name} missing 'version'"
            assert "status" in entry, f"{name} missing 'status'"
            assert "description" in entry, f"{name} missing 'description'"

    def test_hybrid_is_default(self):
        """hybrid_v1 should be marked as default active model."""
        reg_path = PROJECT_ROOT / "ai_core" / "inference" / "model_registry.json"
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["active_model"] == "hybrid_v1"
        hybrid = data["registry"]["hybrid_v1"]
        assert hybrid["status"] == "default"

    def test_inference_package_init(self):
        """ai_core.inference package should be importable."""
        from ai_core.inference import (
            HybridHandwritingEngine, UnifiedPredictor,
            evaluate_with_hybrid, quick_score, get_predictor
        )
        assert HybridHandwritingEngine is not None
        assert UnifiedPredictor is not None






class TestFeatureExtractor:
    """Test feature extraction bridge between image and ML models."""

    def test_extract_features_returns_array(self):
        """extract_features_from_image should return numpy array."""
        img = _setup_test_image()
        from ai_core.inference.hybrid_engine import extract_features_from_image
        
        features = extract_features_from_image(img)
        assert isinstance(features, np.ndarray)
        assert features.ndim == 1

    def test_features_dimension(self):
        """Feature vector should have exactly 16 dimensions (matches retrained models)."""
        img = _setup_test_image()
        from ai_core.inference.hybrid_engine import extract_features_from_image
        
        features = extract_features_from_image(img)
        assert features.shape[0] == 16

    def test_dummy_features_on_missing_image(self):
        """Should return zeros when image doesn't exist."""
        from ai_core.inference.hybrid_engine import extract_features_from_image, _dummy_features
        
        features = extract_features_from_image("/nonexistent/image.png")
        expected = _dummy_features()
        
        np.testing.assert_array_equal(features, expected)






if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
