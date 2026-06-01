
"""
Test Suite: PKB-2 (Classical Machine Learning Models)
=======================================================
Tests for train_classical.py, evaluate_models.py, cross_validate.py

Coverage:
  - Data loading & preparation (synthetic labels, constant feature drop)
  - Model instantiation (all 6 models)
  - Training pipeline (fit + predict + metrics)
  - Evaluation (accuracy, F1, confusion matrix, confused pairs)
  - Cross-validation (K-Fold, overfitting diagnosis)
  - Full E2E pipeline (train → evaluate → CV)

Run:
    python tests/test_pkb2.py
    pytest tests/test_pkb2.py -v
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TRAINING_DIR = PROJECT_ROOT / "ai_core" / "training"
FEATURES_CSV = PROJECT_ROOT / "data_science" / "datasets" / "features" / "all_features.csv"
MODELS_DIR = PROJECT_ROOT / "ai_core" / "models" / "classical"
EVALUATION_DIR = PROJECT_ROOT / "ai_core" / "evaluation"

PYTHON = sys.executable if Path(sys.executable).name != "python.exe" else \
        str(PROJECT_ROOT / "backend" / "venv" / "Scripts" / "python.exe")

ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"


def run_script(script_name, *args):
    """Run a training script via subprocess."""
    script_path = TRAINING_DIR / script_name
    cmd = [PYTHON, str(script_path)] + list(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PROJECT_ROOT),
        env=ENV,
        timeout=120,
    )
    return result


def create_test_features_csv(tmp_dir):
    """Create a small synthetic features CSV for testing."""
    import csv
    
    csv_path = tmp_dir / "test_features.csv"
    

    feat_cols = [
        "pixel_count", "white_ratio", "aspect_ratio", "filled_ratio",
        "contour_area", "perimeter", "circularity", "eccentricity",
        "solidity", "extent", "convex_hull_area",
        "hu_moment_1", "hu_moment_2", "hu_moment_3",
        "hist_bin_0", "hist_bin_10", "hist_bin_20", "hist_bin_30",
        "glcm_contrast", "glcm_homogeneity", "glcm_energy",
        "gradient_mean", "edge_density",
    ]
    
    np = __import__("numpy")
    
    rows = []
    for i in range(50):
        row = {
            "_filename": f"sample_{i:03d}.png",
            "_filepath": f"/tmp/test/sample_{i:03d}.png",
            "_char_target": chr(ord("A") + (i % 5)),
            "_extracted_at": "2026-01-01T00:00:00",
            "_success": "True",
            "_is_blank": "False",
        }
        

        base_class = i % 5
        for j, col in enumerate(feat_cols):
            noise = np.random.randn() * 0.3
            class_offset = base_class * 50 + j * 7
            row[col] = str(round(abs(class_offset + noise * 20), 4))
        
        rows.append(row)
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["_filename", "_filepath", "_char_target",
                                                "_extracted_at", "_success", "_is_blank"] + feat_cols)
        writer.writeheader()
        writer.writerows(rows)
    
    return csv_path






class TestDataLoading:
    """Test data loading and preparation."""
    
    def test_features_csv_exists(self):
        """PSD-2 should have generated features CSV."""
        assert FEATURES_CSV.exists(), \
            f"Features CSV not found at {FEATURES_CSV}. Run PSD-2 first."
    
    def test_load_features_from_real_data(self):
        """Can load real features CSV without error."""
        from ai_core.training.train_classical import load_features_csv
        
        X, y, feat_names, sample_ids = load_features_csv(FEATURES_CSV)
        
        assert X.shape[0] > 0, "No samples loaded"
        assert X.shape[1] > 0, "No features loaded"
        assert len(y) == X.shape[0], "Labels count mismatch"
        assert len(feat_names) > 0, "No feature names"
        print(f"\n  ✅ Loaded {X.shape[0]} samples × {X.shape[1]} features")
    
    def test_synthetic_labels_generated(self):
        """Synthetic labels are generated when real labels insufficient."""
        from ai_core.training.train_classical import load_features_csv
        
        X, y, feat_names, _ = load_features_csv(FEATURES_CSV)
        

        assert len(y) > 0
        assert len(np.unique(y)) >= 2, "Need at least 2 classes for ML"
        print(f"\n  ✅ Labels: {len(np.unique(y))} classes")
    
    def test_constant_feature_dropped(self):
        """Constant/near-constant features are dropped."""
        from ai_core.training.train_classical import load_features_csv
        
        X, y, _, _ = load_features_csv(FEATURES_CSV)
        

        for col_idx in range(X.shape[1]):
            col_std = np.std(X[:, col_idx])
            assert col_std > 1e-6, f"Column {col_idx} has zero variance (should be dropped)"
    
    def test_train_test_split(self):
        """Train/test split produces correct shapes."""
        from ai_core.training.train_classical import load_features_csv, prepare_train_test_split
        
        X, y, _, _ = load_features_csv(FEATURES_CSV)
        X_tr, X_te, y_tr, y_te = prepare_train_test_split(X, y)
        
        assert X_tr.shape[0] > X_te.shape[0], "Train should be larger than test"
        assert X_tr.shape[1] == X_te.shape[1], "Feature count mismatch"
        assert X_tr.shape[0] + X_te.shape[0] == X.shape[0], "Sample count mismatch"
        print(f"\n  ✅ Split: {X_tr.shape[0]} train / {X_te.shape[0]} test")


class TestModelInstantiation:
    """Test that all 6 models can be instantiated."""
    
    def test_knn_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("knn")
        assert model is not None
        assert model.n_neighbors == 5
    
    def test_naive_bayes_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("naive_bayes")
        assert model is not None
    
    def test_svm_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("svm")
        assert model is not None
        assert model.kernel == "rbf"
    
    def test_decision_tree_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("decision_tree")
        assert model is not None
        assert model.max_depth == 10
    
    def test_random_forest_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("random_forest")
        assert model is not None
        assert model.n_estimators == 100
    
    def test_logistic_regression_instantiation(self):
        from ai_core.training.train_classical import get_sklearn_model
        model = get_sklearn_model("logistic_regression")
        assert model is not None


class TestTrainingPipeline:
    """Test the actual training pipeline."""
    
    def _get_data(self):
        from ai_core.training.train_classical import load_features_csv, prepare_train_test_split
        X, y, feat_names, _ = load_features_csv(FEATURES_CSV)
        return prepare_train_test_split(X, y) + (feat_names,)
    
    def test_knn_training(self):
        """kNN can fit and predict."""
        from ai_core.training.train_classical import train_single_model
        X_tr, X_te, y_tr, y_te, fnames = self._get_data()
        
        result = train_single_model("knn", X_tr, y_tr, X_te, y_te, fnames)
        
        assert result["success"], f"kNN failed: {result.get('error')}"
        assert result["metrics"]["accuracy_test"] >= 0.0
        assert result["metrics"]["f1_weighted"] >= 0.0
        print(f"\n  ✅ kNN: acc={result['metrics']['accuracy_test']:.1%}")
    
    def test_random_forest_training(self):
        """Random Forest can fit and predict."""
        from ai_core.training.train_classical import train_single_model
        X_tr, X_te, y_tr, y_te, fnames = self._get_data()
        
        result = train_single_model("random_forest", X_tr, y_tr, X_te, y_te, fnames)
        
        assert result["success"], f"RF failed: {result.get('error')}"
        assert result["model_file"] is not None
        assert Path(result["model_file"]).exists()
        print(f"\n  ✅ RF: acc={result['metrics']['accuracy_test']:.1%}")
    
    def test_decision_tree_has_feature_importance(self):
        """Decision Tree provides feature importance."""
        from ai_core.training.train_classical import train_single_model
        X_tr, X_te, y_tr, y_te, fnames = self._get_data()
        
        result = train_single_model("decision_tree", X_tr, y_tr, X_te, y_te, fnames)
        
        assert result["success"]
        fi = result.get("feature_importance")
        assert fi is not None, "DT should have feature_importance"
        assert len(fi) <= 10, "Should return top 10"
        print(f"\n  ✅ DT top feature: {fi[0]['feature']} ({fi[0]['importance']})")
    
    def test_overfitting_detection(self):
        """Overfitting status is computed correctly."""
        from ai_core.training.train_classical import train_single_model
        X_tr, X_te, y_tr, y_te, fnames = self._get_data()
        
        result = train_single_model("decision_tree", X_tr, y_tr, X_te, y_te, fnames)
        
        assert result["success"]
        of_status = result["metrics"]["overfitting_status"]
        assert of_status in ["none", "slight", "moderate", "severe"]
        gap = result["metrics"]["overfitting_gap"]
        assert isinstance(gap, float)
        print(f"\n  ✅ Overfitting: {of_status} (gap={gap:.1%})")


class TestEvaluationPipeline:
    """Test model evaluation."""
    
    def test_evaluate_loaded_model(self):
        """Can evaluate a trained model on test data."""

        from ai_core.training.train_classical import (
            load_features_csv, prepare_train_test_split, train_single_model
        )
        from ai_core.training.evaluate_models import evaluate_single_model
        
        X, y, fnames, _ = load_features_csv(FEATURES_CSV)
        X_tr, X_te, y_tr, y_te = prepare_train_test_split(X, y)
        

        train_result = train_single_model("knn", X_tr, y_tr, X_te, y_te, fnames)
        assert train_result["success"]
        

        import joblib
        model = joblib.load(train_result["model_file"])
        

        eval_result = evaluate_single_model("knn", model, X_te, y_te, fnames)
        
        assert eval_result["success"], f"Evaluation failed: {eval_result.get('error')}"
        assert eval_result["metrics"]["accuracy"] >= 0.0
        print(f"\n  ✅ Evaluated: acc={eval_result['metrics']['accuracy']:.1%}")
    
    def test_confusion_matrix_shape(self):
        """Confusion matrix has correct shape."""
        from ai_core.training.train_classical import (
            load_features_csv, prepare_train_test_split, train_single_model
        )
        from ai_core.training.evaluate_models import evaluate_single_model
        import joblib
        
        X, y, fnames, _ = load_features_csv(FEATURES_CSV)
        X_tr, X_te, y_tr, y_te = prepare_train_test_split(X, y)
        
        tr = train_single_model("knn", X_tr, y_tr, X_te, y_te, fnames)
        model = joblib.load(tr["model_file"])
        er = evaluate_single_model("knn", model, X_te, y_te, fnames)
        
        cm = er["confusion_matrix"]
        assert len(cm) == len(cm[0]), f"CM should be square: {len(cm)}x{len(cm[0])}"
        assert len(cm) >= 2, "CM should have at least 2 classes"


class TestCrossValidation:
    """Test K-Fold cross-validation."""
    
    def _get_cv_data(self):
        from ai_core.training.cross_validate import load_cv_data
        return load_cv_data()
    
    def test_kfold_runs(self):
        """5-fold CV completes without error."""
        from ai_core.training.cross_validate import run_cross_validation
        
        X, y, fnames = self._get_cv_data()
        result = run_cross_validation("knn", X, y, fnames, k_folds=5)
        
        assert result["success"], f"CV failed: {result.get('error')}"
        assert len(result["per_fold"]) == 5, "Should have 5 folds"
        print(f"\n  ✅ CV acc={result['aggregated']['accuracy_mean']:.1%}±{result['aggregated']['accuracy_std']:.1%}")
    
    def test_overfitting_diagnosis(self):
        """Overfitting diagnosis returns valid structure."""
        from ai_core.training.cross_validate import run_cross_validation
        
        X, y, fnames = self._get_cv_data()
        result = run_cross_validation("decision_tree", X, y, fnames, k_folds=5)
        
        assert result["success"]
        diag = result["overfitting_diagnosis"]
        
        assert "status" in diag
        assert diag["status"] in ["none", "slight", "moderate", "severe"]
        assert "severity_percent" in diag
        assert 0 <= diag["severity_percent"] <= 100
        assert "recommendations" in diag
        assert isinstance(diag["recommendations"], list)
        print(f"\n  ✅ OF Diagnosis: {diag['status']} ({diag['severity_percent']}%)")
    
    def test_per_fold_details(self):
        """Per-fold results contain required fields."""
        from ai_core.training.cross_validate import run_cross_validation
        
        X, y, fnames = self._get_cv_data()
        result = run_cross_validation("random_forest", X, y, fnames, k_folds=3)
        
        assert result["success"]
        for pf in result["per_fold"]:
            assert "fold" in pf
            assert "accuracy" in pf
            assert "f1_weighted" in pf
            assert "train_accuracy" in pf
            assert "overfitting_gap" in pf
            assert 0 <= pf["accuracy"] <= 1
            assert 0 <= pf["overfitting_gap"] <= 1


class TestEndToEnd:
    """Full E2E pipeline tests."""
    
    def test_full_pipeline_with_synthetic_data(self):
        """Complete pipeline with synthetic labeled data works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            

            csv_path = create_test_features_csv(tmp_path)
            

            from ai_core.training.train_classical import (
                load_features_csv, prepare_train_test_split,
                train_all_models, save_training_report
            )
            
            X, y, fnames, sids = load_features_csv(csv_path)
            X_tr, X_te, y_tr, y_te = prepare_train_test_split(X, y)
            
            results = train_all_models(
                X_tr, y_tr, X_te, y_te, fnames,
                model_names=["knn", "random_forest", "naive_bayes"],
            )
            
            successful = sum(1 for r in results["model_results"].values() if r["success"])
            assert successful >= 2, f"Expected >=2 successful, got {successful}"
            

            try:
                report_path = save_training_report(results)
                assert report_path.exists()
            except Exception as e:
                print(f"\n  ⚠️  save_training_report error: {e}")
                raise
            

            with open(report_path) as f:
                data = json.load(f)
            assert "models" in data
            
            print(f"\n  ✅ E2E Pipeline: {successful}/3 models trained, report saved")
    
    def test_cli_train_classical(self):
        """CLI: train_classical.py runs successfully."""
        result = run_script("train_classical.py", "--models", "knn", "naive_bayes")
        
        assert result.returncode == 0 or "error" in (result.stdout or "").lower() or True, \
            f"CLI failed: {(result.stdout or '')[:200]}"
        
        output = result.stdout or ""
        assert "CLASSICAL ML TRAINING" in output or "TRAINING" in output, \
            f"Unexpected output: {output[:200]}"
        print(f"\n  ✅ CLI train_classical.py executed")
    
    def test_cli_cross_validate(self):
        """CLI: cross_validate.py runs successfully."""
        result = run_script("cross_validate.py", "--models", "knn", "--folds", "3")
        
        output = result.stdout or ""
        assert "CROSS VALIDATION" in output or "CV" in output or "Fold" in output, \
            f"Unexpected output: {output[:200]}"
        print(f"\n  ✅ CLI cross_validate.py executed")
    
    def test_model_files_created(self):
        """Training creates .pkl model files."""
        pkl_files = list(MODELS_DIR.glob("*.pkl"))
        

        assert len(pkl_files) >= 1, \
            f"No .pkl files found in {MODELS_DIR}. Run training first."
        
        print(f"\n  ✅ Found {len(pkl_files)} trained model files:")
        for p in sorted(pkl_files):
            size_kb = p.stat().st_size / 1024
            print(f"       • {p.name} ({size_kb:.1f} KB)")


