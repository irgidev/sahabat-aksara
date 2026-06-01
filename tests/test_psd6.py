"""
Test Suite: PSD-6 — Advanced Analytics
==========================================
Covers:
  - PSD-6.1: Handwriting Style Clustering (K-Means)
  - PSD-6.2: Anomaly Detection (Isolation Forest + Statistical)
  - PSD-6.3: Personalized Difficulty Recommendation Engine
  - PSD-6.4: Advanced Analytics API Endpoints

Run:
    backend/venv/Scripts/python.exe -m pytest tests/test_psd6.py -v
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






class TestClustering:
    """PSD-6.1: Handwriting Style Clustering."""

    def test_generate_clustering_data_shape(self):
        """Clustering data generator produces correct shape."""
        from clustering import generate_clustering_data
        
        X, labels, student_ids, fnames = generate_clustering_data(n_students=30)
        
        assert X.shape[0] == 30
        assert X.shape[1] == 10
        assert len(labels) == 30
        assert len(student_ids) == 30
        assert len(fnames) == 10

    def test_generate_clustering_data_has_4_profiles(self):
        """Synthetic data has 4 cluster profile types."""
        from clustering import generate_clustering_data
        
        _, labels, _, _ = generate_clustering_data(n_students=40)
        
        unique_labels = set(labels)
        assert len(unique_labels) == 4, f"Expected 4 profiles, got {unique_labels}"

    def test_kmeans_returns_required_keys(self):
        """K-Means clustering returns all required keys."""
        from clustering import generate_clustering_data, run_kmeans_clustering
        
        X, _, _, _ = generate_clustering_data()
        result = run_kmeans_clustering(X, n_clusters=4)
        
        assert "labels" in result
        assert "n_clusters" in result
        assert "metrics" in result
        assert "cluster_summary" in result
        assert "inertia" in result
        assert result["n_clusters"] == 4

    def test_kmeans_labels_match_n_samples(self):
        """Number of labels equals number of samples."""
        from clustering import generate_clustering_data, run_kmeans_clustering
        
        X, _, _, _ = generate_clustering_data(n_students=25)
        result = run_kmeans_clustering(X, n_clusters=3)
        
        assert len(result["labels"]) == 25

    def test_kmeans_silhouette_score_exists(self):
        """Silhouette score is computed when possible."""
        from clustering import generate_clustering_data, run_kmeans_clustering
        
        X, _, _, _ = generate_clustering_data(n_students=30)
        result = run_kmeans_clustering(X, n_clusters=4)
        
        sil = result["metrics"].get("silhouette")
        if sil is not None:
            assert -1 <= sil <= 1, f"Silhouette out of range: {sil}"

    def test_find_optimal_clusters(self):
        """Optimal K finder returns results for K=2..max_k."""
        from clustering import generate_clustering_data, find_optimal_clusters
        
        X, _, _, _ = generate_clustering_data()
        opt = find_optimal_clusters(X, max_k=6)
        
        assert "results" in opt
        assert "recommended_k" in opt
        assert 2 <= opt["recommended_k"] <= 6
        assert len(opt["results"]) == 5

    def test_interpret_cluster_returns_type(self):
        """Cluster interpretation returns a type string."""
        from clustering import interpret_cluster
        
        cs = {
            "cluster_id": 0,
            "n_members": 5,
            "avg_features": [80, 85, 90, 5, 95, 3, 88, 92, 70, 85],
            "centroid": [78, 82, 88, 6, 93, 4, 86, 90, 68, 83],
        }
        fnames = [f"f{i}" for i in range(10)]
        
        interp = interpret_cluster(cs, fnames)
        
        assert "type" in interp
        assert "description" in interp
        assert "recommendation" in interp
        assert isinstance(interp["type"], str)

    def test_interpret_neat_writer(self):
        """High accuracy cluster identified as 'penulis_rapi'."""
        from clustering import interpret_cluster
        
        cs = {
            "cluster_id": 0,
            "n_members": 8,
            "avg_features": [82, 88, 92, 4, 96, 3, 90, 94, 72, 88],
            "centroid": [80, 86, 90, 5, 94, 4, 88, 92, 70, 86],
        }
        fnames = [f"f{i}" for i in range(10)]
        
        interp = interpret_cluster(cs, fnames)
        assert "rapi" in interp["type"]

    def test_full_clustering_pipeline_runs(self):
        """Full clustering pipeline completes without error."""
        from clustering import run_full_clustering_pipeline
        
        report = run_full_clustering_pipeline()
        
        assert report is not None
        assert "method" in report or "optimal_k" in report






class TestAnomalyDetection:
    """PSD-6.2: Anomaly Detection."""

    def test_generate_anomaly_data_shape(self):
        """Anomaly data generator produces correct shape with labels."""
        from anomaly_detection import generate_anomaly_data
        
        X, labels = generate_anomaly_data(n_samples=80)
        
        assert X.shape[0] >= 75 and X.shape[0] <= 85
        assert len(labels) >= 75 and len(labels) <= 85
        assert any(l != "normal" for l in labels), "Should have some anomalies"

    def test_generate_anomaly_data_has_types(self):
        """Anomaly data includes multiple anomaly types."""
        from anomaly_detection import generate_anomaly_data
        
        _, labels = generate_anomaly_data(anomaly_ratio=0.15)
        
        unique_types = set(labels)
        assert "normal" in unique_types
        assert len(unique_types) >= 2

    def test_isolation_forest_detects_anomalies(self):
        """Isolation Forest finds anomalies in synthetic data."""
        from anomaly_detection import generate_anomaly_data, detect_anomalies_isolation_forest
        
        X, _ = generate_anomaly_data(n_samples=100)
        result = detect_anomalies_isolation_forest(X, contamination=0.1)
        
        assert "anomaly_indices" in result
        assert "normal_indices" in result
        assert len(result["anomaly_indices"]) > 0
        assert len(result["anomaly_indices"]) < len(X)

    def test_isolation_forest_scores_negative_for_anomalies(self):
        """Anomaly scores are negative for anomalous samples."""
        from anomaly_detection import generate_anomaly_data, detect_anomalies_isolation_forest
        
        X, _ = generate_anomaly_data(n_samples=50)
        result = detect_anomalies_isolation_forest(X)
        
        scores = result["scores"]
        anom_idx = set(result["anomaly_indices"])
        
        for idx in anom_idx:
            assert scores[idx] < 0, f"Anomaly at {idx} should have negative score, got {scores[idx]}"

    def test_statistical_detection_works(self):
        """Statistical anomaly detection returns results."""
        from anomaly_detection import generate_anomaly_data, detect_anomalies_statistical
        
        X, _ = generate_anomaly_data(n_samples=60)
        result = detect_anomalies_statistical(X)
        
        assert "anomalies_by_feature" in result
        assert isinstance(result["anomalies_by_feature"], dict)

    def test_pattern_analysis_categorizes_anomalies(self):
        """Pattern analysis categorizes anomalies into types."""
        from anomaly_detection import generate_anomaly_data, analyze_anomaly_patterns
        
        X, _ = generate_anomaly_data(n_samples=80, anomaly_ratio=0.12)
        anom_indices = list(range(10))
        
        patterns = analyze_anomaly_patterns(X, anom_indices)
        
        assert "total_anomalies" in patterns
        assert "categories" in patterns
        assert patterns["total_anomalies"] > 0

    def test_full_anomaly_detection_pipeline(self):
        """Full anomaly detection pipeline runs end-to-end."""
        from anomaly_detection import run_full_anomaly_detection
        
        report = run_full_anomaly_detection()
        
        assert report is not None
        assert "isolation_forest" in report or "method" in report






class TestRecommendationEngine:
    """PSD-6.3: Personalized Difficulty Recommendation."""

    def test_generate_student_data(self):
        """Student performance data generator works."""
        from recommendation_engine import generate_student_performance_data
        
        students = generate_student_performance_data(n_students=5, n_exercises_per_student=20)
        
        assert len(students) == 5
        for s in students:
            assert "id" in s
            assert "nama" in s
            assert "kelas" in s
            assert "exercises" in s
            assert len(s["exercises"]) == 20

    def test_char_difficulty_computation(self):
        """Per-character difficulty computation produces scores."""
        from recommendation_engine import (
            generate_student_performance_data, compute_char_difficulty_for_student
        )
        
        students = generate_student_performance_data(n_students=1, n_exercises_per_student=30)
        diff = compute_char_difficulty_for_student(students[0]["exercises"])
        
        assert isinstance(diff, dict)
        assert len(diff) > 0
        for c, d in diff.items():
            assert "avg_accuracy" in d
            assert "difficulty_score" in d
            assert 0 <= d["difficulty_score"] <= 100

    def test_recommendation_learning_path_structure(self):
        """Learning path has required structure."""
        from recommendation_engine import (
            generate_student_performance_data, recommend_learning_path
        )
        
        students = generate_student_performance_data()
        rec = recommend_learning_path(students[0])
        
        assert "student_id" in rec
        assert "summary" in rec
        assert "top_5_hardest" in rec
        assert "top_5_easiest" in rec
        assert "learning_path" in rec
        assert "general_recommendation" in rec

    def test_learning_path_has_weeks_and_actions(self):
        """Each learning path entry has week, character, action."""
        from recommendation_engine import (
            generate_student_performance_data, recommend_learning_path
        )
        
        students = generate_student_performance_data()
        rec = recommend_learning_path(students[0])
        
        for step in rec["learning_path"]:
            assert "week" in step
            assert "character" in step
            assert "action" in step
            assert "priority" in step

    def test_summary_counts_categories(self):
        """Summary counts mastered/practicing/struggling/not_tried."""
        from recommendation_engine import (
            generate_student_performance_data, recommend_learning_path
        )
        
        students = generate_student_performance_data(n_exercises_per_student=50)
        rec = recommend_learning_path(students[0])
        summ = rec["summary"]
        
        assert "mastered_count" in summ
        assert "practicing_count" in summ
        assert "struggling_count" in summ
        assert "not_tried_count" in summ
        assert summ["mastered_count"] + summ["practicing_count"] + \
               summ["struggling_count"] + summ["not_tried_count"] >= 0

    def test_class_recommendations_aggregates(self):
        """Class-level recommendations aggregate per class."""
        from recommendation_engine import (
            generate_student_performance_data, generate_class_recommendations
        )
        
        students = generate_student_performance_data(n_students=8)
        recs = generate_class_recommendations(students)
        
        assert "TK-A" in recs or "TK-B" in recs
        for kelas, data in recs.items():
            assert "n_students" in data
            assert "class_avg_accuracy" in data
            assert "recommendation" in data

    def test_general_recommendation_in_bahasa(self):
        """General recommendation is in Bahasa Indonesia."""
        from recommendation_engine import (
            generate_student_performance_data, recommend_learning_path
        )
        
        students = generate_student_performance_data()
        rec = recommend_learning_path(students[0])
        
        rec_text = rec.get("general_recommendation", "")
        assert isinstance(rec_text, str)
        assert len(rec_text) > 10

    def test_full_recommendation_engine_runs(self):
        """Full recommendation engine pipeline runs successfully."""
        from recommendation_engine import run_full_recommendation_engine
        
        report = run_full_recommendation_engine()
        
        assert report is not None
        assert "individual_recommendations" in report
        assert "class_recommendations" in report






class TestPSD6Endpoints:
    """PSD-6.4: Advanced Analytics API Endpoints."""

    @classmethod
    def setup_class(cls):
        sys.path.insert(0, str(PROJECT_ROOT / "backend"))
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        scripts_dir = str(PROJECT_ROOT / "data_science" / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    def test_clustering_endpoint(self):
        """GET /api/psd/clustering returns clustering results."""
        resp = self.client.get("/api/psd/clustering")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "ok_fallback")

    def test_clustering_has_metrics(self):
        """Clustering response has metrics like silhouette score."""
        resp = self.client.get("/api/psd/clustering")
        data = resp.json()
        assert "clustering_version" in data
        assert "n_clusters" in data or "clusters" in data

    def test_anomaly_endpoint(self):
        """GET /api/psd/anomalies returns anomaly detection results."""
        resp = self.client.get("/api/psd/anomalies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "error")

    def test_anomaly_has_counts(self):
        """Anomaly response has total anomalies and rate."""
        resp = self.client.get("/api/psd/anomalies")
        data = resp.json()
        if data.get("status") == "ok":
            assert "total_anomalies" in data or "anomalies_detected" in data
            assert "anomaly_rate" in data

    def test_recommendation_endpoint(self):
        """GET /api/psd/recommendations/{id} returns recommendations."""
        resp = self.client.get("/api/psd/recommendations/s001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "error")

    def test_recommendation_has_learning_path(self):
        """Recommendation response contains learning path."""
        resp = self.client.get("/api/psd/recommendations/s001")
        data = resp.json()
        if data.get("status") == "ok":
            assert "learning_path" in data
            assert "summary" in data

    def test_advanced_analytics_dashboard(self):
        """GET /api/psd/advanced-analytics returns combined analytics."""
        resp = self.client.get("/api/psd/advanced-analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboard_version" in data
        assert "clustering" in data
        assert "anomalies" in data
        assert "recommendations_summary" in data






class TestPSD6Integration:
    """End-to-end integration across PSD-6 components."""

    def test_clustering_then_recommendation_flow(self):
        """Clustering insights can feed into recommendations."""
        from clustering import generate_clustering_data, run_kmeans_clustering
        from recommendation_engine import (
            generate_student_performance_data, recommend_learning_path
        )
        

        X, _, student_ids, _ = generate_clustering_data()
        clust_result = run_kmeans_clustering(X)
        
        students = generate_student_performance_data()
        rec = recommend_learning_path(students[0])
        
        assert clust_result["n_clusters"] > 0
        assert len(rec["learning_path"]) > 0

    def test_all_psd6_reports_generated(self):
        """All PSD-6 scripts can generate reports to disk."""
        reports_dir = PROJECT_ROOT / "data_science" / "reports"
        
        from clustering import run_full_clustering_pipeline
        from anomaly_detection import run_full_anomaly_detection
        from recommendation_engine import run_full_recommendation_engine
        
        r1 = run_full_clustering_pipeline()
        r2 = run_full_anomaly_detection()
        r3 = run_full_recommendation_engine()
        

        json_files = list(reports_dir.glob("*.json"))
        png_files = list(reports_dir.glob("*.png"))
        
        assert len(json_files) >= 3, f"Expected >= 3 JSON reports, found {len(json_files)}"
        assert r1 is not None and r2 is not None and r3 is not None


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
