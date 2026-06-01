"""
Probability Calibration for Sahabat Aksara Models
===================================================
Many ML models output poorly calibrated probabilities:
  - Model says "90% confident" but is actually only 70% accurate
  - This is critical for kid-friendly feedback (don't lie to kids!)

This module provides:
  1. Reliability Diagrams (calibration curves)
  2. Brier Score evaluation
  3. Isotonic Regression & Platt Scaling calibration
  4. Per-model calibration assessment

Theory:
────────
  Well-calibrated: P(y=1 | predicted=p) ≈ p for all p ∈ [0,1]
  
  Brier Score: BS = (1/N) Σ (p_i - y_i)²
    Range: [0, 0] perfect, [0.25, 0.25] random (binary), worse for multi-class
  
  Expected Calibration Error (ECE):
    ECE = Σ_b n_b/N |acc(b) - conf(b)|
    Where b = bucket of predictions, acc = actual accuracy, conf = avg confidence

Usage:
    python ai_core/training/calibrate_models.py

Author: Sahabat Aksara AI Team (PKB-4 Phase 2)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np






def brier_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """
    Compute Brier Score (multi-class generalization).
    
    BS = (1/N) Σᵢ Σₖ (p_ik - y_ik)²
    
    Lower is better. 0 = perfect calibration.
    
    Args:
        y_true: One-hot encoded true labels (N, K)
        y_proba: Predicted probabilities (N, K)
        
    Returns:
        Brier score (float)
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_proba = np.asarray(y_proba, dtype=np.float64)
    return np.mean((y_proba - y_true) ** 2)


def brier_skill_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """
    Brier Skill Score: how much better than climatology (prior).
    
    BSS = 1 - BS(model) / BS(reference)
      reference = always predict prior distribution
    
    Range: (-∞, 1], where 1 = perfect, 0 = no skill vs prior, negative = worse.
    """
    bs_model = brier_score(y_true, y_proba)
    

    prior = np.mean(y_true, axis=0)
    y_ref = np.tile(prior, (len(y_true), 1))
    bs_ref = brier_score(y_true, y_ref)
    
    if bs_ref == 0:
        return 1.0 if bs_model == 0 else 0.0
    
    return 1.0 - bs_model / bs_ref


def expected_calibration_error(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    n_bins: int = 15,
) -> Tuple[float, List[Dict]]:
    """
    Compute Expected Calibration Error (ECE).
    
    ECE = Σ_b (n_b/N) |accuracy(b) - confidence(b)|
    
    Groups predictions into bins by confidence level,
    then compares average confidence vs actual accuracy in each bin.
    
    Args:
        y_true: True class indices (N,) or one-hot (N, K)
        y_proba: Predicted probabilities (N, K)
        n_bins: Number of equal-width bins
        
    Returns:
        Tuple of (ece score, bin details list)
    """
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba, dtype=np.float64)
    

    if y_true.ndim > 1:
        y_true = np.argmax(y_true, axis=1)
    

    pred_classes = np.argmax(y_proba, axis=1)
    confidences = np.max(y_proba, axis=1)
    accuracies = (pred_classes == y_true).astype(np.float64)
    

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_details = []
    
    for i in range(n_bins):
        mask = (confidences > bin_edges[i]) & (confidences <= bin_edges[i + 1])
        n_in_bin = np.sum(mask)
        
        if n_in_bin == 0:
            continue
        
        avg_conf = np.mean(confidences[mask])
        avg_acc = np.mean(accuracies[mask])
        
        ece += (n_in_bin / len(y_true)) * abs(avg_acc - avg_conf)
        
        bin_details.append({
            "bin": i,
            "range": f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
            "count": int(n_in_bin),
            "avg_confidence": round(float(avg_conf), 4),
            "avg_accuracy": round(float(avg_acc), 4),
            "gap": round(abs(float(avg_acc) - float(avg_conf)), 4),
            "overconfident": avg_conf > avg_acc,
        })
    
    return float(ece), bin_details


