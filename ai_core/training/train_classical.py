
"""
PKB-2.1: Classical Machine Learning Training Pipeline
==========================================================
Trains 6 classical ML models for handwriting character classification.
Uses feature vectors extracted by PSD-2 (extract_features.py).

Models:
  1. k-Nearest Neighbors (kNN)     — Distance-based, simple, fast
  2. Naive Bayes (Gaussian)         — Probabilistic, P(class|features)
  3. Support Vector Machine (SVM)   — RBF kernel, high-dimensional
  4. Decision Tree                 — Interpretable, rule-based
  5. Random Forest                 — Ensemble of trees, robust
  6. Logistic Regression            — Linear baseline, multi-class

Usage:
    python train_classical.py
    python train_classical.py --input features/all_features.csv
    python train_classical.py --models knn svm rf
    python train_classical.py --cv 5
    python train_classical.py --grid-search

Author: Sahabat Aksara — PKB-2 Classical ML Pipeline
"""

import sys
import os
import json
import argparse
import logging
import time
import warnings
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any

import numpy as np


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data_science" / "datasets"
FEATURES_DIR = DATA_DIR / "features"
MODELS_DIR = PROJECT_ROOT / "ai_core" / "models" / "classical"
EXPORTS_DIR = DATA_DIR / "exports"
DEFAULT_FEATURES_CSV = FEATURES_DIR / "all_features.csv"


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("train")





MODEL_REGISTRY = {
    "knn": {
        "display_name": "k-Nearest Neighbors",
        "description": "Klasifikasi berdasarkan jarak ke tetangga terdekat di feature space",
        "sklearn_class": "KNeighborsClassifier",
        "default_params": {"n_neighbors": 5, "weights": "distance", "metric": "minkowski"},
        "param_grid": {
            "classifier__n_neighbors": [3, 5, 7, 11],
            "classifier__weights": ["uniform", "distance"],
        },
        "needs_scaling": True,
        "color": "#3498db",
    },
    "naive_bayes": {
        "display_name": "Naive Bayes (Gaussian)",
        "description": "Probabilistik: P(c|f₁,...,fₙ) ∝ P(c) × ∏P(fᵢ|c). Cepat & probabilistic.",
        "sklearn_class": "GaussianNB",
        "default_params": {"var_smoothing": 1e-9},
        "param_grid": {
            "classifier__var_smoothing": [1e-10, 1e-9, 1e-7, 1e-5, 1e-3],
        },
        "needs_scaling": False,
        "color": "#2ecc71",
    },
    "svm": {
        "display_name": "Support Vector Machine (RBF)",
        "description": "Hyperplane separator di high-dimensional space dengan kernel trick",
        "sklearn_class": "SVC",
        "default_params": {"kernel": "rbf", "C": 1.0, "gamma": "scale", "probability": False},
        "param_grid": {
            "classifier__C": [0.1, 1.0, 10.0],
            "classifier__gamma": ["scale", "auto", 0.01, 0.1],
        },
        "needs_scaling": True,
        "color": "#e74c3c",
    },
    "decision_tree": {
        "display_name": "Decision Tree",
        "description": "Aturan if-else otomatis. INTERPRETABLE! Bisa dieksport sebagai rules.",
        "sklearn_class": "DecisionTreeClassifier",
        "default_params": {"max_depth": 10, "criterion": "gini", "random_state": 42},
        "param_grid": {
            "classifier__max_depth": [5, 10, 15, None],
            "classifier__criterion": ["gini", "entropy"],
            "classifier__min_samples_split": [2, 5, 10],
        },
        "needs_scaling": False,
        "color": "#f39c12",
    },
    "random_forest": {
        "display_name": "Random Forest",
        "description": "Ensemble dari banyak decision tree. Robust & akurat untuk data kompleks.",
        "sklearn_class": "RandomForestClassifier",
        "default_params": {"n_estimators": 100, "max_depth": 10, "random_state": 42, "n_jobs": -1},
        "param_grid": {
            "classifier__n_estimators": [50, 100, 200],
            "classifier__max_depth": [5, 10, None],
            "classifier__min_samples_split": [2, 5],
        },
        "needs_scaling": False,
        "color": "#9b59b6",
    },
    "logistic_regression": {
        "display_name": "Logistic Regression",
        "description": "Baseline linear classifier. Multi-class softmax. Cepat & sederhana.",
        "sklearn_class": "LogisticRegression",
        "default_params": {"max_iter": 1000, "solver": "lbfgs", "random_state": 42},
        "param_grid": {
            "classifier__C": [0.1, 1.0, 10.0],
            "classifier__solver": ["lbfgs", "saga"],
        },
        "needs_scaling": True,
        "color": "#1abc9c",
    },
}

