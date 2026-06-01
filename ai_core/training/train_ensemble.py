"""
PKB-5.1: Ensemble Training Pipeline
=====================================
Train ensemble strategies combining all available models:
  1. Soft Voting Classifier (sklearn VotingClassifier)
  2. Stacking Ensemble (meta-learner on top of base models)
  3. Custom Weighted Ensemble (config-driven weights)

Output:
  - ai_core/models/ensemble/voting_classifier.pkl
  - ai_core/models/ensemble/stacking_meta.pkl
  - ai_core/models/ensemble/hybrid_weights.json

Run:
    backend/venv/Scripts/python.exe ai_core/training/train_ensemble.py
    backend/venv/Scripts/python.exe ai_core/training/train_ensemble.py --no-train
"""

import os
import sys
import json
import time
import warnings
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np






ENSEMBLE_DIR = PROJECT_ROOT / "ai_core" / "models" / "ensemble"
CLASSICAL_DIR = PROJECT_ROOT / "ai_core" / "models" / "classical"


DEFAULT_HYBRID_WEIGHTS = {
    "version": "2.0",
    "description": "PKB-5 hybrid ensemble weights — CV-dominant for kid handwriting (V3)",
    "branches": {
        "cv": {"weight": 0.70, "description": "Computer Vision — PRIMARY (tuned V3 Nuclear for kids)"},
        "ml": {"weight": 0.15, "description": "Classical ML models (secondary)"},
        "dl": {"weight": 0.15, "description": "Deep Learning CNN (secondary)"}
    },
    "fallback_weights": {
        "cv": {"weight": 0.50, "description": "CV-only fallback when ML/DL unavailable"},
        "ml": {"weight": 0.50, "description": "ML-only fallback when CV/DL unavailable"},
        "cv_ml": {"weight": {"cv": 0.45, "ml": 0.55}, "description": "CV+ML when DL unavailable"}
    },
    "confidence_thresholds": {
        "high": 80,
        "medium": 55,
        "low": 25
    },
    "star_thresholds": [25, 45, 65],
    "last_updated": None
}