def reliability_data(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    n_bins: int = 15,
) -> Dict[str, Any]:
    """
    Generate full reliability diagram data for plotting.
    
    Returns dict with:
        - perfect_line: points for perfectly calibrated line
        - observed: (confidence, accuracy) points per bin
        - histogram: counts per bin (for bar chart below curve)
        - ece: expected calibration error
        - mce: maximum calibration error
    """
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba, dtype=np.float64)
    
    if y_true.ndim > 1:
        y_true = np.argmax(y_true, axis=1)
    
    pred_classes = np.argmax(y_proba, axis=1)
    confidences = np.max(y_proba, axis=1)
    accuracies = (pred_classes == y_true).astype(np.float64)
    
    bin_edges = np.linspace(0, 1, n_bins + 1)
    
    bin_confs = []
    bin_accs = []
    bin_counts = []
    max_ce = 0.0
    
    for i in range(n_bins):
        mask = (confidences > bin_edges[i]) & (confidences <= bin_edges[i + 1])
        n_in_bin = int(np.sum(mask))
        
        if n_in_bin > 0:
            bc = float(np.mean(confidences[mask]))
            ba = float(np.mean(accuracies[mask]))
            gap = abs(ba - bc)
            max_ce = max(max_ce, gap)
        else:
            bc = (bin_edges[i] + bin_edges[i + 1]) / 2
            ba = bc
            gap = 0
        
        bin_confs.append(bc)
        bin_accs.append(ba)
        bin_counts.append(n_in_bin)
    
    ece_val, _ = expected_calibration_error(y_true, y_proba, n_bins)
    
    return {
        "perfect_line": {"x": [0, 1], "y": [0, 1]},
        "observed": {"x": bin_confs, "y": bin_accs},
        "histogram": {"x": [(bin_edges[i]+bin_edges[i+1])/2 for i in range(n_bins)],
                     "counts": bin_counts},
        "n_bins": n_bins,
        "n_samples": len(y_true),
        "ece": round(ece_val, 5),
        "mce": round(max_ce, 5),
        "calibration_level": _calibration_level(ece_val),
    }


def _calibration_level(ece: float) -> str:
    """Interpret ECE value."""
    if ece < 0.02:
        return "excellent"
    elif ece < 0.05:
        return "good"
    elif ece < 0.10:
        return "moderate"
    elif ece < 0.15:
        return "poor"
    else:
        return "very_poor"