ALL_MODEL_NAMES = list(MODEL_REGISTRY.keys())


def get_sklearn_model(model_name: str):
    """Instantiate a scikit-learn model from registry."""
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.svm import SVC
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    class_map = {
        "knn": KNeighborsClassifier,
        "naive_bayes": GaussianNB,
        "svm": SVC,
        "decision_tree": DecisionTreeClassifier,
        "random_forest": RandomForestClassifier,
        "logistic_regression": LogisticRegression,
    }

    cls = class_map.get(model_name)
    if cls is None:
        raise ValueError(f"Unknown model: {model_name}")

    params = MODEL_REGISTRY[model_name]["default_params"].copy()
    return cls(**params)






def load_features_csv(csv_path: Path) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """
    Load features CSV and return (X, y, feature_names, sample_ids).
    
    Handles:
      - Missing labels → generate synthetic labels for testing
      - Non-numeric values → convert/replace with NaN
      - Constant features → drop (zero variance)
    """
    import csv as csv_mod
    
    rows = []
    fieldnames = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    
    if not rows:
        raise ValueError(f"No data in {csv_path}")
    

    meta_cols = ["_filename", "_filepath", "_char_target", "_extracted_at", "_success", "_is_blank"]
    feat_cols = [c for c in fieldnames if not c.startswith("_")]
    

    X_list = []
    y_list = []
    sample_ids = []
    
    for row in rows:

        sid = row.get("_filename", f"sample_{len(sample_ids)}")
        sample_ids.append(sid)
        

        label = row.get("_char_target", "").strip()
        

        feat_vec = []
        for col in feat_cols:
            val = row.get(col, "")
            try:
                feat_vec.append(float(val))
            except (ValueError, TypeError):
                feat_vec.append(np.nan)
        
        X_list.append(feat_vec)
        y_list.append(label)
    
    X = np.array(X_list, dtype=np.float64)
    

    y_raw = np.array(y_list)
    

    valid_labels = [l for l in y_raw if l and len(l) == 1 and (l.isalpha() or l.isdigit())]
    
    if len(valid_labels) < len(y_raw) * 0.5:

        log.warning(f"  ⚠️  Only {len(valid_labels)}/{len(y_raw)} samples have valid character labels.")
        log.info(f"  📝 Generating synthetic labels for training demonstration...")
        



        y_synthetic = _generate_synthetic_labels(X, sample_ids)
        y = y_synthetic
    else:

        unique_labels = sorted(set(valid_labels))
        label_to_idx = {l: i for i, l in enumerate(unique_labels)}
        y = np.array([label_to_idx.get(l, 0) for l in y_raw])
    

    constant_mask = []
    for col_idx in range(X.shape[1]):
        col = X[:, col_idx]
        valid = col[~np.isnan(col)]
        if len(valid) > 0 and np.std(valid) < 1e-6:
            constant_mask.append(col_idx)
    
    if constant_mask:
        log.info(f"  🔧 Dropping {len(constant_mask)} constant/near-constant features")
        X = np.delete(X, constant_mask, axis=1)
        feat_cols = [c for i, c in enumerate(feat_cols) if i not in constant_mask]
    

    nan_counts = np.isnan(X).sum(axis=0)
    cols_with_nan = np.where(nan_counts > 0)[0]
    
    if len(cols_with_nan) > 0:
        for col_idx in cols_with_nan:
            col_mean = np.nanmean(X[:, col_idx])
            mask = np.isnan(X[:, col_idx])
            X[mask, col_idx] = col_mean
    
    return X, y, feat_cols, sample_ids


def _generate_synthetic_labels(X: np.ndarray, sample_ids: List[str]) -> np.ndarray:
    """
    Generate synthetic character labels based on image feature clustering.
    
    This is a DEMO function — real training needs human-labeled data.
    Strategy: use pixel_count + aspect_ratio to simulate different characters.
    """
    n_samples = X.shape[0]
    

    CHARS = (
        list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") +
        list("abcdefghijklmnopqrstuvwxyz") +
        list("0123456789")
    )
    n_classes = len(CHARS)
    

    labels = []
    for i in range(n_samples):

        pixel_val = X[i, 0] if X.shape[1] > 0 else 0
        aspect_val = X[i, 2] if X.shape[1] > 2 else 0
        

        idx = int((pixel_val * 7 + aspect_val * 13 + i * 17)) % n_classes
        labels.append(CHARS[idx])
    
    return np.array(labels)


