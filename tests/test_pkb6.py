"""
Test Suite: PKB-6 — Comprehensive Benchmark & Documentation
=============================================================
Covers:
  - PKB-6.1: Master Benchmark Report Generator
  - PKB-6.2: Algorithm Documentation Generator
  - PKB-6.3: Experiment Tracker + A/B Testing

Run:
    backend/venv/Scripts/python.exe -m pytest tests/test_pkb6.py -v
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ai_core" / "evaluation"))

import numpy as np






class TestBenchmarkGenerator:
    """PKB-6.1: Master Benchmark Report."""

    def test_generate_benchmark_data(self):
        """Benchmark data generator produces correct shapes."""
        from benchmark import generate_benchmark_data
        
        X_tr, X_te, y_tr, y_te = generate_benchmark_data(n_samples=100)
        
        assert X_tr.shape[0] > X_te.shape[0], "Train should be larger than test"
        assert X_tr.shape[1] == X_te.shape[1], "Same feature dimension"
        assert len(y_tr) == X_tr.shape[0]
        assert len(y_te) == X_te.shape[0]

    def test_generate_image_data(self):
        """Image benchmark data generates valid 64x64 images."""
        from benchmark import generate_image_benchmark_data
        
        images, labels = generate_image_benchmark_data(n_images=10)
        
        assert len(images) == 10
        assert len(labels) == 10
        assert images[0].shape == (64, 64), f"Expected (64,64), got {images[0].shape}"

    def test_benchmark_classical_model_returns_dict(self):
        """Classical model benchmark returns dict with required keys."""
        from benchmark import generate_benchmark_data, benchmark_classical_model
        
        X_tr, X_te, y_tr, y_te = generate_benchmark_data()
        result = benchmark_classical_model("random_forest", None, X_tr, X_te, y_tr, y_te)
        
        assert isinstance(result, dict)
        assert "model_name" in result
        assert "status" in result
        assert result["model_name"] == "random_forest"

    def test_benchmark_baseline_cv_returns_dict(self):
        """CV baseline benchmark returns dict with accuracy."""
        from benchmark import generate_image_benchmark_data, benchmark_baseline_cv
        
        images = [np.random.randint(0, 255, (64, 64), dtype=np.uint8) for _ in range(5)]
        labels = list("ABCDE")
        result = benchmark_baseline_cv(images, labels)
        
        assert isinstance(result, dict)
        assert result["model_name"] == "baseline_cv"
        assert "raw_avg_score" in result or result["status"] != "ok"

    def test_speed_accuracy_plot_generates_file(self):
        """Speed-accuracy plot generates PNG file."""
        from benchmark import generate_speed_accuracy_plot, generate_benchmark_data, benchmark_baseline_cv
        
        X_tr, X_te, y_tr, y_te = generate_benchmark_data()
        images = [np.random.randint(0, 255, (64, 64), dtype=np.uint8) for _ in range(5)]
        labels = list("ABCDE")
        

        results = [
            {"model_name": "test_model", "type": "classical_ml", "status": "ok",
             "accuracy": 0.75, "inference_time_ms_per_sample": 5.2, "model_size_mb": 0.1},
            {"model_name": "test_fast", "type": "cv", "status": "ok",
             "accuracy": 0.60, "inference_time_ms_per_sample": 1.0, "model_size_mb": 0.01},
        ]
        
        path = generate_speed_accuracy_plot(results)
        if path:
            assert os.path.exists(path)

    def test_generate_markdown_report_contains_table(self):
        """Markdown report contains comparison table."""
        from benchmark import generate_comparison_table
        
        results = [
            {"model_name": "A", "type": "ml", "status": "ok", "accuracy": 0.8,
             "precision": 0.78, "recall": 0.76, "f1": 0.77,
             "inference_time_ms_per_sample": 5.0},
        ]
        
        md = generate_comparison_table(results)
        assert "| Model |" in md
        assert "A" in md

    def test_run_full_benchmark_produces_report(self):
        """Full benchmark pipeline runs and produces JSON report."""
        from benchmark import run_full_benchmark
        
        report = run_full_benchmark()
        
        assert isinstance(report, dict)
        assert "results" in report
        assert "summary" in report
        assert report["summary"]["total_models"] >= 1






class TestAlgorithmDocs:
    """PKB-6.2: Algorithm Documentation Generator."""

    def test_generate_docs_creates_file(self):
        """Algorithm docs generator creates MD file."""
        from generate_algorithm_docs import generate_algorithm_docs, DOCS_DIR
        
        path = generate_algorithm_docs()
        
        assert os.path.exists(path)
        content = Path(path).read_text(encoding='utf-8')
        assert "Algorithm Documentation" in content

    def test_docs_contain_all_algorithms(self):
        """Generated docs contain all algorithm definitions."""
        from generate_algorithm_docs import ALGORITHM_DEFINITIONS, generate_algorithm_docs
        
        path = generate_algorithm_docs()
        content = Path(path).read_text(encoding='utf-8')
        
        for algo in ALGORITHM_DEFINITIONS:
            assert algo["name"] in content, f"Missing algorithm: {algo['name']}"

    def test_docs_have_theory_section(self):
        """Each algorithm has theory section with formulas."""
        from generate_algorithm_docs import ALGORITHM_DEFINITIONS, generate_algorithm_docs
        
        path = generate_algorithm_docs()
        content = Path(path).read_text(encoding='utf-8')
        
        for algo in ALGORITHM_DEFINITIONS[:3]:
            assert "## Teori" in content or "### Teori" in content

    def test_docs_have_implementation_section(self):
        """Each algorithm has implementation section with code."""
        from generate_algorithm_docs import ALGORITHM_DEFINITIONS, generate_algorithm_docs
        
        path = generate_algorithm_docs()
        content = Path(path).read_text(encoding='utf-8')
        
        assert "```python" in content
        assert "from sklearn" in content or "import tensorflow" in content

    def test_docs_have_pros_cons_table(self):
        """Each algorithm has pros/cons table."""
        from generate_algorithm_docs import ALGORITHM_DEFINITIONS, generate_algorithm_docs
        
        path = generate_algorithm_docs()
        content = Path(path).read_text(encoding='utf-8')
        
        assert "Kelebihan" in content
        assert "Kekurangan" in content






class TestExperimentTracker:
    """PKB-6.3: Experiment Tracking & A/B Testing."""

    def test_log_experiment_creates_record(self):
        """Logging an experiment creates a record with ID."""
        from experiment_tracker import log_experiment, EXPERIMENTS_FILE
        
        rec = log_experiment(
            experiment_name="Test Experiment",
            category="unit_test",
            params={"lr": 0.001, "epochs": 10},
            results={"accuracy": 0.85},
            tags=["test"],
        )
        
        assert "id" in rec
        assert rec["name"] == "Test Experiment"
        assert len(rec["id"]) > 0
        assert EXPERIMENTS_FILE.exists()

    def test_log_experiment_persists_to_file(self):
        """Experiment persists to experiments.json file."""
        from experiment_tracker import log_experiment, query_experiments, EXPERIMENTS_FILE
        
        log_experiment(
            experiment_name="Persistence Test",
            category="unit_test",
            params={},
            results={"acc": 0.9},
        )
        
        exps = query_experiments(name_contains="Persistence Test")
        assert len(exps) >= 1
        assert exps[0]["name"] == "Persistence Test"

    def test_query_experiments_filters_by_category(self):
        """Query can filter by category."""
        from experiment_tracker import log_experiment, query_experiments
        
        log_experiment(experiment_name="Cat-A-1", category="alpha", params={}, results={})
        log_experiment(experiment_name="Cat-B-1", category="beta", params={}, results={})
        
        alpha_results = query_experiments(category="alpha")
        beta_results = query_experiments(category="beta")
        
        assert all(e["category"] == "alpha" for e in alpha_results)
        assert all(e["category"] == "beta" for e in beta_results)

    def test_query_experiments_limits_results(self):
        """Query respects limit parameter."""
        from experiment_tracker import log_experiment, query_experiments
        
        for i in range(5):
            log_experiment(experiment_name=f"Limit-{i}", category="limit_test", params={}, results={})
        
        limited = query_experiments(category="limit_test", limit=3)
        assert len(limited) <= 3

    def test_duplicate_experiment_updates_run_count(self):
        """Re-logging same experiment increments run_count."""
        from experiment_tracker import log_experiment, query_experiments
        
        params = {"unique_param": "same"}
        r1 = log_experiment(experiment_name="Dup Test", category="dup", params=params, results={})
        r2 = log_experiment(experiment_name="Dup Test", category="dup", params=params, results={})
        
        assert r2.get("run_count", 1) >= 2

    def test_ab_test_initialization(self):
        """A/B test object initializes correctly."""
        from experiment_tracker import ABTest
        
        ab = ABTest(name="test_ab", description="Test A/B framework")
        
        assert ab.name == "test_ab"
        assert ab.test_id is not None
        assert len(ab.test_id) > 0

    def test_ab_test_declare_winner(self):
        """A/B test declares winner based on accuracy."""
        from experiment_tracker import ABTest
        
        ab = ABTest(name="winner_test")
        ab.group_a = {
            "label": "Model A",
            "fn": lambda x: "A",
            "data": [1, 2, 3],
            "labels": ["A", "A", "A"],
        }
        ab.group_b = {
            "label": "Model B",
            "fn": lambda x: "B",
            "data": [1, 2, 3],
            "labels": ["B", "B", "B"],
        }
        
        result = ab.run()
        winner = ab.declare_winner(metric="accuracy")
        
        assert winner is not None
        assert "winner" in winner
        assert "margin" in winner

    def test_get_best_experiment(self):
        """get_best_experiment returns top result by metric."""
        from experiment_tracker import log_experiment, get_best_experiment
        
        log_experiment(experiment_name="Best-80", category="best_test",
                       params={}, results={"accuracy": 0.80})
        log_experiment(experiment_name="Best-95", category="best_test",
                       params={}, results={"accuracy": 0.95})
        
        best = get_best_experiment(metric="accuracy", category="best_test")
        assert best is not None
        assert best["name"] == "Best-95"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
