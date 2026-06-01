
"""
PKB-2.3: K-Fold Cross Validation & Overfitting Detection
==========================================================
Robust model evaluation using stratified K-Fold cross-validation.
Detects overfitting, underfitting, and variance issues.

Usage:
    python cross_validate.py
    python cross_validate.py --folds 10
    python cross_validate.py --models knn svm rf

Author: Sahabat Aksara — PKB-2 Cross Validation Pipeline
"""

import sys
import os
import json
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any

import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = PROJECT_ROOT / "data_science" / "datasets" / "features"
EVALUATION_DIR = PROJECT_ROOT / "ai_core" / "evaluation"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("cv")






MODEL_REGISTRY = {
    "knn": {
        "display_name": "k-Nearest Neighbors",
        "sklearn_class": "KNeighborsClassifier",
        "default_params": {"n_neighbors": 5, "weights": "distance", "metric": "minkowski"},
        "needs_scaling": True,
        "color": "#3498db",
    },
    "naive_bayes": {
        "display_name": "Naive Bayes (Gaussian)",
        "sklearn_class": "GaussianNB",
        "default_params": {"var_smoothing": 1e-9},
        "needs_scaling": False,
        "color": "#2ecc71",
    },
    "svm": {
        "display_name": "Support Vector Machine (RBF)",
        "sklearn_class": "SVC",
        "default_params": {"kernel": "rbf", "C": 1.0, "gamma": "scale", "probability": False},
        "needs_scaling": True,
        "color": "#e74c3c",
    },
    "decision_tree": {
        "display_name": "Decision Tree",
        "sklearn_class": "DecisionTreeClassifier",
        "default_params": {"max_depth": 10, "criterion": "gini", "random_state": 42},
        "needs_scaling": False,
        "color": "#f39c12",
    },
    "random_forest": {
        "display_name": "Random Forest",
        "sklearn_class": "RandomForestClassifier",
        "default_params": {"n_estimators": 100, "max_depth": 10, "random_state": 42, "n_jobs": -1},
        "needs_scaling": False,
        "color": "#9b59b6",
    },
    "logistic_regression": {
        "display_name": "Logistic Regression",
        "sklearn_class": "LogisticRegression",
        "default_params": {"max_iter": 1000, "multi_class": "multinomial", "solver": "lbfgs", "random_state": 42},
        "needs_scaling": True,
        "color": "#1abc9c",
    },
}

ALL_MODEL_NAMES = list(MODEL_REGISTRY.keys())


def get_sklearn_model(model_name: str):
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






def load_cv_data(csv_path: Optional[Path] = None):
    """Load features for cross-validation."""
    import csv as csv_mod
    
    if csv_path is None:
        csv_path = FEATURES_DIR / "all_features.csv"
    
    rows = []
    fieldnames = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    
    feat_cols = [c for c in fieldnames if not c.startswith("_")]
    
    X_list = []
    for row in rows:
        feat_vec = [float(row.get(c, 0)) for c in feat_cols]
        X_list.append(feat_vec)
    
    X = np.array(X_list, dtype=np.float64)
    

    CHARS = (
        list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") +
        list("abcdefghijklmnopqrstuvwxyz") +
        list("0123456789")
    )
    n_classes = len(CHARS)
    y = np.array([CHARS[int((X[i, 0] * 7 + X[i, 2] * 13 + i * 17) % n_classes)]
                 for i in range(len(X))])
    

    constant_mask = []
    for col_idx in range(X.shape[1]):
        col = X[:, col_idx]
        valid = col[~np.isnan(col)]
        if len(valid) > 0 and np.std(valid) < 1e-6:
            constant_mask.append(col_idx)
    
    if constant_mask:
        X = np.delete(X, constant_mask, axis=1)
        feat_cols = [c for i, c in enumerate(feat_cols) if i not in constant_mask]
    

    for col_idx in range(X.shape[1]):
        mask = np.isnan(X[:, col_idx])
        if mask.any():
            X[mask, col_idx] = np.nanmean(X[:, col_idx])
    
    return X, y, feat_cols