def prepare_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split data into train/test sets."""
    from sklearn.model_selection import train_test_split
    
    strat = y if stratify else None
    

    if stratify:
        unique, counts = np.unique(y, return_counts=True)
        if np.any(counts < 2):
            log.info(f"  ℹ️  Some classes have <2 samples, disabling stratified split")
            strat = None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=strat
    )
    
    return X_train, X_test, y_train, y_test






def train_single_model(
    model_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
    do_grid_search: bool = False,
    cv_folds: int = 5,
) -> Dict[str, Any]:
    """
    Train a single model end-to-end.
    
    Returns comprehensive result dict with metrics, timing, and trained model.
    """
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report, confusion_matrix,
        top_k_accuracy_score,
    )
    
    registry = MODEL_REGISTRY[model_name]
    t_start = time.time()
    
    result = {
        "model_name": model_name,
        "display_name": registry["display_name"],
        "description": registry["description"],
        "trained_at": datetime.now().isoformat(),
        "success": False,
        "error": None,
        "metrics": {},
        "timing": {},
        "best_params": None,
        "model_file": None,
    }
    
    try:

        steps = []
        if registry["needs_scaling"]:
            steps.append(("scaler", StandardScaler()))
        
        base_model = get_sklearn_model(model_name)
        steps.append(("classifier", base_model))
        
        pipeline = Pipeline(steps)
        

        if do_grid_search and registry["param_grid"]:
            from sklearn.model_selection import GridSearchCV
            
            log.info(f"    Running GridSearchCV ({cv_folds}-fold)...")
            grid = GridSearchCV(
                pipeline,
                registry["param_grid"],
                cv=cv_folds,
                scoring="accuracy",
                n_jobs=-1,
                refit=True,
            )
            
            grid.fit(X_train, y_train)
            pipeline = grid.best_estimator_
            result["best_params"] = {
                k.replace("classifier__", ""): v
                for k, v in grid.best_params_.items()
            }
            result["metrics"]["cv_best_score"] = round(grid.best_score_, 4)
        else:
            pipeline.fit(X_train, y_train)
        

        t_infer_start = time.time()
        y_pred_train = pipeline.predict(X_train)
        y_pred_test = pipeline.predict(X_test)
        infer_time = (time.time() - t_infer_start) * 1000
        

        try:
            y_proba = pipeline.predict_proba(X_test)
            has_proba = True
        except Exception:
            y_proba = None
            has_proba = False
        

        acc_train = accuracy_score(y_train, y_pred_train)
        acc_test = accuracy_score(y_test, y_pred_test)
        

        unique_test = np.unique(y_test)
        if len(unique_test) < 2:
            prec = rec = f1 = acc_test
            macro_prec = macro_rec = macro_f1 = acc_test
        else:
            prec = precision_score(y_test, y_pred_test, average="weighted", zero_division=0)
            rec = recall_score(y_test, y_pred_test, average="weighted", zero_division=0)
            f1 = f1_score(y_test, y_pred_test, average="weighted", zero_division=0)
            macro_prec = precision_score(y_test, y_pred_test, average="macro", zero_division=0)
            macro_rec = recall_score(y_test, y_pred_test, average="macro", zero_division=0)
            macro_f1 = f1_score(y_test, y_pred_test, average="macro", zero_division=0)
        

        try:
            all_labels = sorted(set(y_test.tolist()) | set(pipeline.classes_)) if hasattr(pipeline, 'classes_') else None
            top3 = top_k_accuracy_score(y_test, y_proba, k=3, labels=all_labels) if y_proba is not None else None
            top5 = top_k_accuracy_score(y_test, y_proba, k=5, labels=all_labels) if y_proba is not None else None
        except Exception:
            top3 = top5 = None
        

        cm = confusion_matrix(y_test, y_pred_test)
        

        overfitting_gap = acc_train - acc_test
        overfitting_status = "none"
        if overfitting_gap > 0.20:
            overfitting_status = "severe"
        elif overfitting_gap > 0.10:
            overfitting_status = "moderate"
        elif overfitting_gap > 0.05:
            overfitting_status = "slight"
        
        total_time = (time.time() - t_start) * 1000
        
        result.update({
            "success": True,
            "metrics": {
                "accuracy_train": round(acc_train, 4),
                "accuracy_test": round(acc_test, 4),
                "precision_weighted": round(prec, 4),
                "recall_weighted": round(rec, 4),
                "f1_weighted": round(f1, 4),
                "precision_macro": round(macro_prec, 4),
                "recall_macro": round(macro_rec, 4),
                "f1_macro": round(macro_f1, 4),
                "top3_accuracy": round(float(top3), 4) if top3 is not None else None,
                "top5_accuracy": round(float(top5), 4) if top5 is not None else None,
                "overfitting_gap": round(overfitting_gap, 4),
                "overfitting_status": overfitting_status,
                "n_classes_test": len(unique_test),
                "has_probability": has_proba,
            },
            "timing": {
                "total_ms": round(total_time, 1),
                "inference_ms": round(infer_time, 2),
                "n_train": len(X_train),
                "n_test": len(X_test),
                "n_features": X_train.shape[1],
            },
            "confusion_matrix": cm.tolist(),
        })
        

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODELS_DIR / f"{model_name}.pkl"
        
        import joblib
        joblib.dump(pipeline, str(model_path))
        result["model_file"] = str(model_path)
        result["model_size_kb"] = round(model_path.stat().st_size / 1024, 1)
        

        if hasattr(pipeline.named_steps.get("classifier", None), "feature_importances_"):
            clf = pipeline.named_steps["classifier"]
            fi = clf.feature_importances_

            top_indices = np.argsort(fi)[-10:][::-1]
            result["feature_importance"] = [
                {"feature": feature_names[i], "importance": round(float(fi[i]), 4)}
                for i in top_indices
            ]
        
        log.info(f"    ✅ {registry['display_name']}: "
                   f"test_acc={acc_test:.1%}, F1={f1:.3f}, "
                   f"time={total_time:.0f}ms")
        
        if overfitting_status != "none":
            status_icon = {"slight": "🟡", "moderate": "🟠", "severe": "🔴"}
            log.info(f"       {status_icon.get(overfitting_status, '')} "
                      f"Overfitting: train={acc_train:.1%} vs test={acc_test:.1%} "
                      f"(gap={overfitting_gap:.1%})")
        
    except Exception as e:
        result["error"] = str(e)
        result["timing"]["total_ms"] = round((time.time() - t_start) * 1000, 1)
        log.error(f"    ❌ {registry['display_name']} FAILED: {e}")
    
    return result


def train_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
    model_names: Optional[List[str]] = None,
    do_grid_search: bool = False,
    cv_folds: int = 5,
) -> Dict[str, Any]:
    """Train all specified models and collect results."""
    if model_names is None:
        model_names = ALL_MODEL_NAMES
    
    results = {}
    t_total_start = time.time()
    
    for i, model_name in enumerate(model_names, 1):
        registry = MODEL_REGISTRY.get(model_name, {})
        icon = registry.get("color", "⚪")
        display = registry.get("display_name", model_name)
        
        print(f"\n  [{i}/{len(model_names)}] Training {icon} {display}...", end="", flush=True)
        
        result = train_single_model(
            model_name=model_name,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            do_grid_search=do_grid_search,
            cv_folds=cv_folds,
        )
        
        results[model_name] = result
        
        if result["success"]:
            m = result["metrics"]
            t = result.get("timing", {})
            print(f" ✅ acc={m['accuracy_test']:.1%} | F1={m['f1_weighted']:.3f} | "
                  f"{t.get('inference_ms', '?')}ms/inference")
        else:
            print(f" ❌ {result.get('error', 'Unknown error')[:60]}")
    
    total_time = (time.time() - t_total_start) * 1000
    
    return {
        "timestamp": datetime.now().isoformat(),
        "model_results": results,
        "summary": {
            "total_models": len(model_names),
            "successful": sum(1 for r in results.values() if r["success"]),
            "failed": sum(1 for r in results.values() if not r["success"]),
            "total_time_ms": round(total_time, 1),
            "n_features": len(feature_names),
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
    }






def print_training_report(results: Dict[str, Any]) -> None:
    """Print comprehensive training report."""
    model_results = results.get("model_results", {})
    summary = results.get("summary", {})
    
    print("\n" + "=" * 70)
    print("  🤖 CLASSICAL ML TRAINING REPORT (PKB-2.1)")
    print("=" * 70)
    

    print(f"\n  📊 Summary:")
    print(f"    Models trained:   {summary.get('successful', 0)}/{summary.get('total_models', 0)}")
    print(f"    Failed:           {summary.get('failed', 0)}")
    print(f"    Features:        {summary.get('n_features', '?')}")
    print(f"    Train/Test:       {summary.get('n_train', '?')}/{summary.get('n_test', '?')}")
    print(f"    Total time:       {summary.get('total_time_ms', 0):.0f}ms")
    

    print(f"\n  📋 Model Comparison:")
    print(f"  {'Model':<26s} {'Acc':>6s} {'Prec':>6s} {'Rec':>6s} {'F1':>6s} {'Time':>8s} {'Overfit':>9s} {'Status':>8s}")
    print(f"  {'─'*26} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*9} {'─'*8}")
    
    ranked = sorted(
        [(name, r) for name, r in model_results.items() if r["success"]],
        key=lambda x: x[1]["metrics"].get("f1_weighted", 0),
        reverse=True
    )
    
    for rank, (name, result) in enumerate(ranked, 1):
        reg = MODEL_REGISTRY[name]
        m = result["metrics"]
        t = result["timing"]
        of = m.get("overfitting_status", "none")
        of_icon = {"none": "✅", "slight": "🟡", "moderate": "🟠", "severe": "🔴"}.get(of, "?")
        
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
        
        print(f"  {medal}{reg['display_name']:<24s} "
              f"{m['accuracy_test']:>5.1%} "
              f"{m['precision_weighted']:>5.1%} "
              f"{m['recall_weighted']:>5.1%} "
              f"{m['f1_weighted']:>5.3f} "
              f"{t['inference_ms']:>7.1f}ms "
              f"{of_icon:>5s}{of:<4s} "
              f"{'SAVED' if result.get('model_file') else 'NO'}")
    

    if ranked:
        best_name, best_result = ranked[0]
        best_m = best_result["metrics"]
        best_reg = MODEL_REGISTRY[best_name]
        print(f"\n  🏆 Best Model: **{best_reg['display_name']}** ({best_name})")
        print(f"     Test Accuracy: {best_m['accuracy_test']:.1%}")
        print(f"     F1 Score (weighted): {best_m['f1_weighted']:.4f}")
        print(f"     Inference Time: {best_result['timing']['inference_ms']:.1f}ms/image")
        
        if best_result.get("feature_importance"):
            print(f"\n     Top 5 Important Features:")
            for fi in best_result["feature_importance"][:5]:
                print(f"       • {fi['feature']}: {fi['importance']}")
        
        if best_result.get("best_params"):
            print(f"\n     Best Params (GridSearch):")
            for k, v in best_result["best_params"].items():
                print(f"       • {k}: {v}")


def save_training_report(results: Dict[str, Any]) -> Path:
    """Save full training results to JSON."""
    reports_dir = PROJECT_ROOT / "ai_core" / "evaluation"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = reports_dir / "training_results.json"
    

    saveable = {
        "timestamp": results.get("timestamp"),
        "summary": results.get("summary"),
        "models": {},
    }
    
    for name, result in results.get("model_results", {}).items():
        entry = {
            "success": result.get("success"),
            "display_name": result.get("display_name"),
            "metrics": result.get("metrics", {}),
            "timing": result.get("timing", {}),
            "model_file": result.get("model_file"),
            "model_size_kb": result.get("model_size_kb"),
            "best_params": result.get("best_params"),
            "feature_importance": result.get("feature_importance")[:10] if result.get("feature_importance") else None,
            "error": result.get("error"),
        }
        saveable["models"][name] = entry
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(saveable, f, indent=2, ensure_ascii=False, default=str)
    
    return report_path






def export_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    sample_ids: List[str],
    output_dir: Path,
) -> None:
    """Export train/test split to separate CSV files for reuse."""
    import csv as csv_mod
    
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    

    from sklearn.model_selection import train_test_split
    idx_train, idx_test = train_test_split(
        np.arange(len(y)), test_size=0.2, random_state=42, stratify=None
    )
    
    def write_split(indices, suffix):
        out_path = output_dir / f"{suffix}_features.csv"
        label_path = output_dir / f"{suffix}_labels.csv"
        
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv_mod.writer(f)
            writer.writerow(feature_names)
            for i in indices:
                row = [str(v) for v in X[i]]
                writer.writerow(row)
        
        with open(label_path, "w", newline="", encoding="utf-8") as f:
            writer = csv_mod.writer(f)
            writer.writerow(["label"])
            for i in indices:
                writer.writerow([str(y[i])])
        
        log.info(f"  💾 Exported: {out_path.name} ({len(indices)} samples)")
    
    write_split(idx_train, "train")
    write_split(idx_test, "test")






def main():
    parser = argparse.ArgumentParser(
        description="🤖 Sahabat Aksara — Classical ML Training (PKB-2.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available models:
  knn                  k-Nearest Neighbors (distance-based)
  naive_bayes          Naive Bayes Gaussian (probabilistic)
  svm                  Support Vector Machine (RBF kernel)
  decision_tree       Decision Tree (interpretable!)
  random_forest        Random Forest (ensemble trees)
  logistic_regression  Logistic Regression (linear baseline)
  all                  Train all 6 models (default)

Examples:
  python train_classical.py
  python train_classical.py --models knn svm rf
  python train_classical.py --grid-search
  python train_classical.py --cv 10
        """,
    )
    
    parser.add_argument("--input", "-i", type=str, default=None,
                        help=f"Input features CSV (default: {DEFAULT_FEATURES_CSV})")
    parser.add_argument("--models", "-m", nargs="+", default=None,
                        choices=ALL_MODEL_NAMES + ["all"],
                        help="Models to train (default: all)")
    parser.add_argument("--test-size", "-t", type=float, default=0.2,
                        help="Test set ratio (default: 0.2)")
    parser.add_argument("--grid-search", "-g", action="store_true",
                        help="Enable GridSearchCV hyperparameter tuning")
    parser.add_argument("--cv", "-c", type=int, default=5,
                        help="K-Fold CV folds for grid search (default: 5)")
    parser.add_argument("--no-export", action="store_true",
                        help="Skip exporting train/test split files")
    
    args = parser.parse_args()
    

    input_path = Path(args.input) if args.input else DEFAULT_FEATURES_CSV
    

    if args.models and "all" in args.models:
        model_names = ALL_MODEL_NAMES
    elif args.models:
        model_names = args.models
    else:
        model_names = ALL_MODEL_NAMES
    

    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  🤖 SAHABAT AKSARA — CLASSICAL ML TRAINING (PKB-2.1)".center(64) + "║")
    print("╠" + "═" * 68 + "╣")
    print(f"║  Input:  {str(input_path):<54s}║")
    print(f"║  Models: {', '.join(model_names):<48s}║")
    print(f"║  Grid:   {'Yes' if args.grid_search else 'No':<55s}║")
    print(f"║  CV:     {args.cv}-fold{'':<51s}║")
    print("╚" + "═" * 68 + "╝\n")
    

    print("  Loading features...")
    X, y, feature_names, sample_ids = load_features_csv(input_path)
    
    n_samples, n_features = X.shape
    unique_classes = len(np.unique(y))
    
    print(f"  ✅ Loaded: {n_samples} samples × {n_features} features × {unique_classes} classes")
    

    classes, counts = np.unique(y, return_counts=True)
    if len(classes) <= 15:
        print(f"  📊 Class distribution:")
        for c, cnt in zip(classes, counts):
            bar = "█" * min(cnt, 20)
            pct = cnt / n_samples * 100
            print(f"       '{c}': {cnt:>4d} ({pct:>5.1f}%) {bar}")
    

    X_train, X_test, y_train, y_test = prepare_train_test_split(
        X, y, test_size=args.test_size
    )
    
    print(f"\n  📦 Split: {len(X_train)} train / {len(X_test)} test")
    

    results = train_all_models(
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        feature_names=feature_names,
        model_names=model_names,
        do_grid_search=args.grid_search,
        cv_folds=args.cv,
    )
    

    print_training_report(results)
    

    report_path = save_training_report(results)
    print(f"\n  📄 Report saved: {report_path}")
    

    if not args.no_export:
        export_train_test_split(X, y, feature_names, sample_ids, EXPORTS_DIR)
    

    failed = results["summary"].get("failed", 0)
    if failed > 0:
        print(f"\n  ⚠️  {failed} model(s) failed to train.")
        sys.exit(1)
    else:
        print(f"\n  ✅ All {results['summary']['successful']} models trained successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