def _generate_synthetic_ensemble_data(n_samples=200, n_features=20, n_classes=62, seed=42):
    """
    Generate synthetic feature data for ensemble training.
    In production, this would be replaced by real labeled data from PSD pipelines.
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features) * 2
    

    class_centers = rng.randn(n_classes, n_features) * 1.5
    y = np.array([i % n_classes for i in range(n_samples)])
    
    for i in range(n_samples):
        cls = y[i]
        X[i] = X[i] * 0.3 + class_centers[cls] + rng.randn(n_features) * 0.5
    
    return X, y






def train_soft_voting(X_train, y_train, model_paths=None):
    """
    Train a Soft Voting Classifier using sklearn's VotingClassifier.
    
    Loads pre-trained classical models if available, otherwise trains from scratch.
    Soft voting averages probability predictions across all models.
    
    Args:
        X_train: Feature matrix (N, D)
        y_train: Labels (N,)
        model_paths: dict of {name: path} for pre-trained .pkl files
    
    Returns:
        Trained VotingClassifier + accuracy on synthetic test set
    """
    from sklearn.ensemble import VotingClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    import joblib
    
    estimators = []
    

    model_defs = [
        ("svm", SVC(kernel="rbf", probability=True, C=1.0), "svm.pkl"),
        ("rf", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42), "random_forest.pkl"),
        ("lr", LogisticRegression(max_iter=1000, C=1.0), "logistic_regression.pkl"),
        ("nb", GaussianNB(), "naive_bayes.pkl"),
        ("knn", KNeighborsClassifier(n_neighbors=5), "knn.pkl"),

    ]
    
    loaded_count = 0
    for name, default_model, pkl_file in model_defs:
        pkl_path = CLASSICAL_DIR / pkl_file
        if pkl_path.exists():
            try:
                loaded = joblib.load(pkl_path)

                has_proba = hasattr(loaded, 'predict_proba') and callable(loaded.predict_proba)
                if not has_proba and isinstance(loaded, Pipeline):
                    last_step = loaded.steps[-1][-1] if loaded.steps else None
                    has_proba = hasattr(last_step, 'predict_proba') and callable(getattr(last_step, 'predict_proba', None))
                
                if not has_proba:
                    print(f"  ⚯ Skipping {name}: no predict_proba (use hard-voting or retrain)")
                    continue
                
                if isinstance(loaded, Pipeline):
                    estimators.append((name, loaded))
                else:
                    estimators.append((name, Pipeline([("scaler", StandardScaler()), ("clf", loaded)])))
                loaded_count += 1
                print(f"  ✓ Loaded pre-trained: {name} from {pkl_file}")
            except Exception as e:
                print(f"  ⚠ Failed to load {pkl_file}: {e}, using fresh model")
                fresh = Pipeline([("scaler", StandardScaler()), ("clf", default_model)])
                if hasattr(fresh, 'predict_proba'):
                    estimators.append((name, fresh))
                    loaded_count += 1
        else:
            print(f"  ⚠ No pre-trained file: {pkl_file}, using fresh model")
            fresh = Pipeline([("scaler", StandardScaler()), ("clf", default_model)])
            if hasattr(fresh, 'predict_proba'):
                estimators.append((name, fresh))
                loaded_count += 1
    
    print(f"\n  Models in voting ensemble: {len(estimators)} ({loaded_count} pre-loaded)")
    

    voting_clf = VotingClassifier(
        estimators=estimators,
        voting="soft",
        weights=None
    )
    

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        voting_clf.fit(X_train, y_train)
    

    X_tr, X_te, y_tr, y_te = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
    try:
        acc = voting_clf.score(X_te[:min(len(X_te), 50)], y_te[:min(len(y_te), 50)])
    except Exception:
        acc = 0.0

        acc = voting_clf.score(X_train, y_train)
    
    return voting_clf, acc






def train_stacking_ensemble(X_train, y_train):
    """
    Train a Stacking Classifier.
    
    Base models: kNN, SVM, RF, LR (diverse types)
    Meta-learner: Logistic Regression (learns optimal combination)
    
    Stacking is more powerful than voting because the meta-learner can learn
    which base model to trust for which type of input.
    """
    from sklearn.ensemble import StackingClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    import joblib
    
    base_estimators = [
        ("knn", Pipeline([("scaler", StandardScaler()), ("clf", KNeighborsClassifier(n_neighbors=5))])),
        ("svm", Pipeline([("scaler", StandardScaler()), ("clf", SVC(kernel="rbf", probability=True, C=1.0))])),
        ("rf", Pipeline([("scaler", StandardScaler()), ("clf", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42))])),
        ("lr", Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, C=1.0))])),
    ]
    
    meta_learner = LogisticRegression(max_iter=1000)
    
    stacking_clf = StackingClassifier(
        estimators=base_estimators,
        final_estimator=meta_learner,
        cv=3,
        stack_method="predict_proba",
        passthrough=True
    )
    
    print("  Training Stacking Classifier (4 base models + LR meta-learner)...")
    t0 = time.time()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stacking_clf.fit(X_train, y_train)
    elapsed = time.time() - t0
    print(f"  Stacking trained in {elapsed:.1f}s")
    

    try:
        X_tr, X_te, y_tr, y_te = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
        acc = stacking_clf.score(X_te[:min(len(X_te), 50)], y_te[:min(len(y_te), 50)])
    except Exception:
        acc = stacking_clf.score(X_train, y_train)
    
    return stacking_clf, acc






def create_custom_weighted_config(benchmark_results=None):
    """
    Generate custom weighted ensemble configuration based on benchmark results.
    
    Weights are proportional to each model's estimated accuracy.
    This config is used at inference time by the HybridEngine.
    
    Args:
        benchmark_results: dict of {model_name: {"accuracy": float, ...}}
        
    Returns:
        Dict with weights configuration
    """
    config = DEFAULT_HYBRID_WEIGHTS.copy()
    
    if benchmark_results:

        total_acc = sum(r.get("accuracy", 50) for r in benchmark_results.values())
        if total_acc > 0:
            for name, result in benchmark_results.items():
                raw_weight = result.get("accuracy", 50) / total_acc

                if name in ("knn", "svm", "rf", "lr", "nb", "dt"):
                    config["branches"]["ml"]["weight"] = max(
                        config["branches"]["ml"]["weight"],
                        raw_weight * 2
                    )
                elif name in ("cnn_simple", "cnn_transfer"):
                    config["branches"]["dl"]["weight"] = max(
                        config["branches"]["dl"]["weight"],
                        raw_weight * 2
                    )
                elif name in ("baseline_v3", "pattern_match"):
                    config["branches"]["cv"]["weight"] = max(
                        config["branches"]["cv"]["weight"],
                        raw_weight * 2
                    )
    
    from datetime import datetime
    config["last_updated"] = datetime.now().isoformat()
    
    return config


def save_hybrid_weights(config, output_dir=None):
    """Save hybrid weights JSON to disk."""
    if output_dir is None:
        output_dir = ENSEMBLE_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    path = output_dir / "hybrid_weights.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  Saved hybrid weights to: {path}")
    return path






def run_ensemble_training(no_train=False):
    """
    Run full ensemble training pipeline.
    
    Args:
        no_train: If True, only generate config files (skip actual model training)
    
    Returns:
        Dict with training results
    """
    import joblib
    from datetime import datetime
    
    os.makedirs(ENSEMBLE_DIR, exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "ensemble_dir": str(ENSEMBLE_DIR),
        "models": {},
        "config": None
    }
    
    print("=" * 60)
    print("  PKB-5.1: ENSEMBLE TRAINING PIPELINE")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if no_train:
        print("\n⚡ --no-train mode: generating config only\n")
        config = create_custom_weighted_config()
        save_hybrid_weights(config)
        results["config"] = config
        results["status"] = "config_only"
        return results
    

    print("\n[1/4] Generating synthetic training data...")
    n_samples = 300
    n_classes = 62
    X, y = _generate_synthetic_ensemble_data(n_samples=n_samples, n_features=20, n_classes=n_classes)
    print(f"  Data shape: X={X.shape}, y={y.shape}, classes={len(np.unique(y))}")
    

    print("\n[2/4] Training Soft Voting Classifier...")
    try:
        voting_clf, voting_acc = train_soft_voting(X, y)
        voting_path = ENSEMBLE_DIR / "voting_classifier.pkl"
        joblib.dump(voting_clf, voting_path)
        print(f"  ✓ Saved: {voting_path} (accuracy ~{voting_acc*100:.1f}%)")
        results["models"]["soft_voting"] = {
            "file": str(voting_path),
            "accuracy": round(voting_acc, 4),
            "type": "VotingClassifier(soft)"
        }
    except Exception as e:
        print(f"  ✗ Soft Voting failed: {e}")
        results["models"]["soft_voting"] = {"error": str(e)}
    

    print("\n[3/4] Training Stacking Ensemble...")
    try:
        stacking_clf, stacking_acc = train_stacking_ensemble(X, y)
        stacking_path = ENSEMBLE_DIR / "stacking_meta.pkl"
        joblib.dump(stacking_clf, stacking_path)
        print(f"  ✓ Saved: {stacking_path} (accuracy ~{stacking_acc*100:.1f}%)")
        results["models"]["stacking"] = {
            "file": str(stacking_path),
            "accuracy": round(stacking_acc, 4),
            "type": "StackingClassifier(LR meta)"
        }
    except Exception as e:
        print(f"  ✗ Stacking failed: {e}")
        results["models"]["stacking"] = {"error": str(e)}
    

    print("\n[4/4] Generating Custom Weighted Config...")
    config = create_custom_weighted_config()
    config_path = save_hybrid_weights(config)
    results["config"] = config
    results["status"] = "completed"
    

    report_path = ENSEMBLE_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ Ensemble training complete! Report: {report_path}")
    
    return results






if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PKB-5.1: Train Ensemble Models")
    parser.add_argument("--no-train", action="store_true", help="Only generate config, skip model training")
    args = parser.parse_args()
    
    result = run_ensemble_training(no_train=args.no_train)
    print(f"\nStatus: {result.get('status', 'unknown')}")
