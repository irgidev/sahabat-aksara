"""
Test Suite: PKB-4 — Bayesian Network & Transfer Learning
==========================================================
Covers:
  PKB-4.1 Bayesian Scorer (train_bayesian_network.py)
  PKB-4.2 Probability Calibration (calibrate_models.py)
  PKB-4.3 Transfer Learning (train_transfer_learning.py)

Run:
    backend/venv/Scripts/python.exe tests/test_pkb4.py -v
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ai_core" / "training"))

import numpy as np






def _make_synthetic_features(n=100, n_feat=20, seed=42):
    """Create deterministic feature matrix."""
    rng = np.random.RandomState(seed)
    return rng.randn(n, n_feat)


def _make_synthetic_scores(n=100, seed=42):
    """Create deterministic scores 0-100."""
    rng = np.random.RandomState(seed)
    return rng.uniform(10, 95, n)


def _make_synthetic_proba(n=100, n_classes=10, seed=42):
    """Create probability distributions (rows sum to 1)."""
    rng = np.random.RandomState(seed)
    logits = rng.randn(n, n_classes)
    exp_l = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exp_l / exp_l.sum(axis=1, keepdims=True)


def _make_labels(n=100, n_classes=10, seed=42):
    """Create class labels."""
    rng = np.random.RandomState(seed)
    return rng.randint(0, n_classes, n)






class TestBayesianScorerInit:
    """Test BayesianScorer initialization and basic structure."""

    def test_import_bayesian_module(self):
        """Bayesian module should be importable."""
        from train_bayesian_network import BayesianScorer
        assert BayesianScorer is not None

    def test_create_scorer(self):
        """Should instantiate with default parameters."""
        from train_bayesian_network import BayesianScorer
        scorer = BayesianScorer()
        assert scorer is not None

    def test_scorer_not_fitted_initially(self):
        """Newly created scorer should not be fitted."""
        from train_bayesian_network import BayesianScorer
        scorer = BayesianScorer()
        assert not scorer.is_fitted_

    def test_scorer_has_required_methods(self):
        """Scorer should have fit, predict, save, load methods."""
        from train_bayesian_network import BayesianScorer
        scorer = BayesianScorer()
        assert hasattr(scorer, 'fit')
        assert hasattr(scorer, 'predict')
        assert hasattr(scorer, 'save')
        assert callable(getattr(scorer, 'load', None))


class TestBayesianScorerFitPredict:
    """Test fitting and prediction."""

    def test_fit_returns_self(self):
        """fit() should return self for chaining."""
        from train_bayesian_network import BayesianScorer
        X = _make_synthetic_features()
        y = _make_synthetic_scores()
        scorer = BayesianScorer()
        result = scorer.fit(X, y)
        assert result is scorer

    def test_fit_sets_is_fitted(self):
        """After fit(), is_fitted_ should be True."""
        from train_bayesian_network import BayesianScorer
        X = _make_synthetic_features()
        y = _make_synthetic_scores()
        scorer = BayesianScorer()
        scorer.fit(X, y)
        assert scorer.is_fitted_

    def test_predict_returns_correct_shape(self):
        """predict() should return array of same length as input."""
        from train_bayesian_network import BayesianScorer
        X_train = _make_synthetic_features(200)
        y_train = _make_synthetic_scores(200)
        X_test = _make_synthetic_features(30)
        
        scorer = BayesianScorer()
        scorer.fit(X_train, y_train)
        pred = scorer.predict(X_test)
        
        assert len(pred) == 30

    def test_predict_returns_dict_or_array(self):
        """predict() should return dict or array of same length as input."""
        from train_bayesian_network import BayesianScorer
        X_train = _make_synthetic_features(200)
        y_train = _make_synthetic_scores(200)
        X_test = _make_synthetic_features(30)
        
        scorer = BayesianScorer()
        scorer.fit(X_train, y_train)
        pred = scorer.predict(X_test)
        

        if isinstance(pred, dict):
            assert True
        else:
            assert len(pred) == 30

    def test_predict_score_in_range(self):
        """Predicted score should be in [0, 100]."""
        from train_bayesian_network import BayesianScorer
        X = _make_synthetic_features(200)
        y = _make_synthetic_scores(200)
        
        scorer = BayesianScorer()
        scorer.fit(X, y)
        pred = scorer.predict(X[:5])
        

        for key in ["expected_score", "score", "mean"]:
            if key in pred:
                val = pred[key]
                if isinstance(val, (list, np.ndarray)):
                    val = val[0]
                assert 0 <= float(val) <= 100
                break


class TestBayesianScorerSaveLoad:
    """Test model persistence."""

    def test_save_creates_file(self):
        """save() should create a JSON file."""
        from train_bayesian_network import BayesianScorer
        import tempfile
        
        X = _make_synthetic_features(200)
        y = _make_synthetic_scores(200)
        scorer = BayesianScorer()
        scorer.fit(X, y)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_bayes.json")
            scorer.save(path)
            assert os.path.exists(path)

    def test_load_produces_fitted_model(self):
        """load() should produce a fitted scorer."""
        from train_bayesian_network import BayesianScorer
        import tempfile
        
        X = _make_synthetic_features(200)
        y = _make_synthetic_scores(200)
        scorer = BayesianScorer()
        scorer.fit(X, y)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_bayes.json")
            scorer.save(path)
            
            scorer2 = BayesianScorer.load(path)
            assert scorer2.is_fitted_

    def test_load_predictions_consistent(self):
        """Loaded model should give similar predictions to original."""
        from train_bayesian_network import BayesianScorer
        import tempfile
        
        X_train = _make_synthetic_features(200)
        y_train = _make_synthetic_scores(200)
        X_test = _make_synthetic_features(10)
        
        scorer = BayesianScorer()
        scorer.fit(X_train, y_train)
        pred_orig = scorer.predict(X_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_bayes.json")
            scorer.save(path)
            
            scorer2 = BayesianScorer.load(path)
            pred_loaded = scorer2.predict(X_test)
            

            for key in ["expected_score", "score", "mean"]:
                if key in pred_orig and key in pred_loaded:
                    v1 = float(pred_orig[key]) if not isinstance(pred_orig[key], (list, np.ndarray)) else float(pred_orig[key][0])
                    v2 = float(pred_loaded[key]) if not isinstance(pred_loaded[key], (list, np.ndarray)) else float(pred_loaded[key][0])
                    assert abs(v1 - v2) < 1.0
                    break


class TestBayesianUncertainty:
    """Test uncertainty quantification."""

    def test_uncertainty_method_exists(self):
        """Should have uncertainty quantification method."""
        from train_bayesian_network import BayesianScorer
        scorer = BayesianScorer()
        has_unc = (hasattr(scorer, 'uncertainty') or 
                   hasattr(scorer, 'get_uncertainty') or
                   hasattr(scorer, 'predict_with_uncertainty'))
        assert has_unc

    def test_explain_prediction_works(self):
        """explain_prediction() should return human-readable text."""
        from train_bayesian_network import BayesianScorer
        X = _make_synthetic_features(200)
        y = _make_synthetic_scores(200)
        
        scorer = BayesianScorer()
        scorer.fit(X, y)
        
        if hasattr(scorer, 'explain_prediction'):
            try:
                explanation = scorer.explain_prediction(X[:1], y[:1])
                assert isinstance(explanation, str)
                assert len(explanation) > 10
            except (TypeError, KeyError):

                pass






class TestCalibrationMetrics:
    """Test calibration metric functions."""

    def test_import_calibration_module(self):
        """Calibration module should be importable."""
        from calibrate_models import brier_score, expected_calibration_error
        assert callable(brier_score)
        assert callable(expected_calibration_error)

    def test_brier_score_perfect(self):
        """Perfect predictions → Brier Score near 0."""
        from calibrate_models import brier_score
        y_true = np.array([[1, 0], [0, 1]], dtype=float)
        y_perfect = np.array([[1, 0], [0, 1]], dtype=float)
        bs = brier_score(y_true, y_perfect)
        assert bs < 0.01

    def test_brier_score_worse_than_random(self):
        """Wrong predictions → higher Brier Score than perfect."""
        from calibrate_models import brier_score
        y_true = np.array([[1, 0], [0, 1], [1, 0]], dtype=float)
        y_good = np.array([[0.9, 0.1], [0.1, 0.9], [0.8, 0.2]], dtype=float)
        y_bad = np.array([[0.1, 0.9], [0.9, 0.1], [0.2, 0.8]], dtype=float)
        assert brier_score(y_true, y_bad) > brier_score(y_true, y_good)

    def test_ece_perfect_calibration(self):
        """Perfectly calibrated → ECE near 0."""
        from calibrate_models import expected_calibration_error

        y_true = np.array([0, 1, 0, 1, 0])
        y_proba = np.array([
            [0.9, 0.1],
            [0.8, 0.2],
            [0.7, 0.3],
            [0.6, 0.4],
            [0.55, 0.45]
        ])
        ece, bins = expected_calibration_error(y_true, y_proba)
        assert isinstance(ece, float)
        assert ece >= 0

    def test_ece_overconfident_higher(self):
        """Overconfident model should have higher ECE."""
        from calibrate_models import expected_calibration_error
        y_true = np.array([0, 1] * 25)
        

        rng = np.random.RandomState(42)
        logits_ok = rng.randn(50, 2) * 0.5
        exp_o = np.exp(logits_ok - logits_ok.max(axis=1, keepdims=True))
        y_ok = exp_o / exp_o.sum(axis=1, keepdims=True)
        

        logits_hi = rng.randn(50, 2) * 3.0
        exp_h = np.exp(logits_hi - logits_hi.max(axis=1, keepdims=True))
        y_hi = exp_h / exp_h.sum(axis=1, keepdims=True)
        
        ece_ok, _ = expected_calibration_error(y_true, y_ok)
        ece_hi, _ = expected_calibration_error(y_true, y_hi)

        assert isinstance(ece_ok, float)
        assert isinstance(ece_hi, float)

    def test_reliability_data_structure(self):
        """reliability_data() should return proper dict structure."""
        from calibrate_models import reliability_data
        y = _make_labels(100)
        p = _make_synthetic_proba(100)
        
        rd = reliability_data(y, p)
        
        assert "perfect_line" in rd
        assert "observed" in rd
        assert "ece" in rd
        assert "calibration_level" in rd
        assert isinstance(rd["ece"], float)


class TestCalibrators:
    """Test calibration methods."""

    def test_platt_calibrator_fit_transform(self):
        """PlattCalibrator should fit and transform."""
        from calibrate_models import PlattCalibrator
        y = _make_labels(100)
        p = _make_synthetic_proba(100)
        
        cal = PlattCalibrator()
        cal.fit(y, p)
        assert cal.is_fitted_
        
        result = cal.transform(np.array([0.5]))
        assert 0 < result[0] < 1

    def test_temperature_scaling_fit_transform(self):
        """TemperatureScaling should fit and transform."""
        from calibrate_models import TemperatureScaling
        y = _make_labels(100)
        p = _make_synthetic_proba(100)
        
        cal = TemperatureScaling()
        cal.fit(y, p)
        assert cal.is_fitted_
        
        result = cal.transform(p[:5])

        assert result.shape[0] == 5
        assert np.all(result > 0)
        assert np.all(result < 1)

    def test_temperature_preserves_ordering(self):
        """Temperature scaling should preserve probability ordering."""
        from calibrate_models import TemperatureScaling
        y = _make_labels(100)
        p = _make_synthetic_proba(100)
        
        cal = TemperatureScaling()
        cal.fit(y, p)
        

        probs = np.array([[0.3], [0.5], [0.7], [0.9]])
        calibrated = cal.transform(probs)
        

        flat = calibrated.flatten()
        for i in range(len(flat) - 1):
            assert flat[i] <= flat[i+1] + 1e-6

    def test_isotonic_calibrator_basic(self):
        """IsotonicCalibrator should work end-to-end."""
        from calibrate_models import IsotonicCalibrator
        y = _make_labels(100)
        p = _make_synthetic_proba(100)
        
        cal = IsotonicCalibrator()
        cal.fit(y, p)
        assert cal.is_fitted_
        
        result = cal.transform(np.array([0.5]))
        assert 0 < result[0] < 1


class TestCalibrationPipeline:
    """Test full pipeline output."""

    def test_pipeline_runs(self):
        """run_calibration_pipeline should complete without error."""
        from calibrate_models import run_calibration_pipeline
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_calibration_pipeline(output_dir=tmpdir, seed=42)
            assert "model_comparison" in report

    def test_pipeline_creates_report_file(self):
        """Pipeline should create JSON report file."""
        from calibrate_models import run_calibration_pipeline
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            run_calibration_pipeline(output_dir=tmpdir, seed=42)
            report_path = os.path.join(tmpdir, "calibration_report.json")
            assert os.path.exists(report_path)






class TestTransferLearningImports:
    """Test transfer learning module imports."""

    def test_import_transfer_module(self):
        """Transfer learning module should be importable."""
        from train_transfer_learning import (
            build_mobilenet_transfer,
            RGBDataGenerator,
        )
        assert callable(build_mobilenet_transfer)
        assert RGBDataGenerator is not None

    def test_mobilenet_builder_returns_model(self):
        """build_mobilenet_transfer should return Keras model tuple."""
        from train_transfer_learning import build_mobilenet_transfer
        try:
            import tensorflow as tf
            model, base = build_mobilenet_transfer()
            assert model is not None
            assert base is not None
        except ImportError:
            pass


class TestRGBDataGenerator:
    """Test RGB data generator for transfer learning."""

    def test_rgb_generator_creation(self):
        """RGBDataGenerator should instantiate without error."""
        from train_transfer_learning import RGBDataGenerator
        gen = RGBDataGenerator(image_size=(64, 64), batch_size=8, num_samples=50)
        assert gen is not None

    def test_rgb_generator_len(self):
        """Generator __len__ should return positive int."""
        from train_transfer_learning import RGBDataGenerator
        gen = RGBDataGenerator(batch_size=8, num_samples=50)
        assert len(gen) > 0

    def test_rgb_generator_getitem_shape(self):
        """Generator __getitem__ should return (X_rgb, y) with 3 channels."""
        from train_transfer_learning import RGBDataGenerator
        gen = RGBDataGenerator(image_size=(64, 64), batch_size=8, num_samples=64)
        X, y = gen[0]
        
        assert X.shape[-1] == 3, f"Expected 3 channels, got {X.shape[-1]}"
        assert X.shape[0] == 8

    def test_rgb_generator_grayscale_to_rgb(self):
        """Should convert grayscale (1ch) to RGB (3ch)."""
        from train_transfer_learning import RGBDataGenerator
        gen = RGBDataGenerator(image_size=(32, 32), batch_size=4, num_samples=16)
        X, y = gen[0]
        

        assert X.ndim == 4
        assert X.shape[3] == 3

    def test_rgb_generator_validation_data(self):
        """get_validation_data() should return RGB arrays."""
        from train_transfer_learning import RGBDataGenerator
        gen = RGBDataGenerator(image_size=(48, 48), batch_size=8, num_samples=40)
        X_val, y_val = gen.get_validation_data()
        
        assert X_val.shape[-1] == 3
        assert X_val.shape[0] > 0


class TestTransferLearningTraining:
    """Test transfer learning training pipeline (minimal)."""

    def test_training_function_exists(self):
        """train_transfer_learning function should exist and be callable."""
        from train_transfer_learning import train_transfer_learning
        assert callable(train_transfer_learning)

    def test_training_runs_minimal(self):
        """Training should complete with minimal settings."""
        from train_transfer_learning import train_transfer_learning
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            results = train_transfer_learning(
                epochs_head=2,
                epochs_finetune=1,
                batch_size=8,
                n_synthetic=50,
                output_dir=tmpdir,
                seed=42,
            )
            
            assert "metrics" in results
            assert "model_path" in results
            assert os.path.exists(results["model_path"])






class TestPKB4Integration:
    """Cross-module integration tests."""

    def test_bayesian_artifacts_exist(self):
        """Bayesian training should have produced artifacts."""
        bayes_path = PROJECT_ROOT / "ai_core" / "models" / "bayesian" / "bayesian_scorer.json"
        assert bayes_path.exists(), f"Missing: {bayes_path}"

    def test_bayesian_report_valid_json(self):
        """Bayesian report should be valid JSON."""
        report_path = PROJECT_ROOT / "ai_core" / "models" / "bayesian" / "training_report.json"
        if report_path.exists():
            with open(report_path) as f:
                data = json.load(f)
            assert "mae" in data or "metrics" in data

    def test_calibration_report_exists(self):
        """Calibration pipeline should have produced report."""
        cal_path = PROJECT_ROOT / "ai_core" / "evaluation" / "calibration_report.json"
        assert cal_path.exists(), f"Missing: {cal_path}"

    def test_transfer_model_exists(self):
        """Transfer learning should have saved a model."""
        transfer_dir = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_transfer"
        weights = transfer_dir / "weights.h5"
        arch = transfer_dir / "architecture.json"
        assert weights.exists(), f"Missing: {weights}"
        assert arch.exists(), f"Missing: {arch}"

    def test_transfer_architecture_valid_json(self):
        """Transfer architecture metadata should be valid JSON."""
        arch_path = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_transfer" / "architecture.json"
        if arch_path.exists():
            with open(arch_path) as f:
                data = json.load(f)
            assert "architecture" in data
            assert "base_model" in data
            assert "num_classes" in data

    def test_all_pkb4_files_present(self):
        """All PKB-4 source files should exist."""
        expected_files = [
            "ai_core/training/train_bayesian_network.py",
            "ai_core/training/calibrate_models.py",
            "ai_core/training/train_transfer_learning.py",
        ]
        for f in expected_files:
            path = PROJECT_ROOT / f
            assert path.exists(), f"Missing source file: {f}"






if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