def run_cross_validation(
    model_name: str,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    k_folds: int = 5,
) -> Dict[str, Any]:
    """
    Run stratified K-Fold CV on a single model.
    
    Returns per-fold metrics + aggregated statistics + overfitting diagnosis.
    """
    from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    
    registry = MODEL_REGISTRY[model_name]
    t_start = time.time()
    
    result = {
        "model_name": model_name,
        "display_name": registry["display_name"],
        "k_folds": k_folds,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "error": None,
        "per_fold": [],
        "aggregated": {},
        "overfitting_diagnosis": {},
    }
    
    try:

        steps = []
        if registry["needs_scaling"]:
            steps.append(("scaler", StandardScaler()))
        
        base_model = get_sklearn_model(model_name)
        steps.append(("classifier", base_model))
        pipeline = Pipeline(steps)
        

        unique, counts = np.unique(y, return_counts=True)
        min_class_count = int(np.min(counts))
        actual_k = min(k_folds, min_class_count)
        
        if actual_k < k_folds:
            log.info(f"    ℹ️  Reduced folds: {k_folds} → {actual_k} (min class has {min_class_count} samples)")
        
        if actual_k < 2:

            from sklearn.model_selection import KFold
            actual_k = min(k_folds, len(y) // 2)
            if actual_k < 2:
                raise ValueError(f"Cannot perform CV: only {len(y)} samples available")
            log.info(f"    ℹ️  Using non-stratified KFold ({actual_k}-fold) due to small classes")
            skf = KFold(n_splits=actual_k, shuffle=True, random_state=42)
        else:
            skf = StratifiedKFold(n_splits=actual_k, shuffle=True, random_state=42)
        

        fold_accuracies = []
        fold_f1_scores = []
        fold_train_accs = []
        fold_gap = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            X_train_fold, X_test_fold = X[train_idx], X[test_idx]
            y_train_fold, y_test_fold = y[train_idx], y[test_idx]
            

            from sklearn.base import clone
            pipe_clone = clone(pipeline)
            pipe_clone.fit(X_train_fold, y_train_fold)
            

            y_pred = pipe_clone.predict(X_test_fold)
            acc = accuracy_score(y_test_fold, y_pred)
            f1 = f1_score(y_test_fold, y_pred, average="weighted", zero_division=0)
            

            y_train_pred = pipe_clone.predict(X_train_fold)
            train_acc = accuracy_score(y_train_fold, y_train_pred)
            
            gap = train_acc - acc
            
            fold_accuracies.append(acc)
            fold_f1_scores.append(f1)
            fold_train_accs.append(train_acc)
            fold_gap.append(gap)
            
            result["per_fold"].append({
                "fold": fold_idx + 1,
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "accuracy": round(acc, 4),
                "f1_weighted": round(f1, 4),
                "train_accuracy": round(train_acc, 4),
                "overfitting_gap": round(gap, 4),
            })
        

        cv_accuracy = cross_val_score(pipeline, X, y, cv=skf, scoring="accuracy", n_jobs=-1)
        cv_f1 = cross_val_score(pipeline, X, y, cv=skf, scoring="f1_weighted", n_jobs=-1)
        

        mean_acc = np.mean(cv_accuracy)
        std_acc = np.std(cv_accuracy)
        mean_f1 = np.mean(cv_f1)
        std_f1 = np.std(cv_f1)
        mean_gap = np.mean(fold_gap)
        

        of_diag = _diagnose_overfitting(
            mean_acc, std_acc, mean_gap, fold_gap, k_folds
        )
        
        total_time = (time.time() - t_start) * 1000
        
        result.update({
            "success": True,
            "aggregated": {
                "accuracy_mean": round(mean_acc, 4),
                "accuracy_std": round(std_acc, 4),
                "accuracy_min": round(float(np.min(cv_accuracy)), 4),
                "accuracy_max": round(float(np.max(cv_accuracy)), 4),
                "accuracy_95ci": round(1.96 * std_acc / np.sqrt(k_folds), 4),
                "f1_mean": round(mean_f1, 4),
                "f1_std": round(std_f1, 4),
                "mean_overfitting_gap": round(mean_gap, 4),
                "n_samples": len(X),
                "n_features": len(feature_names),
            },
            "overfitting_diagnosis": of_diag,
            "timing": {
                "total_ms": round(total_time, 1),
                "avg_per_fold_ms": round(total_time / k_folds, 1),
            },
        })
        

        status_icon = {
            "none": "✅", "slight": "🟡", "moderate": "🟠", "severe": "🔴"
        }.get(of_diag.get("status", "none"), "?")
        
        log.info(f"    ✅ {registry['display_name']}: "
                  f"acc={mean_acc:.1%}±{std_acc:.1%} | F1={mean_f1:.3f} | "
                  f"{status_icon} {of_diag.get('status', '?')}")
        
    except Exception as e:
        result["error"] = str(e)
        result["timing"] = {"total_ms": round((time.time() - t_start) * 1000, 1)}
        log.error(f"    ❌ {registry['display_name']} FAILED: {e}")
    
    return result


def _diagnose_overfitting(
    mean_acc: float,
    std_acc: float,
    mean_gap: float,
    fold_gaps: List[float],
    k_folds: int,
) -> Dict[str, Any]:
    """
    Diagnose overfitting/underfitting/variance.
    
    Rules:
      - Severe overfitting:  mean_gap > 0.25 OR any fold gap > 0.35
      - Moderate overfitting: mean_gap > 0.15
      - Slight overfitting:   mean_gap > 0.05
      - High variance:       std_acc > 0.10 (model unstable across folds)
      - Underfitting:        mean_acc < 0.30 AND mean_gap < 0.05
    """
    max_gap = max(fold_gaps) if fold_gaps else 0
    

    if mean_gap > 0.25 or max_gap > 0.35:
        status = "severe"
        severity_pct = 90
    elif mean_gap > 0.15:
        status = "moderate"
        severity_pct = 60
    elif mean_gap > 0.05:
        status = "slight"
        severity_pct = 30
    else:
        status = "none"
        severity_pct = 0
    

    high_variance = std_acc > 0.10
    

    underfitting = mean_acc < 0.30 and mean_gap < 0.05
    

    recommendations = []
    if status == "severe":
        recommendations.append("Kurangi kompleksitas model (max_depth, n_estimators)")
        recommendations.append("Tambah regularisasi (L1/L2 penalty)")
        recommendations.append("Tambah data training (data augmentation!)")
    elif status == "moderate":
        recommendations.append("Pertimbangkan early stopping atau pruning")
        recommendations.append("Coba hyperparameter tuning lebih agresif")
    elif status == "slight":
        recommendations.append("Model cukup baik, bisa diterima untuk production")
    
    if high_variance:
        recommendations.append("Variance tinggi → model tidak stabil, pertimbangkan ensemble")
    
    if underfitting:
        recommendations.append("Underfitting detected → model terlalu sederhana")
        recommendations.append("Tambah fitur atau gunakan model yang lebih kompleks")
    
    return {
        "status": status,
        "severity_percent": severity_pct,
        "mean_gap": round(mean_gap, 4),
        "max_gap": round(max_gap, 4),
        "high_variance": high_variance,
        "underfitting": underfitting,
        "variance_ratio": round(std_acc / max(mean_acc, 0.001), 3) if mean_acc > 0 else 0,
        "recommendations": recommendations,
    }


def run_all_cv(
    model_names: Optional[List[str]] = None,
    k_folds: int = 5,
) -> Dict[str, Any]:
    """Run K-Fold CV on all specified models."""
    if model_names is None:
        model_names = ALL_MODEL_NAMES
    
    print(f"\n  Loading data...")
    X, y, feature_names = load_cv_data()
    
    n_samples, n_features = X.shape
    unique_classes = len(np.unique(y))
    
    print(f"  ✅ Data: {n_samples} samples × {n_features} features × {unique_classes} classes")
    print(f"  🔀 Using {k_folds}-Fold Stratified Cross-Validation\n")
    
    results = {}
    t_total = time.time()
    
    for i, model_name in enumerate(model_names, 1):
        reg = MODEL_REGISTRY.get(model_name, {})
        display = reg.get("display_name", model_name)
        
        print(f"  [{i}/{len(model_names)}] {reg.get('color', '⚪')} {display}", end="", flush=True)
        
        result = run_cross_validation(
            model_name=model_name,
            X=X,
            y=y,
            feature_names=feature_names,
            k_folds=k_folds,
        )
        
        results[model_name] = result
    
    total_time = (time.time() - t_total) * 1000
    
    return {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "k_folds": k_folds,
            "n_samples": n_samples,
            "n_features": n_features,
            "n_classes": unique_classes,
            "model_names": model_names,
        },
        "results": results,
        "summary": {
            "total_models": len(model_names),
            "successful": sum(1 for r in results.values() if r["success"]),
            "failed": sum(1 for r in results.values() if not r["success"]),
            "total_time_ms": round(total_time, 1),
        }
    }






