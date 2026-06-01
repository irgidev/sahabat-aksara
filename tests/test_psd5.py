"""
Test Suite: PSD-5 — Automated Pipeline & Reporting
====================================================
Covers:
  - PSD-5.1: Export for Training (stratified split, save, report)
  - PSD-5.2: Pipeline Trigger + Status endpoints
  - PSD-5.3: Auto-Report Generator (analysis, HTML, recommendations)
  - PSD-5.4: Data Quality Monitor endpoint

Run:
    backend/venv/Scripts/python.exe -m pytest tests/test_psd5.py -v
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data_science" / "scripts"))

import numpy as np






def _make_synthetic_data(n=200, n_features=20, n_classes=5):
    """Create synthetic data for testing."""
    rng = np.random.RandomState(42)
    X = rng.randn(n, n_features) * 2
    centers = rng.randn(n_classes, n_features) * 1.5
    y = np.array([f"class_{i % n_classes}" for i in range(n)])
    for i in range(n):
        cls_idx = i % n_classes
        X[i] = X[i] * 0.3 + centers[cls_idx] + rng.randn(n_features) * 0.5
    feature_names = [f"feature_{i}" for i in range(n_features)]
    return X, y, feature_names






class TestExportForTraining:
    """PSD-5.1: Train/Test Split & Dataset Preparation."""

    def test_stratified_split_basic(self):
        """Stratified split preserves class proportions."""
        from export_for_training import stratified_train_test_split
        X, y, fnames = _make_synthetic_data(n=200, n_classes=5)
        X_tr, X_te, y_tr, y_te, info = stratified_train_test_split(X, y, test_ratio=0.2)

        assert len(X_tr) + len(X_te) == len(X), "Total samples must be preserved"
        assert len(y_tr) > len(y_te), "Train should be larger than test"
        assert info["strategy"] in ("stratified", "random"), f"Unexpected strategy: {info['strategy']}"
        assert info["train_size"] == len(y_tr)
        assert info["test_size"] == len(y_te)

    def test_stratified_split_ratio(self):
        """Test ratio is approximately correct (within tolerance)."""
        from export_for_training import stratified_train_test_split
        X, y, fnames = _make_synthetic_data(n=100, n_classes=3)
        _, _, _, _, info = stratified_train_test_split(X, y, test_ratio=0.25)

        expected_test = int(100 * 0.25)
        actual_test = info["test_size"]
        assert abs(actual_test - expected_test) <= 1, \
            f"Expected ~{expected_test} test samples, got {actual_test}"

    def test_stratified_split_balance(self):
        """Balance score should be high for well-stratified data."""
        from export_for_training import stratified_train_test_split
        X, y, fnames = _make_synthetic_data(n=300, n_classes=5)
        _, _, _, _, info = stratified_train_test_split(X, y, test_ratio=0.2)

        assert info.get("balance_score", 0) >= 0.7, \
            f"Balance score too low: {info.get('balance_score')}"

    def test_single_class_fallback(self):
        """Single-class data should fall back to random split without error."""
        from export_for_training import stratified_train_test_split
        X = np.random.randn(50, 10)
        y = np.array(["only_class"] * 50)

        X_tr, X_te, y_tr, y_te, info = stratified_train_test_split(X, y, test_ratio=0.2)

        assert len(X_tr) > 0 and len(X_te) > 0
        assert "random" in info["strategy"].lower()

    def test_save_splits_csv(self):
        """Saving splits creates CSV files with correct shape."""
        from export_for_training import save_splits
        X, y, fnames = _make_synthetic_data(n=60, n_features=8)

        import tempfile
        tmpdir = Path(tempfile.mkdtemp())

        try:
            saved = save_splits(
                X[:48], X[12:], y[:48], y[12:], fnames,
                output_dir=tmpdir, fmt="csv"
            )

            assert "train_csv" in saved
            assert "test_csv" in saved

            import pandas as pd
            train_df = pd.read_csv(saved["train_csv"])
            assert train_df.shape[0] == 48
            assert "label" in train_df.columns
            assert len(train_df.columns) == len(fnames) + 1
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_save_splits_npy(self):
        """Saving splits also creates NPY files when fmt='both'."""
        from export_for_training import save_splits
        X, y, fnames = _make_synthetic_data(n=40, n_features=5)

        import tempfile
        tmpdir = Path(tempfile.mkdtemp())

        try:
            saved = save_splits(
                X[:32], X[8:], y[:32], y[8:], fnames,
                output_dir=tmpdir, fmt="both"
            )

            assert "train_npy" in saved
            assert "test_npy" in saved
            assert os.path.exists(saved["train_npy"])

            loaded = np.load(saved["train_npy"])
            assert loaded.shape == (32, 5)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_generate_split_report(self):
        """Split report contains all required sections."""
        from export_for_training import generate_split_report

        split_info = {
            "total_samples": 100,
            "test_ratio": 0.2,
            "n_classes": 5,
            "strategy": "stratified",
            "train_size": 80,
            "test_size": 20,
            "class_distribution_before": {"A": 20, "B": 20, "C": 20, "D": 20, "E": 20},
            "train_distribution": {"A": 16, "B": 16, "C": 16, "D": 16, "E": 16},
            "test_distribution": {"A": 4, "B": 4, "C": 4, "D": 4, "E": 4},
            "balance_score": 0.95,
            "warnings": [],
        }

        report = generate_split_report(split_info, {"train_csv": "/tmp/train.csv"}, elapsed_sec=1.23)

        assert report["status"] == "success"
        assert report["split_config"]["test_ratio"] == 0.2
        assert report["dataset_summary"]["train_size"] == 80
        assert report["dataset_summary"]["test_size"] == 20
        assert report["processing_time_sec"] == 1.23

    def test_synthetic_dataset_generation(self):
        """Synthetic dataset has correct shape and multiple classes."""
        from export_for_training import generate_synthetic_dataset

        X, y, fnames, meta = generate_synthetic_dataset(n_samples=150, n_features=15, n_classes=6)

        assert X.shape == (150, 15)
        assert len(y) == 150
        assert meta["n_classes"] == 6
        assert len(fnames) == 15

    def test_run_export_pipeline_full(self):
        """Full pipeline runs end-to-end without error."""
        from export_for_training import run_export_pipeline

        result = run_export_pipeline(test_ratio=0.25, use_synthetic=True)

        assert result["status"] == "success"
        assert "dataset_summary" in result
        assert result["dataset_summary"]["train_size"] > 0
        assert result["dataset_summary"]["test_size"] > 0






class TestAutoReportGenerator:
    """PSD-5.3: Weekly/Monthly Report Generation."""

    def test_collect_exercise_data_returns_records(self):
        """Data collector returns a list of records with source indicator."""
        from generate_reports import collect_exercise_data

        records, source = collect_exercise_data(days_back=7)

        assert isinstance(records, list)
        assert isinstance(source, str)
        assert source in ("supabase", "synthetic")
        if source == "synthetic":
            assert len(records) > 0, "Synthetic should always return data"

    def test_compute_progress_summary_structure(self):
        """Progress summary has all required keys."""
        from generate_reports import compute_progress_summary, _generate_synthetic_report_data

        records = _generate_synthetic_report_data(days=7)
        summary = compute_progress_summary(records)

        assert "total_exercises" in summary
        assert "trend" in summary
        assert summary["trend"] in ("improving", "declining", "stable", "no_data")
        assert "active_students" in summary
        assert summary["active_students"] > 0

    def test_top_improved_sorted_by_improvement(self):
        """Top improved list is sorted descending by improvement amount."""
        from generate_reports import compute_top_improved, _generate_synthetic_report_data

        records = _generate_synthetic_report_data(days=14)
        top = compute_top_improved(records, top_n=5)

        if len(top) > 1:
            improvements = [t["improvement"] for t in top]
            assert improvements == sorted(improvements, reverse=True), \
                "Top improved should be sorted descending"

    def test_needs_attention_has_recommendations(self):
        """At-risk students have recommendation strings."""
        from generate_reports import compute_needs_attention, _generate_synthetic_report_data

        records = _generate_synthetic_report_data(days=21)
        at_risk = compute_needs_attention(records, bottom_n=5)

        for r in at_risk:
            assert "nama" in r
            assert "recommendation" in r
            assert isinstance(r["recommendation"], str)
            assert len(r["recommendation"]) > 5

    def test_character_difficulty_ranking(self):
        """Character difficulty is sorted ascending (hardest first)."""
        from generate_reports import compute_character_difficulty, _generate_synthetic_report_data

        records = _generate_synthetic_report_data()
        rankings = compute_character_difficulty(records)

        if len(rankings) > 1:
            accs = [r["avg_accuracy"] for r in rankings]
            assert accs == sorted(accs), "Should be sorted ascending (hardest first)"

    def test_character_difficulty_fields(self):
        """Each character ranking has required fields."""
        from generate_reports import compute_character_difficulty, _generate_synthetic_report_data

        records = _generate_synthetic_report_data()
        rankings = compute_character_difficulty(records)

        for r in rankings:
            assert "character" in r
            assert "avg_accuracy" in r
            assert "difficulty_score" in r
            assert "attempts" in r

    def test_generate_teacher_recommendations(self):
        """Recommendations list contains actionable items in Bahasa Indonesia."""
        from generate_reports import generate_teacher_recommendations, \
            compute_progress_summary, compute_top_improved, \
            compute_needs_attention, compute_character_difficulty, \
            _generate_synthetic_report_data

        records = _generate_synthetic_report_data()
        summary = compute_progress_summary(records)
        top = compute_top_improved(records)
        risk = compute_needs_attention(records)
        chars = compute_character_difficulty(records)

        recs = generate_teacher_recommendations(summary, top, risk, chars)

        assert isinstance(recs, list)
        assert len(recs) > 0
        for r in recs:
            assert "text" in r
            assert isinstance(r["text"], str)

            assert len(r["text"]) > 10

    def test_generate_headline(self):
        """Headline generator returns non-empty string based on trend."""
        from generate_reports import _generate_headline

        for trend in ["improving", "declining", "stable", "no_data"]:
            headline = _generate_headline({"trend": trend, "total_exercises": 50})
            assert isinstance(headline, str)
            assert len(headline) > 3

    def test_generate_weekly_report_structure(self):
        """Full weekly report has all required top-level sections."""
        from generate_reports import generate_weekly_report

        report = generate_weekly_report(period_days=7)

        assert report["report_type"] == "weekly"
        assert "executive_summary" in report
        assert "top_improved" in report
        assert "needs_attention" in report
        assert "character_difficulty" in report
        assert "recommendations" in report
        assert "metadata" in report
        assert report["metadata"]["total_records_analyzed"] > 0

    def test_weekly_report_saves_json(self):
        """Weekly report saves JSON file to reports directory."""
        from generate_reports import generate_weekly_report, REPORTS_DIR

        report = generate_weekly_report(period_days=7)

        json_files = list(REPORTS_DIR.glob("weekly_*.json"))
        assert len(json_files) > 0, "Should have created at least one weekly JSON"


        with open(json_files[-1], "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["report_type"] == "weekly"

    def test_weekly_report_saves_html(self):
        """Weekly report also generates HTML file."""
        from generate_reports import generate_weekly_report, REPORTS_DIR

        report = generate_weekly_report(period_days=7)

        html_files = list(REPORTS_DIR.glob("weekly_*.html"))
        assert len(html_files) > 0, "Should have created HTML report"

        html_content = html_files[-1].read_text(encoding="utf-8")
        assert "<html" in html_content.lower() or "<!doctype" in html_content.lower()

    def test_html_report_contains_sections(self):
        """HTML report contains key sections."""
        from generate_reports import generate_weekly_report, REPORTS_DIR, _render_html_report

        report = generate_weekly_report(period_days=7)
        html = _render_html_report(report)

        assert "Laporan" in html or "Sahabat Aksara" in html
        assert "<table" in html.lower()






class TestPSD5Endpoints:
    """PSD-5.2 & 5.4: Pipeline and Data Quality API endpoints."""

    @classmethod
    def setup_class(cls):
        """Start FastAPI TestClient."""
        sys.path.insert(0, str(PROJECT_ROOT / "backend"))
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        

        scripts_dir = str(PROJECT_ROOT / "data_science" / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_pipeline_status_endpoint(self):
        """GET /api/psd/status returns pipeline status."""
        resp = self.client.get("/api/psd/status")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["pipeline_version"] == "psd-5.2"
        assert data["status"] == "ready"
        assert "data_inventory" in data
        assert "endpoints_available" in data
        assert len(data["endpoints_available"]) >= 4

    def test_pipeline_status_has_inventory(self):
        """Pipeline status includes file counts."""
        resp = self.client.get("/api/psd/status")
        data = resp.json()
        
        inv = data["data_inventory"]
        assert "total_images_in_dataset" in inv
        assert "export_files" in inv
        assert "report_files" in inv
        assert isinstance(inv["export_file_names"], list)

    def test_data_quality_endpoint(self):
        """GET /api/psd/data-quality returns quality metrics."""
        resp = self.client.get("/api/psd/data-quality")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["quality_version"] == "psd-5.4"
        assert "dataset_overview" in data
        assert "class_distribution" in data
        assert "data_integrity" in data
        assert "export_split" in data

    def test_data_quality_has_health_score(self):
        """Data quality includes health score (0-100)."""
        resp = self.client.get("/api/psd/data-quality")
        data = resp.json()
        
        health = data["data_integrity"]["health_score"]
        assert 0 <= health <= 100, f"Health score out of range: {health}"

    def test_data_quality_has_imbalance_check(self):
        """Data quality checks class imbalance."""
        resp = self.client.get("/api/psd/data-quality")
        data = resp.json()
        
        cd = data["class_distribution"]
        assert "imbalance_ratio" in cd
        assert "is_imbalanced" in cd
        assert "recommendation" in cd
        assert isinstance(cd["is_imbalanced"], bool)

    def test_data_quality_export_split(self):
        """Data quality checks export split files exist."""
        resp = self.client.get("/api/psd/data-quality")
        data = resp.json()
        
        split = data["export_split"]
        assert "train_exists" in split
        assert "test_exists" in split
        assert isinstance(split["train_exists"], bool)

    def test_report_endpoint(self):
        """GET /api/psd/report returns latest report."""
        resp = self.client.get("/api/psd/report")
        assert resp.status_code == 200
        
        data = resp.json()

        assert "report_type" in data or "status" in data

    def test_report_endpoint_has_metadata(self):
        """Report endpoint returns metadata when available."""
        resp = self.client.get("/api/psd/report")
        data = resp.json()
        
        if "metadata" in data:
            meta = data["metadata"]
            assert "total_records_analyzed" in meta
            assert "unique_students" in meta

    def test_run_pipeline_endpoint(self):
        """POST /api/psd/run-pipeline triggers pipeline steps."""
        resp = self.client.post("/api/psd/run-pipeline", json={})
        assert resp.status_code == 200
        
        data = resp.json()
        assert "steps" in data
        assert "started_at" in data
        assert "completed_at" in data
        assert "total_steps" in data
        assert "successful_steps" in data
        assert len(data["steps"]) >= 3

    def test_run_pipeline_steps_have_status(self):
        """Each pipeline step has status field."""
        resp = self.client.post("/api/psd/run-pipeline", json={})
        data = resp.json()
        
        for step in data["steps"]:
            assert "step" in step
            assert "status" in step
            assert step["status"] in ("ok", "error", "running")






class TestPSD5Integration:
    """End-to-end integration tests across PSD-5 components."""

    def test_export_then_report_flow(self):
        """Export pipeline produces data that report generator can use."""
        from export_for_training import run_export_pipeline
        from generate_reports import generate_weekly_report
        

        export_result = run_export_pipeline(use_synthetic=True)
        assert export_result["status"] == "success"
        

        report = generate_weekly_report(period_days=7)
        assert report["metadata"]["total_records_analyzed"] > 0

    def test_pipeline_api_creates_artifacts(self):
        """Running pipeline via API creates artifacts on disk."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        resp = client.post("/api/psd/run-pipeline", json={})
        assert resp.status_code == 200
        

        reports_dir = PROJECT_ROOT / "data_science" / "reports"
        assert (reports_dir / "latest_report.json").exists() or \
               len(list(reports_dir.glob("weekly_*.json"))) > 0

    def test_status_reflects_latest_run(self):
        """After running pipeline, status shows updated inventory."""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        

        client.post("/api/psd/run-pipeline", json={})
        

        resp = client.get("/api/psd/status")
        data = resp.json()
        
        assert data["status"] == "ready"
        assert data["latest_report"] is not None or data["data_inventory"]["report_files"] > 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