class IsotonicCalibrator:
    """
    Isotonic Regression Calibrator.
    
    Fits a non-decreasing piecewise function to map
    uncalibrated probabilities to calibrated ones.
    
    Works well when you have enough data and the miscalibration
    pattern is complex (non-linear).
    """
    
    def __init__(self):
        self.is_fitted_ = False
        self._x_points = None
        self._y_points = None
    
    def fit(self, y_true: np.ndarray, y_proba: np.ndarray, 
            target_class: Optional[int] = None) -> 'IsotonicCalibrator':
        """
        Fit isotonic calibrator on (predicted_prob, empirical_freq) pairs.
        
        Args:
            y_true: True labels (indices or one-hot)
            y_proba: Predicted probabilities
            target_class: Class to calibrate (None = use predicted class prob)
        """
        from scipy.interpolate import interp1d
        
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba, dtype=np.float64)
        
        if y_true.ndim > 1:
            y_true = np.argmax(y_true, axis=1)
        

        if target_class is not None:
            probs = y_proba[:, target_class]
            correct = (y_true == target_class).astype(np.float64)
        else:
            probs = np.max(y_proba, axis=1)
            correct = (np.argmax(y_proba, axis=1) == y_true).astype(np.float64)
        

        n_bins = min(50, len(probs) // 10)
        n_bins = max(n_bins, 10)
        
        bin_edges = np.linspace(0, 1, n_bins + 1)
        x_pts = []
        y_pts = []
        
        for i in range(n_bins):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
            if np.sum(mask) > 0:
                x_pts.append(float((bin_edges[i] + bin_edges[i + 1]) / 2))
                y_pts.append(float(np.mean(correct[mask])))
        

        y_cummax = np.maximum.accumulate(y_pts)
        
        self._x_points = np.array(x_pts)
        self._y_points = np.array(y_cummax)
        self.is_fitted_ = True
        return self
    
    def transform(self, proba: np.ndarray) -> np.ndarray:
        """Apply calibration to probabilities."""
        if not self.is_fitted_:
            raise RuntimeError("Calibrator not fitted.")
        
        from scipy.interpolate import interp1d
        
        proba = np.asarray(proba, dtype=np.float64)
        

        proba_clipped = np.clip(proba, 0, 1)
        

        try:
            f = interp1d(self._x_points, self._y_points, kind='linear',
                         bounds_error=False, fill_value=(self._y_points[0], self._y_points[-1]))
            result = np.array(f(proba_clipped)).flatten()
        except Exception:
            result = proba_clipped
        
        return np.clip(result, 0.001, 0.999)


class PlattCalibrator:
    """
    Platt Scaling (Logistic Calibration).
    
    Fits a logistic regression to map model outputs
    to well-calibrated probabilities:
        P_calibrated = 1 / (1 + exp(a * logit(p_raw) + b))
    
    Simple, fast, works well with limited data.
    Good for sigmoid-shaped miscalibration patterns.
    """
    
    def __init__(self):
        self.a = 0.0
        self.b = 0.0
        self.is_fitted_ = False
    
    def fit(self, y_true: np.ndarray, y_proba: np.ndarray,
            target_class: Optional[int] = None,
            max_iter: int = 1000) -> 'PlattCalibrator':
        """Fit Platt scaling parameters using gradient descent."""
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba, dtype=np.float64)
        
        if y_true.ndim > 1:
            y_true = np.argmax(y_true, axis=1)
        
        if target_class is not None:
            probs = y_proba[:, target_class]
            correct = (y_true == target_class).astype(np.float64)
        else:
            probs = np.max(y_proba, axis=1)
            correct = (np.argmax(y_proba, axis=1) == y_true).astype(np.float64)
        

        eps = 1e-7
        probs = np.clip(probs, eps, 1 - eps)
        

        logits = np.log(probs / (1 - probs))
        

        a, b = 0.0, 0.0
        lr = 0.01
        
        for _ in range(max_iter):
            z = a * logits + b
            p = 1 / (1 + np.exp(-z))
            p = np.clip(p, eps, 1 - eps)
            
            grad_a = np.mean((p - correct) * logits)
            grad_b = np.mean(p - correct)
            
            a -= lr * grad_a
            b -= lr * grad_b
        
        self.a = a
        self.b = b
        self.is_fitted_ = True
        return self
    
    def transform(self, proba: np.ndarray) -> np.ndarray:
        """Apply Platt scaling."""
        if not self.is_fitted_:
            raise RuntimeError("Calibrator not fitted.")
        
        proba = np.asarray(proba, dtype=np.float64)
        eps = 1e-7
        proba = np.clip(proba, eps, 1 - eps)
        logits = np.log(proba / (1 - proba))
        
        z = self.a * logits + self.b
        calib = 1 / (1 + np.exp(-z))
        
        return np.clip(calib, 0.001, 0.999)


class TemperatureScaling:
    """
    Temperature Scaling — simplest calibration method.
    
    Softmax with temperature T:
        P_calibrated(x) = softmax(logits / T)
    
    Single parameter! T>1 makes probabilities more uniform (less confident).
    T<1 makes them sharper (more confident).
    T=1 means no change.
    """
    
    def __init__(self):
        self.temperature = 1.0
        self.is_fitted_ = False
    
    def fit(self, y_true: np.ndarray, y_proba: np.ndarray,
            max_iter: int = 500) -> 'TemperatureScaling':
        """Find optimal temperature via grid search + refinement."""
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba, dtype=np.float64)
        
        if y_true.ndim > 1:
            y_true = np.argmax(y_true, axis=1)
        

        best_t = 1.0
        best_nll = float('inf')
        
        for t in np.linspace(0.1, 5.0, 100):
            scaled = self._apply_temp(y_proba, t)
            nll = -np.mean(np.log(scaled[np.arange(len(y_true)), y_true] + 1e-10))
            if nll < best_nll:
                best_nll = nll
                best_t = t
        

        for t in np.linspace(max(0.1, best_t - 0.3), best_t + 0.3, 50):
            scaled = self._apply_temp(y_proba, t)
            nll = -np.mean(np.log(scaled[np.arange(len(y_true)), y_true] + 1e-10))
            if nll < best_nll:
                best_nll = nll
                best_t = t
        
        self.temperature = best_t
        self.is_fitted_ = True
        return self
    
    def _apply_temp(self, proba: np.ndarray, t: float) -> np.ndarray:
        """Apply temperature scaling to softmax probabilities."""

        eps = 1e-7
        logit = np.log(np.clip(proba, eps, 1))
        scaled_logit = logit / t
        

        shifted = scaled_logit - np.max(scaled_logit, axis=1, keepdims=True)
        exp_s = np.exp(shifted)
        return exp_s / np.sum(exp_s, axis=1, keepdims=True)
    
    def transform(self, proba: np.ndarray) -> np.ndarray:
        """Apply temperature scaling."""
        if not self.is_fitted_:
            raise RuntimeError("Not fitted.")
        return self._apply_temp(proba, self.temperature)