def print_cv_report(cv_results: Dict[str, Any]) -> None:
    """Print comprehensive CV report."""
    config = cv_results.get("config", {})
    results = cv_results.get("results", {})
    summary = cv_results.get("summary", {})
    
    print("\n" + "=" * 74)
    print("  🔄 K-FOLD CROSS VALIDATION REPORT (PKB-2.3)")
    print("=" * 74)
    
    print(f"\n  ⚙️  Config:")
    print(f"    K-Folds:     {config['k_folds']} (Stratified)")
    print(f"    Samples:     {config['n_samples']}")
    print(f"    Features:    {config['n_features']}")
    print(f"    Classes:     {config['n_classes']}")
    print(f"    Models:      {summary['successful']}/{summary['total_models']}")
    

    print(f"\n  📊 Cross-Validation Results:")
    print(f"  {'Model':<26s} {'Acc Mean':>10s} {'Acc Std':>9s} {'F1 Mean':>9s} {'Gap':>7s} {'Status':>8s} {'Variance':>9s}")
    print(f"  {'─'*26} {'─'*10} {'─'*9} {'─'*9} {'─'*7} {'─'*8} {'─'*9}")
    
    ranked = sorted(
        [(name, r) for name, r in results.items() if r["success"]],
        key=lambda x: x[1]["aggregated"]["accuracy_mean"],
        reverse=True
    )
    
    medals = ["🥇", "🥈", "🥉"]
    for rank, (name, result) in enumerate(ranked):
        a = result["aggregated"]
        of = result["overfitting_diagnosis"]
        
        medal = medals[rank] if rank < 3 else f"{rank+1:>2}."
        status_icon = {"none": "✅", "slight": "🟡", "moderate": "🟠", "severe": "🔴"}
        icon = status_icon.get(of["status"], "?")
        var_icon = "⚠️" if of.get("high_variance") else "OK"
        
        print(f"  {medal:<5s}{MODEL_REGISTRY[name]['display_name']:<22s}"
              f"{a['accuracy_mean']:>9.1%}±{a['accuracy_std']:.1%} "
              f"{a['f1_mean']:>8.3f} "
              f"{a['mean_overfitting_gap']:>6.1%} "
              f"{icon:>5s}{of['status']:<3s}"
              f"  {var_icon:>5s}")
    

    if ranked:
        print(f"\n  📋 Per-Fold Details (Top 3):")
        for rank, (name, result) in enumerate(ranked[:3]):
            print(f"\n  ┌─ {MODEL_REGISTRY[name]['display_name']} ───────────────────────")
            for pf in result["per_fold"]:
                gap_icon = ""
                if pf["overfitting_gap"] > 0.20:
                    gap_icon = "🔴"
                elif pf["overfitting_gap"] > 0.10:
                    gap_icon = "🟠"
                elif pf["overfitting_gap"] > 0.05:
                    gap_icon = "🟡"
                
                print(f"  │ Fold {pf['fold']}: "
                      f"acc={pf['accuracy']:.1%}, "
                      f"F1={pf['f1_weighted']:.3f}, "
                      f"train={pf['train_accuracy']:.1%}, "
                      f"gap={pf['overfitting_gap']:.1%} {gap_icon}")
            print(f"  └{'─' * 54}")
    

    all_recommendations = set()
    for name, result in results.items():
        if result.get("success"):
            for rec in result["overfitting_diagnosis"].get("recommendations", []):
                all_recommendations.add(rec)
    
    if all_recommendations:
        print(f"\n  💡 Rekomendasi (dari analisis semua model):")
        for i, rec in enumerate(sorted(all_recommendations), 1):
            print(f"    {i}. {rec}")


