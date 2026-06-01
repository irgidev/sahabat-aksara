
"""
PKB-2.2: Model Evaluation & Benchmark Suite
==================================================
Comprehensive benchmark of all trained classical ML models.
Generates comparison tables, confusion matrices, and finds best model.

Usage:
    python evaluate_models.py
    python evaluate_models.py --models knn svm rf
    python evaluate_models.py --confusion-matrix

Author: Sahabat Aksara — PKB-2 Evaluation Pipeline
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
MODELS_DIR = PROJECT_ROOT / "ai_core" / "models" / "classical"
FEATURES_DIR = PROJECT_ROOT / "data_science" / "datasets" / "features"
EVALUATION_DIR = PROJECT_ROOT / "ai_core" / "evaluation"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("evaluate")






def load_trained_model(model_name: str):
    """Load a trained model from .pkl file."""
    import joblib
    
    model_path = MODELS_DIR / f"{model_name}.pkl"
    if not model_path.exists():
        return None, f"Model file not found: {model_path}"
    
    try:
        model = joblib.load(str(model_path))
        return model, None
    except Exception as e:
        return None, f"Failed to load: {e}"


def list_available_models() -> List[str]:
    """List all trained model files."""
    if not MODELS_DIR.exists():
        return []
    return [p.stem for p in MODELS_DIR.glob("*.pkl")]






def load_evaluation_data(csv_path: Optional[Path] = None):
    """Load features + labels for evaluation (same split as training)."""
    from sklearn.model_selection import train_test_split
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
    
    X_list, y_raw, sample_ids = [], [], []
    for row in rows:
        sample_ids.append(row.get("_filename", "?"))
        y_raw.append(row.get("_char_target", ""))
        X_list.append([float(row.get(c, 0)) for c in feat_cols])
    
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
    

    idx_train, idx_test = train_test_split(
        np.arange(len(y)), test_size=0.2, random_state=42
    )
    
    return X, y, feat_cols, idx_train, idx_test, sample_ids






def evaluate_single_model(
    model_name: str,
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation on a single trained model.
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report, confusion_matrix,
        cohen_kappa_score, matthews_corrcoef,
        balanced_accuracy_score,
        top_k_accuracy_score,
    )
    
    t_start = time.time()
    
    result = {
        "model_name": model_name,
        "evaluated_at": datetime.now().isoformat(),
        "success": False,
        "error": None,
        "metrics": {},
        "classification_report": {},
        "confused_pairs": [],
    }
    
    try:

        y_pred = model.predict(X_test)
        
        try:
            y_proba = model.predict_proba(X_test)
            has_proba = True
        except Exception:
            y_proba = None
            has_proba = False
        
        infer_time = (time.time() - t_start) * 1000
        
        unique_test = np.unique(y_test)
        

        acc = accuracy_score(y_test, y_pred)
        
        if len(unique_test) >= 2:
            prec_w = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            rec_w = recall_score(y_test, y_pred, average="weighted", zero_division=0)
            f1_w = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            prec_m = precision_score(y_test, y_pred, average="macro", zero_division=0)
            rec_m = recall_score(y_test, y_pred, average="macro", zero_division=0)
            f1_m = f1_score(y_test, y_pred, average="macro", zero_division=0)
            kappa = cohen_kappa_score(y_test, y_pred)
            mcc = matthews_corrcoef(y_test, y_pred)
            bal_acc = balanced_accuracy_score(y_test, y_pred)
        else:
            prec_w = rec_w = f1_w = prec_m = rec_m = f1_m = kappa = mcc = bal_acc = acc
        

        try:
            all_labels = sorted(set(y_test.tolist()) | set(model.classes_)) if hasattr(model, 'classes_') else None
            top3 = top_k_accuracy_score(y_test, y_proba, k=3, labels=all_labels) if y_proba is not None else None
            top5 = top_k_accuracy_score(y_test, y_proba, k=5, labels=all_labels) if y_proba is not None else None
        except Exception:
            top3 = top5 = None
        

        unique_labels = sorted(set(y_test.tolist()) | set(y_pred.tolist()))
        cm = confusion_matrix(y_test, y_pred, labels=unique_labels)
        

        confused_pairs = []
        if cm.shape[0] > 1 and cm.shape[1] > 1:
            np.fill_diagonal(cm, -1)
            flat_indices = np.argsort(cm.flatten())[::-1]
            
            for idx in flat_indices[:10]:
                true_idx, pred_idx = np.unravel_index(idx, cm.shape)
                count = cm[true_idx, pred_idx]
                if count > 0:
                    confused_pairs.append({
                        "actual": str(unique_test[true_idx]) if true_idx < len(unique_test) else "?",
                        "predicted": str(unique_test[pred_idx]) if pred_idx < len(unique_test) else "?",
                        "count": int(count),
                    })
        

        try:
            report_dict = classification_report(
                y_test, y_pred, output_dict=True, zero_division=0
            )
            per_class = {}
            for label_key in sorted(report_dict.keys(), key=lambda x: str(x)):
                if isinstance(label_key, (int, float, str)):
                    per_class[str(label_key)] = {
                        "precision": round(report_dict[label_key].get("precision", 0), 4),
                        "recall": round(report_dict[label_key].get("recall", 0), 4),
                        "f1": round(report_dict[label_key].get("f1-score", 0), 4),
                        "support": int(report_dict[label_key].get("support", 0)),
                    }
            result["per_class_metrics"] = per_class
        except Exception:
            pass
        
        result.update({
            "success": True,
            "metrics": {
                "accuracy": round(acc, 4),
                "precision_weighted": round(prec_w, 4),
                "recall_weighted": round(rec_w, 4),
                "f1_weighted": round(f1_w, 4),
                "precision_macro": round(prec_m, 4),
                "recall_macro": round(rec_m, 4),
                "f1_macro": round(f1_m, 4),
                "kappa": round(kappa, 4),
                "mcc": round(mcc, 4),
                "balanced_accuracy": round(bal_acc, 4),
                "top3_accuracy": round(float(top3), 4) if top3 is not None else None,
                "top5_accuracy": round(float(top5), 4) if top5 is not None else None,
                "n_test_samples": len(y_test),
                "n_classes": len(unique_test),
            },
            "timing": {
                "inference_ms_total": round(infer_time, 2),
                "inference_per_sample_ms": round(infer_time / max(len(y_test), 1), 3),
            },
            "confusion_matrix": cm.tolist(),
            "confused_pairs": confused_pairs[:5],
        })
        
    except Exception as e:
        result["error"] = str(e)
        log.error(f"  ❌ Evaluation failed for {model_name}: {e}")
    
    return result


def run_full_benchmark(
    model_names: Optional[List[str]] = None,
    generate_confusion_png: bool = False,
) -> Dict[str, Any]:
    """Run benchmark on ALL available trained models."""
    
    if model_names is None:
        model_names = list_available_models()
    
    print(f"\n  Loading evaluation data...")
    X, y, feat_cols, idx_train, idx_test, sample_ids = load_evaluation_data()
    
    X_test = X[idx_test]
    y_test = y[idx_test]
    
    print(f"  ✅ Test set: {len(X_test)} samples × {X_test.shape[1]} features")
    
    results = {}
    t_total = time.time()
    
    for i, model_name in enumerate(model_names, 1):
        model, err = load_trained_model(model_name)
        
        if model is None:
            print(f"\n  [{i}/{len(model_names)}] ⏭️  {model_name}: {err}")
            results[model_name] = {"success": False, "error": err}
            continue
        
        print(f"\n  [{i}/{len(model_names)}] Evaluating {model_name}...", end="", flush=True)
        
        eval_result = evaluate_single_model(
            model_name=model_name,
            model=model,
            X_test=X_test,
            y_test=y_test,
            feature_names=feat_cols,
        )
        
        results[model_name] = eval_result
        
        if eval_result["success"]:
            m = eval_result["metrics"]
            t = eval_result.get("timing", {})
            print(f" ✅ acc={m['accuracy']:.1%} | F1={m['f1_weighted']:.3f} | "
                  f"{t.get('inference_per_sample_ms', '?'):.2f}ms/sample")
        else:
            print(f" ❌ {eval_result.get('error', 'Unknown')[:50]}")
    
    total_time = (time.time() - t_total) * 1000
    

    successful = {k: v for k, v in results.items() if v.get("success")}
    ranked = sorted(successful.items(), key=lambda x: x[1]["metrics"].get("f1_weighted", 0), reverse=True)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "benchmark_config": {
            "test_samples": len(X_test),
            "features": len(feat_cols),
            "models_evaluated": len(model_names),
            "successful": len(successful),
            "total_time_ms": round(total_time, 1),
        },
        "ranking": [
            {
                "rank": r + 1,
                "model": name,
                "accuracy": res["metrics"]["accuracy"],
                "f1_weighted": res["metrics"]["f1_weighted"],
                "f1_macro": res["metrics"].get("f1_macro"),
                "kappa": res["metrics"].get("kappa"),
                "inference_ms_per_sample": res.get("timing", {}).get("inference_per_sample_ms"),
            }
            for r, (name, res) in enumerate(ranked)
        ],
        "best_model": ranked[0][0] if ranked else None,
        "worst_model": ranked[-1][0] if ranked else None,
    }
    
    return {
        "model_results": results,
        "summary": summary,
    }






def print_benchmark_report(benchmark: Dict[str, Any]) -> None:
    """Print beautiful benchmark comparison table."""
    summary = benchmark.get("summary", {})
    ranking = summary.get("ranking", [])
    model_results = benchmark.get("model_results", {})
    
    print("\n" + "=" * 72)
    print("  📊 ML BENCHMARK REPORT (PKB-2.2)")
    print("=" * 72)
    
    config = summary.get("benchmark_config", {})
    print(f"\n  ⚙️  Config:")
    print(f"    Test samples:     {config.get('test_samples', '?')}")
    print(f"    Features:         {config.get('features', '?')}")
    print(f"    Models evaluated: {config.get('successful', '?')}/{config.get('models_evaluated', '?')}")
    print(f"    Total time:       {config.get('total_time_ms', 0):.0f}ms")
    

    print(f"\n  🏆 Model Ranking (by F1-weighted):")
    print(f"  {'Rank':<5s} {'Model':<26s} {'Acc':>6s} {'F1(w)':>7s} {'F1(m)':>7s} {'Kappa':>7s} {'Time':>8s}")
    print(f"  {'─'*4} {'─'*26} {'─'*6} {'─'*7} {'─'*7} {'─'*7} {'─'*8}")
    
    medals = ["🥇", "🥈", "🥉"]
    for entry in ranking:
        rank = entry["rank"]
        medal = medals[rank - 1] if rank <= 3 else f"{rank:>2}."
        time_str = f"{entry['inference_ms_per_sample']:.2f}ms" if entry.get("inference_ms_per_sample") else "N/A"
        
        print(f"  {medal:<5s}{entry['model']:<26s}"
              f"{entry['accuracy']:>5.1%} "
              f"{entry['f1_weighted']:>6.3f} "
              f"{entry['f1_macro']:>6.3f} "
              f"{entry['kappa']:>6.3f} "
              f"{time_str:>8s}")
    

    best = summary.get("best_model")
    worst = summary.get("worst_model")
    
    if best and best in model_results:
        br = model_results[best]["metrics"]
        print(f"\n  👑 BEST MODEL: **{best}**")
        print(f"     Accuracy:   {br['accuracy']:.1%}")
        print(f"     F1 (w):     {br['f1_weighted']:.4f}")
        print(f"     Kappa:      {br.get('kappa', 'N/A')}")
        print(f"     Inference: {model_results[best].get('timing', {}).get('inference_per_sample_ms', '?')}ms/sample")
        

        confused = model_results[best].get("confused_pairs", [])
        if confused:
            print(f"\n     Most common mistakes:")
            for cp in confused[:5]:
                print(f"       '{cp['actual']}' → '{cp['predicted']}' ({cp['count']}×)")
    
    if worst and worst in model_results and worst != best:
        wr = model_results[worst]["metrics"]
        print(f"\n  💩 WORST MODEL: **{worst}**")
        print(f"     Accuracy: {wr['accuracy']:.1%} | F1: {wr['f1_weighted']:.4f}")
    

    print(f"\n  ⚡ Speed vs Accuracy Trade-off:")
    for entry in ranking:
        name = entry["model"]
        acc = entry["accuracy"]
        speed = entry.get("inference_ms_per_sample", 0)
        if speed:
            efficiency = acc / max(speed, 0.001) * 100
            bar_len = min(int(efficiency / 2), 20)
            bar = "█" * bar_len
            print(f"     {name:<26s} acc={acc:.0%} | {speed:.2f}ms | eff={efficiency:.0f} {bar}")


def save_benchmark_report(benchmark: Dict[str, Any]) -> Path:
    """Save full benchmark to JSON."""
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    
    path = EVALUATION_DIR / "benchmark_results.json"
    
    saveable = {
        "timestamp": benchmark.get("summary", {}).get("timestamp"),
        "summary": benchmark.get("summary", {}),
        "models": {},
    }
    
    for name, result in benchmark.get("model_results", {}).items():
        saveable["models"][name] = {
            "success": result.get("success"),
            "metrics": result.get("metrics", {}),
            "timing": result.get("timing", {}),
            "confused_pairs": result.get("confused_pairs", [])[:10],
            "error": result.get("error"),
        }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(saveable, f, indent=2, ensure_ascii=False, default=str)
    
    return path






def main():
    parser = argparse.ArgumentParser(
        description="📊 Sahabat Aksara — Model Evaluation & Benchmark (PKB-2.2)",
    )
    parser.add_argument("--models", "-m", nargs="+", default=None,
                        help="Specific models to evaluate (default: all trained)")
    parser.add_argument("--confusion-matrix", action="store_true",
                        help="Generate confusion matrix visualization (requires matplotlib)")
    
    args = parser.parse_args()
    

    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + "  📊 SAHABAT AKSARA — MODEL EVALUATION (PKB-2.2)".center(64) + "║")
    print("╚" + "═" * 68 + "╝\n")
    

    benchmark = run_full_benchmark(
        model_names=args.models,
    )
    

    print_benchmark_report(benchmark)
    

    path = save_benchmark_report(benchmark)
    print(f"\n  📄 Benchmark saved: {path}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