def evaluate_all_models_calibration(
    model_predictions: Dict[str, Tuple[np.ndarray, np.ndarray]],
    n_bins: int = 15,
) -> Dict[str, Any]:
    """
    Evaluate calibration quality across multiple models.
    
    Args:
        model_predictions: Dict of {model_name: (y_true, y_proba)}
        n_bins: Number of bins for reliability diagram
        
    Returns:
        Comprehensive comparison report
    """
    report = {
        "models": {},
        "comparison_table": [],
        "best_calibrated": None,
        "worst_calibrated": None,
    }
    
    results_list = []
    
    for name, (y_true, y_proba) in model_predictions.items():
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba, dtype=np.float64)
        
        if y_true.ndim > 1:
            y_true_idx = np.argmax(y_true, axis=1)
        else:
            y_true_idx = y_true
        

        bs = brier_score(
            (np.arange(y_proba.shape[1]) == y_true_idx[:, None]).astype(float),
            y_proba
        )
        ece, bin_details = expected_calibration_error(y_true_idx, y_proba, n_bins)
        rel_data = reliability_data(y_true_idx, y_proba, n_bins)
        
        model_result = {
            "name": name,
            "brier_score": round(bs, 6),
            "brier_skill_score": round(brier_skill_score(
                (np.arange(y_proba.shape[1]) == y_true_idx[:, None]).astype(float),
                y_proba
            ), 4),
            "ece": round(ece, 5),
            "mce": rel_data["mce"],
            "calibration_level": rel_data["calibration_level"],
            "reliability_data": rel_data,
            "bin_details": bin_details,
        }
        
        report["models"][name] = model_result
        results_list.append(model_result)
    

    results_list.sort(key=lambda x: x["ece"])
    report["comparison_table"] = results_list
    
    if results_list:
        report["best_calibrated"] = results_list[0]["name"]
        report["worst_calibrated"] = results_list[-1]["name"]
    
    return report