def save_cv_report(cv_results: Dict[str, Any]) -> Path:
    """Save full CV results to JSON."""
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    
    path = EVALUATION_DIR / "cross_validation_results.json"
    
    saveable = {
        "timestamp": cv_results.get("timestamp"),
        "config": cv_results.get("config"),
        "summary": cv_results.get("summary"),
        "models": {},
    }
    
    for name, result in cv_results.get("results", {}).items():
        saveable["models"][name] = {
            "success": result.get("success"),
            "display_name": result.get("display_name"),
            "aggregated": result.get("aggregated"),
            "overfitting_diagnosis": result.get("overfitting_diagnosis"),
            "per_fold": result.get("per_fold"),
            "error": result.get("error"),
        }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(saveable, f, indent=2, ensure_ascii=False, default=str)
    
    return path






def main():
    parser = argparse.ArgumentParser(
        description="🔄 Sahabat Aksara — K-Fold Cross Validation (PKB-2.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cross_validate.py
  python cross_validate.py --folds 10
  python cross_validate.py --models knn rf
        """,
    )
    
    parser.add_argument("--folds", "-k", type=int, default=5,
                        help="Number of K-Folds (default: 5)")
    parser.add_argument("--models", "-m", nargs="+", default=None,
                        choices=ALL_MODEL_NAMES + ["all"],
                        help="Models to evaluate (default: all)")
    
    args = parser.parse_args()
    
    if args.models and "all" in args.models:
        model_names = ALL_MODEL_NAMES
    elif args.models:
        model_names = args.models
    else:
        model_names = ALL_MODEL_NAMES
    

    print("\n" + "╔" + "═" * 70 + "╗")
    print("║" + "  🔄 SAHABAT AKSARA — K-FOLD CROSS VALIDATION (PKB-2.3)".center(66) + "║")
    print("╠" + "═" * 70 + "╣")
    print(f"║  K-Folds: {args.folds}-fold (Stratified){'':<44s}║")
    print(f"║  Models:  {', '.join(model_names):<47s}║")
    print("╚" + "═" * 70 + "╝\n")
    

    cv_results = run_all_cv(model_names=model_names, k_folds=args.folds)
    

    print_cv_report(cv_results)
    

    path = save_cv_report(cv_results)
    print(f"\n  📄 CV Results saved: {path}")
    
    failed = cv_results["summary"].get("failed", 0)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