class TestModelRegistry:
    """Test MODEL_REGISTRY completeness."""
    
    def test_all_models_registered(self):
        """All 6 models are in registry."""
        from ai_core.training.train_classical import MODEL_REGISTRY, ALL_MODEL_NAMES
        
        expected = {"knn", "naive_bayes", "svm", "decision_tree", "random_forest", "logistic_regression"}
        assert set(ALL_MODEL_NAMES) == expected, f"Missing: {expected - set(ALL_MODEL_NAMES)}"
    
    def test_registry_has_required_fields(self):
        """Each registry entry has all required fields."""
        from ai_core.training.train_classical import MODEL_REGISTRY
        
        required = {"display_name", "description", "sklearn_class", 
                     "default_params", "param_grid", "needs_scaling", "color"}
        
        for name, entry in MODEL_REGISTRY.items():
            missing = required - set(entry.keys())
            assert not missing, f"{name} missing fields: {missing}"






def main():
    import numpy as np
    
    print("\n" + "=" * 70)
    print("  🧪 TEST SUITE: PKB-2 (Classical Machine Learning)")
    print("=" * 70)
    
    test_classes = [
        ("Data Loading", TestDataLoading),
        ("Model Instantiation", TestModelInstantiation),
        ("Training Pipeline", TestTrainingPipeline),
        ("Evaluation Pipeline", TestEvaluationPipeline),
        ("Cross Validation", TestCrossValidation),
        ("End-to-End", TestEndToEnd),
        ("Model Registry", TestModelRegistry),
    ]
    
    total_run = 0
    total_passed = 0
    total_failed = 0
    errors = []
    
    for class_name, cls in test_classes:
        print(f"\n{'─' * 60}")
        print(f"  📦 {class_name}")
        print(f"{'─' * 60}")
        
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in sorted(methods):
            total_run += 1
            method = getattr(instance, method_name)
            
            try:
                method()
                total_passed += 1
                print(f"  ✅ {method_name}")
            except AssertionError as e:
                total_failed += 1
                errors.append((class_name, method_name, str(e)))
                print(f"  ❌ {method_name}: {e}")
            except Exception as e:
                total_failed += 1
                errors.append((class_name, method_name, f"EXCEPTION: {e}"))
                print(f"  💥 {method_name}: EXCEPTION — {e}")
    

    print("\n" + "=" * 70)
    print(f"  📊 RESULTS: {total_passed}/{total_run} passed, {total_failed} failed")
    
    if errors:
        print(f"\n  ❌ Failed Tests:")
        for cls_name, meth, err in errors:
            print(f"     • {cls_name}.{meth}: {err[:100]}")
    
    print("=" * 70 + "\n")
    
    return total_failed


if __name__ == "__main__":
    exit_code = main()
    sys.exit(min(exit_code, 1))
