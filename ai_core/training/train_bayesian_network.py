"""
Bayesian Network / Probabilistic Methods for Sahabat Aksara
==========================================================
Implementasi model probabilistic untuk handwriting evaluation:

  1. BayesianScorer — Gaussian Naive Bayes per feature per score bucket
     P(score | features) ∝ P(features | score) × P(score)
     
  2. Uncertainty Quantification — confidence interval, bukan point estimate
  
  3. Online Prior Update — update belief saat data baru masuk

Teori Matematis:
───────────────
  Posterior ∝ Likelihood × Prior

  P(S | f₁, f₂, ..., fₙ) = P(S) × ∏ᵢ P(fᵢ | S) / Z

  Dimana:
    S   = Score bucket (Low/Medium/High)
    fᵢ  = Fitur ke-i (dari PSD: HOG, Hu moments, histogram, dll)
    P(S) = Prior probability (histogram akurasi historis)
    P(fᵢ|S) = Likelihood (Gaussian distribution per fitur per bucket)
    Z   = Normalization constant (evidence)

  "Naive" = asumsi independen antar-fitur (tidak benar tapi bekerja baik!)

Keuntungan untuk Sahabat Aksara:
  - Output berupa DISTRIBUSI probabilitas, bukan angka tunggal
  - Bisa kasih uncertainty measure (berapa yakin?)
  - Mudah dijelaskan ke guru/non-technical user
  - Sangat cepat: training O(N×D), inference O(D)

Usage:
    python ai_core/training/train_bayesian_network.py
    python ai_core/training/train_bayesian_network.py --features data_science/datasets/exports/all_features.csv

Author: Sahabat Aksara AI Team (PKB-4 Phase 1)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np







SCORE_BUCKETS = {
    "low":      (0.0, 40.0),
    "medium":   (40.0, 70.0),
    "high":     (70.0, 100.0),
}

BUCKET_NAMES = ["low", "medium", "high"]
N_BUCKETS = len(BUCKET_NAMES)


DEFAULT_PRIOR = np.array([1/3, 1/3, 1/3])


EPSILON = 1e-6






class BayesianScorer:
    """
    Probabilistic scorer using Gaussian Naive Bayes approach.
    
    Instead of returning a single score like classical models,
    this returns a PROBABILITY DISTRIBUTION over score buckets:
        P(Low | features), P(Medium | features), P(High | features)
    
    From this distribution we derive:
        - Expected score (point estimate with uncertainty)
        - Confidence level (how certain is the model?)
        - Credible interval (range of likely scores)
    
    Attributes:
        means_: ndarray of shape (n_buckets, n_features)
            Mean of each feature within each score bucket.
        vars_: ndarray of shape (n_buckets, n_features)
            Variance of each feature within each score bucket.
        priors_: ndarray of shape (n_buckets,)
            Prior probability of each score bucket.
        feature_names_: list of str
            Names of features used for training.
        is_fitted_: bool
            Whether the model has been trained.
    """
    
    def __init__(self, n_buckets: int = N_BUCKETS, var_smoothing: float = 1e-3):
        """
        Initialize BayesianScorer.
        
        Args:
            n_buckets: Number of score buckets (default: 3: low/med/high)
            var_smoothing: Minimum variance to prevent numerical issues
        """
        self.n_buckets = n_buckets
        self.var_smoothing = var_smoothing
        

        self.means_ = None
        self.vars_ = None
        self.priors_ = None
        self.feature_names_ = None
        self.bucket_edges_ = list(SCORE_BUCKETS.values())
        
        self.is_fitted_ = False
    
    def _discretize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Convert continuous accuracy scores into bucket indices.
        
        Args:
            scores: Array of accuracy values in [0, 100]
            
        Returns:
            Array of bucket indices (0, 1, or 2)
        """
        buckets = np.digitize(scores, 
                               bins=[self.bucket_edges_[0][1], self.bucket_edges_[1][1]])
        return buckets
    
    def _bucket_name(self, idx: int) -> str:
        """Convert bucket index to name."""
        return BUCKET_NAMES[idx] if idx < len(BUCKET_NAMES) else f"bucket_{idx}"
    
    def fit(self, X: np.ndarray, y_scores: np.ndarray,
            feature_names: Optional[List[str]] = None,
            sample_weights: Optional[np.ndarray] = None) -> 'BayesianScorer':
        """
        Train the Bayesian Scorer on feature data and accuracy scores.
        
        Computes Gaussian parameters (mean, variance) for each feature
        within each score bucket, plus prior probabilities.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features)
            y_scores: Accuracy scores (0-100) for each sample
            feature_names: Optional names for each feature column
            sample_weights: Optional weights per sample
            
        Returns:
            self (fitted model)
        """
        X = np.asarray(X, dtype=np.float64)
        y_scores = np.asarray(y_scores, dtype=np.float64)
        
        n_samples, n_features = X.shape
        self.feature_names_ = feature_names or [f"feature_{i}" for i in range(n_features)]
        

        y_buckets = self._discretize_scores(y_scores)
        

        if sample_weights is not None:
            weights = np.asarray(sample_weights, dtype=np.float64)
            self.priors_ = np.array([
                np.sum(weights[y_buckets == k]) for k in range(self.n_buckets)
            ])
        else:
            self.priors_ = np.array([
                np.sum(y_buckets == k) for k in range(self.n_buckets)
            ], dtype=np.float64)
        

        self.priors_ = (self.priors_ + EPSILON) / (self.priors_.sum() + EPSILON * self.n_buckets)
        

        self.means_ = np.zeros((self.n_buckets, n_features))
        self.vars_ = np.zeros((self.n_buckets, n_features))
        
        for k in range(self.n_buckets):
            mask = (y_buckets == k)
            if np.sum(mask) > 0:
                X_k = X[mask]
                if sample_weights is not None:
                    w_k = weights[mask]
                    self.means_[k] = np.average(X_k, axis=0, weights=w_k)

                    diff = X_k - self.means_[k]
                    self.vars_[k] = np.average(diff**2, axis=0, weights=w_k)
                else:
                    self.means_[k] = np.mean(X_k, axis=0)
                    self.vars_[k] = np.var(X_k, axis=0, ddof=1)
            

            self.vars_[k] = np.maximum(self.vars_[k], self.var_smoothing)
        
        self.is_fitted_ = True
        return self
    
    def _gaussian_log_prob(self, x: np.ndarray, mean: np.ndarray, 
                            var: np.ndarray) -> np.ndarray:
        """Compute log PDF of Gaussian distribution."""
        return -0.5 * (np.log(2 * np.pi * var) + (x - mean)**2 / var)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute posterior probability distribution over score buckets.
        
        P(bucket | features) ∝ P(bucket) × ∏ᵢ P(fᵢ | bucket)
        
        Uses log-space computation for numerical stability.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features)
            
        Returns:
            Probability matrix of shape (n_samples, n_buckets)
            Each row sums to 1.0
        """
        if not self.is_fitted_:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        X = np.asarray(X, dtype=np.float64)
        n_samples = X.shape[0]
        

        log_posteriors = np.zeros((n_samples, self.n_buckets))
        
        for k in range(self.n_buckets):

            log_posteriors[:, k] = np.log(self.priors_[k] + EPSILON)
            

            log_likelihoods = self._gaussian_log_prob(
                X, self.means_[k], self.vars_[k]
            )
            log_posteriors[:, k] += np.sum(log_likelihoods, axis=1)
        

        max_log = np.max(log_posteriors, axis=1, keepdims=True)
        log_posteriors -= max_log
        posteriors = np.exp(log_posteriors)
        posteriors /= posteriors.sum(axis=1, keepdims=True)
        
        return posteriors
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict the most likely score bucket for each sample.
        
        Returns expected score value (weighted average of bucket centers).
        
        Args:
            X: Feature matrix
            
        Returns:
            Expected scores array of shape (n_samples,)
        """
        proba = self.predict_proba(X)
        

        bucket_centers = np.array([
            (SCORE_BUCKETS[name][0] + SCORE_BUCKETS[name][1]) / 2
            for name in BUCKET_NAMES[:self.n_buckets]
        ])
        
        expected_scores = proba @ bucket_centers
        return expected_scores
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Predict with full uncertainty quantification.
        
        Returns dict with:
            - expected_score: Point estimate (expected value)
            - std_deviation: Standard deviation of score distribution
            - confidence: Confidence level (high/medium/low)
            - credible_interval: 95% credible interval (low, high)
            - probabilities: Full distribution over buckets
            - entropy: Shannon entropy (higher = more uncertain)
        
        Args:
            X: Single sample (1D array) or multiple samples (2D array)
            
        Returns:
            Dict with prediction + uncertainty info
        """
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        proba = self.predict_proba(X)
        results = []
        
        bucket_centers = np.array([
            (SCORE_BUCKETS[name][0] + SCORE_BUCKETS[name][1]) / 2
            for name in BUCKET_NAMES[:self.n_buckets]
        ])
        
        for i in range(len(X)):
            p = proba[i]
            expected = float(p @ bucket_centers)
            

            variance = float(p @ (bucket_centers ** 2)) - expected ** 2
            std_dev = max(0, np.sqrt(variance))
            

            entropy = float(-np.sum(p * np.log(p + EPSILON)))
            max_entropy = np.log(self.n_buckets)
            normalized_entropy = entropy / max_entropy
            

            if normalized_entropy < 0.3:
                confidence = "high"
            elif normalized_entropy < 0.6:
                confidence = "medium"
            else:
                confidence = "low"
            

            cumsum = np.cumsum(p)
            low_idx = np.searchsorted(cumsum, 0.025)
            high_idx = np.searchsorted(cumsum, 0.975)
            ci_low = SCORE_BUCKETS[self._bucket_name(low_idx)][0] if low_idx < self.n_buckets else 0
            ci_high = SCORE_BUCKETS[self._bucket_name(min(high_idx, self.n_buckets-1))][1]
            
            results.append({
                "expected_score": round(expected, 2),
                "std_deviation": round(std_dev, 2),
                "confidence": confidence,
                "entropy": round(entropy, 4),
                "normalized_entropy": round(normalized_entropy, 4),
                "credible_interval_95": [round(ci_low, 1), round(ci_high, 1)],
                "probabilities": {
                    self._bucket_name(k): round(float(p[k]), 4)
                    for k in range(self.n_buckets)
                },
                "prediction_bucket": self._bucket_name(np.argmax(p)),
            })
        
        if len(results) == 1:
            return results[0]
        return results
    
    def update_prior(self, new_scores: np.ndarray, 
                     learning_rate: float = 0.1) -> 'BayesianScorer':
        """
        Online prior update with new observations (Bayesian learning).
        
        P_new(S) = (1-α) × P_old(S) + α × P_observed(S)
        
        This allows the model to adapt as more evaluation data comes in.
        
        Args:
            new_scores: New accuracy scores observed
            learning_rate: How fast to adapt (0=don't change, 1=replace entirely)
            
        Returns:
            self (updated model)
        """
        if not self.is_fitted_:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        new_scores = np.asarray(new_scores, dtype=np.float64)
        new_buckets = self._discretize_scores(new_scores)
        

        observed_priors = np.array([
            np.sum(new_buckets == k) for k in range(self.n_buckets)
        ], dtype=np.float64)
        observed_priors /= observed_priors.sum()
        

        self.priors_ = (1 - learning_rate) * self.priors_ + learning_rate * observed_priors
        

        self.priors_ /= self.priors_.sum()
        
        return self
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Compute which features are most discriminative between buckets.
        
        Uses F-ratio (ANOVA-style): variance between buckets / variance within buckets.
        Higher = more important for distinguishing score levels.
        
        Returns:
            Dict mapping feature name to importance score
        """
        if not self.is_fitted_:
            raise RuntimeError("Model not fitted.")
        
        overall_mean = np.mean(self.means_, axis=0)
        between_var = np.sum(
            self.priors_[:, np.newaxis] * (self.means_ - overall_mean)**2,
            axis=0
        )
        within_var = np.mean(self.vars_, axis=0)
        

        f_ratio = between_var / (within_var + EPSILON)
        
        importance = {
            name: round(float(score), 4)
            for name, score in zip(self.feature_names_, f_ratio)
        }
        

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    def explain_prediction(self, x: np.ndarray, top_k: int = 5) -> str:
        """
        Generate human-readable explanation of why a prediction was made.
        
        Compares the input features against each bucket's typical values
        and highlights which features pushed toward/away from each outcome.
        
        Args:
            x: Input feature vector (1D)
            top_k: Number of most influential features to show
            
        Returns:
            Explanation string in Bahasa Indonesia
        """
        if not self.is_fitted_:
            raise RuntimeError("Model not fitted.")
        
        x = np.asarray(x, dtype=np.float64).flatten()
        result = self.predict_with_uncertainty(x)
        proba = self.predict_proba(x.reshape(1, -1))[0]
        
        lines = []
        lines.append("=" * 55)
        lines.append("  PREDIKSI BAYESIAN — PENJELASAN")
        lines.append("=" * 55)
        lines.append(f"  Skor Ekspektasi : {result['expected_score']:.1f}%")
        lines.append(f"  Tingkat Keyakinan : {result['confidence'].upper()}")
        lines.append(f"  Rentang 95%       : {result['credible_interval_95'][0]:.0f}% - {result['credible_interval_95'][1]:.0f}%")
        lines.append("")
        lines.append("  Distribusi Probabilitas:")
        for bname, p in result['probabilities'].items():
            bar_len = int(p * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            lines.append(f"    {bname:8s} │ {bar} {p*100:.1f}%")
        

        lines.append("")
        lines.append("  Fitur Paling Berpengaruh:")
        

        z_scores = {}
        for j, fname in enumerate(self.feature_names_):
            best_bucket = np.argmax(proba)
            z = abs(x[j] - self.means_[best_bucket, j]) / (np.sqrt(self.vars_[best_bucket, j]) + EPSILON)
            z_scores[fname] = z
        
        top_features = sorted(z_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        for rank, (fname, z) in enumerate(top_features, 1):
            val = x[j] if isinstance(x[j], (int, float)) else x[list(self.feature_names_).index(fname)]
            idx = list(self.feature_names_).index(fname)
            val = x[idx]
            best_b = np.argmax(proba)
            direction = "lebih tinggi" if val > self.means_[best_b, idx] else "lebih rendah"
            lines.append(f"    {rank}. {fname}")
            lines.append(f"       Nilai: {val:.4f} ({direction} dari rata-rata)")
        

        pred_bucket = result['prediction_bucket']
        if pred_bucket == "high":
            tip = "🌟 Hebat! Tulisan kamu sudah sangat bagus!"
        elif pred_bucket == "medium":
            tip = "👍 Bagus! Terus latihan ya biar makin sempurna!"
        else:
            tip = "💪 Jangan menyerah! Coba tulis pelan-pelan dengan teliti."
        
        lines.append("")
        lines.append(f"  💡 Tips: {tip}")
        lines.append("=" * 55)
        
        return "\n".join(lines)
    
    def save(self, path: str) -> None:
        """Save model parameters to JSON file."""
        if not self.is_fitted_:
            raise RuntimeError("Cannot save unfitted model.")
        
        data = {
            "n_buckets": self.n_buckets,
            "var_smoothing": self.var_smoothing,
            "means": self.means_.tolist(),
            "vars": self.vars_.tolist(),
            "priors": self.priors_.tolist(),
            "feature_names": self.feature_names_,
            "bucket_edges": self.bucket_edges_,
        }
        
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'BayesianScorer':
        """Load model from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model = cls(n_buckets=data["n_buckets"], var_smoothing=data["var_smoothing"])
        model.means_ = np.array(data["means"])
        model.vars_ = np.array(data["vars"])
        model.priors_ = np.array(data["priors"])
        model.feature_names_ = data["feature_names"]
        model.bucket_edges_ = data["bucket_edges"]
        model.is_fitted_ = True
        return model






def generate_synthetic_training_data(
    n_samples: int = 500,
    n_features: int = 20,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for Bayesian Scorer demo.
    
    Creates realistic-looking feature vectors with known score relationships
    so the model can learn meaningful patterns.
    
    Features are designed to correlate with handwriting quality:
        - aspect_ratio: Closer to ideal → higher score
        - stroke_density: Moderate density → higher score
        - center_of_mass: Centered → higher score
        - symmetry: More symmetric → higher score
        - etc.
    
    Args:
        n_samples: Number of samples to generate
        n_features: Number of features per sample
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (X features, y scores)
    """
    rng = np.random.RandomState(seed)
    

    quality = rng.uniform(0, 1, n_samples)
    

    X = np.zeros((n_samples, n_features))
    

    X[:, 0] = 0.5 + 0.5 * quality + rng.normal(0, 0.15, n_samples)
    X[:, 0] = np.clip(X[:, 0], 0.2, 2.0)
    

    X[:, 1] = 0.3 + 0.4 * quality + rng.normal(0, 0.1, n_samples)
    X[:, 1] = np.clip(X[:, 1], 0.05, 0.9)
    

    X[:, 2] = quality + rng.normal(0, 0.15, n_samples)
    X[:, 2] = np.clip(X[:, 2], 0, 1)
    

    X[:, 3] = 0.3 + 0.6 * quality + rng.normal(0, 0.12, n_samples)
    X[:, 3] = np.clip(X[:, 3], 0, 1)
    

    X[:, 4] = 0.2 + 0.6 * quality + rng.normal(0, 0.13, n_samples)
    X[:, 4] = np.clip(X[:, 4], 0, 1)
    

    for j in range(5, n_features):
        signal_strength = 0.3 * (1 - j / n_features)
        X[:, j] = 0.5 + signal_strength * quality + rng.normal(0, 0.2, n_samples)
        X[:, j] = np.clip(X[:, j], -1, 2)
    

    base_scores = quality * 90 + 5
    noise = rng.normal(0, 10, n_samples)
    y = np.clip(base_scores + noise, 0, 100)
    
    feature_names = [
        "aspect_ratio", "stroke_density", "centeredness", "symmetry",
        "stroke_uniformity"
    ] + [f"feature_{j}" for j in range(5, n_features)]
    
    return X, y, feature_names






def train_bayesian_pipeline(
    X: Optional[np.ndarray] = None,
    y: Optional[np.ndarray] = None,
    output_dir: Optional[str] = None,
    n_synthetic: int = 500,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Full training pipeline for Bayesian Scorer.
    
    Args:
        X: Feature matrix (None = use synthetic data)
        y: Score labels (None = use synthetic data)
        output_dir: Directory to save model artifacts
        n_synthetic: Number of synthetic samples if no real data
        seed: Random seed
        
    Returns:
        Training results dictionary
    """
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "ai_core" / "models" / "bayesian")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  BAYESIAN SCORER TRAINING PIPELINE")
    print("=" * 60)
    

    if X is None or y is None:
        print(f"\n  [Data] Generating {n_synthetic} synthetic samples...")
        X, y, feature_names = generate_synthetic_training_data(
            n_samples=n_synthetic, n_features=20, seed=seed
        )
    else:
        feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    
    print(f"  Features  : {X.shape[1]}")
    print(f"  Samples   : {X.shape[0]}")
    print(f"  Score range: {y.min():.1f} - {y.max():.1f}")
    print(f"  Score mean : {y.mean():.1f}")
    

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    

    print("\n  [Training] Fitting Bayesian Scorer...")
    model = BayesianScorer()
    model.fit(X_train, y_train, feature_names=feature_names)
    

    print("  [Evaluating] on test set...")
    predictions = model.predict(X_test)
    

    mae = np.mean(np.abs(predictions - y_test))
    rmse = np.sqrt(np.mean((predictions - y_test)**2))
    

    test_buckets = model._discretize_scores(y_test)
    pred_proba = model.predict_proba(X_test)
    pred_buckets = np.argmax(pred_proba, axis=1)
    bucket_acc = np.mean(test_buckets == pred_buckets)
    
    print(f"\n  ──────────────────────────────────────")
    print(f"  MAE (Mean Absolute Error)  : {mae:.2f}")
    print(f"  RMSE (Root Mean Sq Error)  : {rmse:.2f}")
    print(f"  Bucket Accuracy             : {bucket_acc*100:.1f}%")
    

    uncertainties = model.predict_with_uncertainty(X_test)
    if isinstance(uncertainties, list):
        avg_std = np.mean([u['std_deviation'] for u in uncertainties])
    else:
        avg_std = uncertainties['std_deviation']
    print(f"  Avg Uncertainty (σ)         : {avg_std:.2f}")
    

    importance = model.get_feature_importance()
    print(f"\n  Top-5 Fitur Paling Penting:")
    for i, (fname, imp) in enumerate(list(importance.items())[:5], 1):
        print(f"    {i}. {fname}: {imp:.4f}")
    

    print(f"\n  Contoh Penjelasan Prediksi:")
    print(model.explain_prediction(X_test[0]))
    

    model_path = os.path.join(output_dir, "bayesian_scorer.json")
    model.save(model_path)
    print(f"\n  Model saved: {model_path}")
    

    report = {
        "model_type": "BayesianScorer (Gaussian Naive Bayes)",
        "n_features": X.shape[1],
        "n_samples": {"train": len(X_train), "test": len(X_test)},
        "metrics": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "bucket_accuracy": round(bucket_acc, 4),
            "avg_uncertainty": round(avg_std, 4),
        },
        "top_features": dict(list(importance.items())[:10]),
        "priors": {BUCKET_NAMES[k]: round(float(model.priors_[k]), 4) 
                   for k in range(model.n_buckets)},
        "trained_at": __import__('datetime').datetime.now().isoformat(),
    }
    
    report_path = os.path.join(output_dir, "training_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")
    
    return {
        "model": model,
        "metrics": report["metrics"],
        "report": report,
        "model_path": model_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Bayesian Scorer")
    parser.add_argument("--features", type=str, default=None,
                        help="Path to features CSV file")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--samples", type=int, default=500,
                        help="Number of synthetic samples")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    args = parser.parse_args()
    
    X = y = None
    if args.features and Path(args.features).exists():
        import pandas as pd
        df = pd.read_csv(args.features)

        target_cols = [c for c in df.columns if c.lower() in 
                       ('score', 'accuracy', 'label', 'target', 'class')]
        if target_cols:
            y = df[target_cols[0]].values
            X = df.drop(columns=target_cols).values
        else:
            X = df.values
            y = None
    
    results = train_bayesian_pipeline(
        X=X, y=y,
        output_dir=args.output_dir,
        n_synthetic=args.samples,
        seed=args.seed,
    )
    
    print("\n" + "=" * 60)
    print("  BAYESIAN SCORER TRAINING COMPLETE!")
    print("=" * 60)