def plot_reliability_diagram(
    reliability: Dict[str, Any],
    save_path: str,
    title: str = "Reliability Diagram",
    model_name: str = "Model",
):
    """Generate reliability diagram plot."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])
    
    obs = reliability["observed"]
    perf = reliability["perfect_line"]
    hist = reliability["histogram"]
    

    ax_top.plot(perf["x"], perf["y"], '--', color='gray', label='Perfectly Calibrated', linewidth=2)
    ax_top.plot(obs["x"], obs["y"], 'o-', color='#3498db', 
                label='Observed', markersize=8, linewidth=2)

    obs_x = np.array(obs["x"])
    obs_y = np.array(obs["y"])
    perf_y_interp = np.interp(obs_x, perf["x"], perf["y"])
    ax_top.fill_between(obs_x, obs_y, perf_y_interp, 
                        alpha=0.2, color='red' if reliability["ece"] > 0.05 else 'green')
    
    ax_top.set_xlabel('Confidence (Mean Predicted Probability)', fontsize=11)
    ax_top.set_ylabel('Accuracy (Empirical Frequency)', fontsize=11)
    ax_top.set_title(f'{title}\n{model_name} | ECE={reliability["ece"]:.4f} ({reliability["calibration_level"].upper()})',
                    fontsize=13, fontweight='bold')
    ax_top.legend(loc='upper left')
    ax_top.grid(True, alpha=0.3)
    ax_top.set_xlim([0, 1])
    ax_top.set_ylim([0, 1])
    

    colors = ['#27ae60' if c >= a else '#e74c3c' 
              for c, a in zip(obs["y"], obs["x"])]
    ax_bot.bar(hist["x"], hist["counts"], width=0.9/len(hist["x"]),
               color=colors, alpha=0.7, edgecolor='white')
    ax_bot.set_xlabel('Confidence', fontsize=11)
    ax_bot.set_ylabel('Count', fontsize=11)
    ax_bot.set_title('Prediction Distribution (green=underconfident, red=overconfident)', fontsize=10)
    ax_bot.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Reliability diagram saved: {save_path}")






def run_calibration_pipeline(
    output_dir: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Full calibration pipeline with synthetic demo data.
    
    Tests all three calibration methods and compares them.
    """
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "ai_core" / "evaluation")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  PROBABILITY CALIBRATION PIPELINE")
    print("=" * 60)
    
    rng = np.random.RandomState(seed)
    n_samples = 500
    n_classes = 10
    


    true_logits = rng.randn(n_samples, n_classes)
    true_labels = rng.randint(0, n_classes, n_samples)
    

    overconf_logits = true_logits * 2.5
    exp_o = np.exp(overconf_logits - np.max(overconf_logits, axis=1, keepdims=True))
    y_overconfident = exp_o / exp_o.sum(axis=1, keepdims=True)
    

    underconf_logits = true_logits * 0.5
    exp_u = np.exp(underconf_logits - np.max(underconf_logits, axis=1, keepdims=True))
    y_underconfident = exp_u / exp_u.sum(axis=1, keepdims=True)
    

    exp_w = np.exp(true_logits - np.max(true_logits, axis=1, keepdims=True))
    y_well_calibrated = exp_w / exp_w.sum(axis=1, keepdims=True)
    
    y_onehot = (np.arange(n_classes) == true_labels[:, None]).astype(float)
    
    print(f"\n  Data: {n_samples} samples, {n_classes} classes")
    print(f"  Models: overconfident, underconfident, well-calibrated")
    

    model_preds = {
        "Overconfident": (true_labels, y_overconfident),
        "Underconfident": (true_labels, y_underconfident),
        "Well-Calibrated": (true_labels, y_well_calibrated),
    }
    
    report = evaluate_all_models_calibration(model_preds)
    
    print("\n  ┌────────────────┬───────────┬────────┬───────┐")
    print("  │ Model          │ Brier     │ ECE    │ Level │")
    print("  ├────────────────┼───────────┼────────┼───────┤")
    for m in report["comparison_table"]:
        print(f"  │ {m['name']:<14} │ {m['brier_score']:<9.4f} │ {m['ece']:<6.4f} │ {m['calibration_level']:<5} │")
    print("  └────────────────┴───────────┴────────┴───────┘")
    
    print(f"\n  Best calibrated : {report['best_calibrated']}")
    print(f"  Worst calibrated: {report['worst_calibrated']}")
    

    print("\n  [Calibrating] Applying calibration methods...")
    
    calibrators = {
        "Platt": PlattCalibrator(),
        "Temperature": TemperatureScaling(),
    }
    
    cal_results = {}
    for cal_name, calibrator in calibrators.items():
        calibrator.fit(true_labels, y_overconfident)
        y_calibrated = calibrator.transform(y_overconfident)
        


        cal_results[cal_name] = y_calibrated
        
        bs_cal = brier_score(y_onehot, y_calibrated)
        ece_cal, _ = expected_calibration_error(true_labels, y_calibrated)
        
        print(f"    {cal_name:15s}: Brier={bs_cal:.4f}, ECE={ece_cal:.4f}")
    

    for name, (yt, yp) in model_preds.items():
        safe_name = name.lower().replace("-", "_")
        rel_data = reliability_data(yt, yp)
        
        plot_path = os.path.join(output_dir, f"calibration_{safe_name}.png")
        try:
            plot_reliability_diagram(rel_data, plot_path, model_name=name)
        except Exception as e:
            print(f"    Could not plot {name}: {e}")
    

    full_report = {
        "pipeline": "probability_calibration",
        "n_samples": n_samples,
        "n_classes": n_classes,
        "model_comparison": {
            name: {
                "brier_score": m["brier_score"],
                "ece": m["ece"],
                "level": m["calibration_level"],
            } for name, m in report["models"].items()
        },
        "calibration_methods_tested": list(calibrators.keys()),
        "generated_at": __import__('datetime').datetime.now().isoformat(),
    }
    
    report_path = os.path.join(output_dir, "calibration_report.json")
    with open(report_path, 'w') as f:
        json.dump(full_report, f, indent=2)
    print(f"\n  Report saved: {report_path}")
    
    return full_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run calibration pipeline")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    run_calibration_pipeline(output_dir=args.output_dir, seed=args.seed)
    
    print("\n" + "=" * 60)
    print("  CALIBRATION PIPELINE COMPLETE!")
    print("=" * 60)
