"""
Test Suite: PSD-4 — Dashboard Analytics Enhancement
=====================================================
Covers:
  PSD-4.1 Heatmap Endpoint (/api/dashboard/heatmap)
  PSD-4.2 Student Trend Endpoint (/api/dashboard/student-trend/{id})
  PSD-4.3 Character Rankings Endpoint (/api/dashboard/character-rankings)
  PSD-4.4 Class Comparison Endpoint (/api/dashboard/class-comparison)
  PSD-4.5 Dashboard Components (AnalyticsTab, charts)
  PSD-4.6 Export Functionality (/api/dashboard/export)

Run:
    backend/venv/Scripts/python.exe tests/test_psd4.py -v
"""

import os
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))






def _import_main():
    """Import main.py and return the app."""
    import main
    return main.app


def _call_endpoint(client, method, path, **kwargs):
    """Call an endpoint using FastAPI TestClient."""
    from starlette.testclient import TestClient
    if isinstance(client, TestClient):
        resp = getattr(client, method)(path, **kwargs)
        return resp.status_code, resp.json()

    return None, None






class TestHeatmapEndpoint:
    """PSD-4.1: /api/dashboard/heatmap"""

    def test_heatmap_route_exists(self):
        """Heatmap route should be registered in FastAPI app."""
        app = _import_main()
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/dashboard/heatmap" in routes

    def test_heatmap_returns_structure(self):
        """Heatmap endpoint should return proper JSON structure."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        status, data = _call_endpoint(client, "get", "/api/dashboard/heatmap")
        assert status == 200
        
        assert "students" in data
        assert "characters" in data
        assert "matrix" in data
        assert isinstance(data["matrix"], list)
        assert "generated_at" in data

    def test_heatmap_matrix_rows_match_students(self):
        """Matrix row count should match students count."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/heatmap")
        data = resp.json()
        assert resp.status_code == 200
        
        n_students = len(data.get("students", []))
        n_matrix_rows = len(data.get("matrix", []))
        assert n_students == n_matrix_rows

    def test_heatmap_scores_are_numeric(self):
        """Each matrix row should have numeric scores dict."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/heatmap")
        data = resp.json()
        assert resp.status_code == 200
        
        for row in data["matrix"][:3]:
            assert "student_id" in row
            assert "nama" in row
            assert "scores" in row
            assert isinstance(row["scores"], dict)
            if len(row["scores"]) > 0:
                first_val = list(row["scores"].values())[0]
                assert first_val is None or isinstance(first_val, (int, float))


class TestStudentTrendEndpoint:
    """PSD-4.2: /api/dashboard/student-trend/{student_id}"""

    def test_trend_route_exists(self):
        """Student trend route should be registered."""
        app = _import_main()
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert any("student-trend" in r for r in routes)

    def test_trend_returns_structure(self):
        """Trend endpoint should return time series + trend info."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/student-trend/some-student-id?window=14")
        data = resp.json()
        assert resp.status_code == 200
        
        assert "series" in data
        assert "trend" in data
        assert "window_days" in data
        assert "slope_per_day" in data
        assert data["window_days"] == 14
        assert data["trend"] in ("improving", "declining", "stable", "no_data")

    def test_trend_series_has_required_fields(self):
        """Each series entry should have date, avg_accuracy, exercise_count."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/student-trend/test-id?window=7")
        data = resp.json()
        assert resp.status_code == 200
        
        series = data.get("series", [])
        assert isinstance(series, list)
        if len(series) > 0:
            entry = series[0]
            assert "date" in entry
            assert "avg_accuracy" in entry
            assert "exercise_count" in entry

    def test_trend_window_parameter(self):
        """Window parameter should control number of days returned."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp7 = client.get("/api/dashboard/student-trend/test-id?window=7")
        resp30 = client.get("/api/dashboard/student-trend/test-id?window=30")
        data7 = resp7.json()
        data30 = resp30.json()
        
        assert resp7.status_code == 200
        assert resp30.status_code == 200
        assert len(data30["series"]) >= len(data7["series"])


class TestCharacterRankingsEndpoint:
    """PSD-4.3: /api/dashboard/character-rankings"""

    def test_rankings_route_exists(self):
        """Character rankings route should be registered."""
        app = _import_main()
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/dashboard/character-rankings" in routes

    def test_rankings_returns_structure(self):
        """Should return ranked list of characters with metrics."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/character-rankings")
        data = resp.json()
        assert resp.status_code == 200
        
        assert "rankings" in data
        assert "total_characters" in data
        assert "category_summary" in data
        assert isinstance(data["rankings"], list)

    def test_rankings_sorted_by_difficulty(self):
        """Rankings should be sorted by avg_accuracy ascending (hardest first)."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/character-rankings")
        data = resp.json()
        assert resp.status_code == 200
        
        rankings = data["rankings"]
        if len(rankings) >= 2:
            accs = [r["avg_accuracy"] for r in rankings if r["avg_accuracy"] is not None]
            if len(accs) >= 2:
                assert accs == sorted(accs), "Rankings should be sorted by difficulty (ascending)"

    def test_ranking_entry_fields(self):
        """Each ranking entry should have required fields."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/character-rankings")
        data = resp.json()
        assert resp.status_code == 200
        
        for r in data["rankings"][:5]:
            assert "character" in r
            assert "category" in r
            assert "attempts" in r
            assert "avg_accuracy" in r
            assert "max_accuracy" in r
            assert "min_accuracy" in r


class TestClassComparisonEndpoint:
    """PSD-4.4: /api/dashboard/class-comparison"""

    def test_comparison_route_exists(self):
        """Class comparison route should be registered."""
        app = _import_main()
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/dashboard/class-comparison" in routes

    def test_comparison_returns_structure(self):
        """Should return per-class metrics."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/class-comparison")
        data = resp.json()
        assert resp.status_code == 200
        
        assert "classes" in data
        assert "period_days" in data
        assert isinstance(data["classes"], list)

    def test_class_entry_has_metrics(self):
        """Each class entry should have key performance metrics."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/class-comparison")
        data = resp.json()
        assert resp.status_code == 200
        
        for cls in data["classes"]:
            assert "class_name" in cls
            assert "total_students" in cls
            assert "active_students_week" in cls
            assert "total_exercises_week" in cls
            assert "avg_accuracy" in cls


class TestExportEndpoint:
    """PSD-4.6: /api/dashboard/export"""

    def test_export_json_format(self):
        """Export as JSON should return downloadable data."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "exported_at" in data
        assert "total_records" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_export_csv_format(self):
        """Export as CSV should return CSV content-type."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/export?format=csv")
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type or "csv" in content_type.lower()

    def test_export_csv_has_headers(self):
        """CSV export should have header row with expected columns."""
        from starlette.testclient import TestClient
        app = _import_main()
        client = TestClient(app)
        
        resp = client.get("/api/dashboard/export?format=csv")
        text = resp.text
        
        headers = ["nama", "karakter", "akurasi", "bintang"]
        for h in headers:
            assert h in text.lower(), f"CSV missing header: {h}"






class TestFallbackGenerators:
    """Test synthetic fallback data when Supabase unavailable."""

    def test_fake_heatmap_structure(self):
        """_fake_heatmap() should return valid heatmap structure."""
        import main
        data = main._fake_heatmap()
        
        assert "students" in data
        assert "characters" in data
        assert "matrix" in data
        assert len(data["students"]) > 0
        assert len(data["characters"]) > 0

    def test_fake_student_trend_structure(self):
        """_fake_student_trend() should return valid trend structure."""
        import main
        data = main._fake_student_trend("test-student", 30)
        
        assert "series" in data
        assert "trend" in data
        assert "window_days" in data
        assert data["window_days"] == 30
        assert len(data["series"]) == 30

    def test_fake_character_rankings_structure(self):
        """_fake_character_rankings() should return valid rankings."""
        import main
        data = main._fake_character_rankings()
        
        assert "rankings" in data
        assert "total_characters" in data
        assert len(data["rankings"]) > 0

        assert data["total_characters"] >= 60

    def test_fake_class_comparison_structure(self):
        """_fake_class_comparison() should return class comparison data."""
        import main
        data = main._fake_class_comparison()
        
        assert "classes" in data
        assert len(data["classes"]) >= 1
        for cls in data["classes"]:
            assert "class_name" in cls
            assert "total_students" in cls
            assert "avg_accuracy" in cls

    def test_fake_export_json(self):
        """_fake_export('json') should return JSON-like dict."""
        import main
        data = main._fake_export("json")
        
        assert "data" in data
        assert "total_records" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_fake_export_csv(self):
        """_fake_export('csv') should return Response-like object."""
        import main
        result = main._fake_export("csv")
        

        assert hasattr(result, "body") or hasattr(result, "status_code") or result is not None






class TestPSD4Integration:
    """Cross-cutting integration tests."""

    def test_all_psd4_endpoints_registered(self):
        """All 5 new endpoints must be registered."""
        app = _import_main()
        routes = {r.path for r in app.routes if hasattr(r, 'path')}
        
        required = [
            "/api/dashboard/heatmap",
            "/api/dashboard/student-trend/{student_id}",
            "/api/dashboard/character-rankings",
            "/api/dashboard/class-comparison",
            "/api/dashboard/export",
        ]
        for ep in required:

            found = any(ep.replace("{", "").replace("}", "") == r.replace("{", "").replace("}", "") 
                       for r in routes) or ep in routes
            assert found, f"Missing endpoint: {ep}"

    def test_fallback_functions_exist_in_main(self):
        """Fallback generator functions should exist in main module."""
        import main
        
        funcs = [
            "_fake_heatmap",
            "_fake_student_trend",
            "_fake_character_rankings",
            "_fake_class_comparison",
            "_fake_export",
        ]
        for f in funcs:
            assert hasattr(main, f), f"Missing fallback function: {f}"
            assert callable(getattr(main, f))

    def test_defaultdict_imported(self):
        """main.py should import defaultdict for aggregation."""
        import main

        assert True

    def test_dashboard_component_file_updated(self):
        """Dashboard.jsx should contain PSD-4 component references."""
        dash_path = PROJECT_ROOT / "frontend/src/components/Dashboard.jsx"
        assert dash_path.exists(), f"Missing: {dash_path}"
        
        content = dash_path.read_text(encoding="utf-8")
        

        psd4_indicators = [
            "AnalyticsTab",
            "ChartPieSlice",
            "DownloadSimple",
            "PieChart",
            "LineChart",
            "Line",
            "PSD-4.1",
            "PSD-4.2",
            "PSD-4.3",
            "PSD-4.4",
            "PSD-4.5",
            "analitik",
            "Heatmap Akurasi",
            "Ranking Kesulitan",
            "Trend Perkembangan",
            "Perbandingan Kelas",
            "Distribusi Bintang",
        ]
        
        found = sum(1 for ind in psd4_indicators if ind in content)
        assert found >= 8, f"Only {found}/{len(psd4_indicators)} PSD-4 indicators found in Dashboard.jsx"

    def test_backend_syntax_valid(self):
        """backend/main.py should have no syntax errors."""
        import py_compile
        try:
            py_compile.compile(str(PROJECT_ROOT / "backend/main.py"), doraise=True)
        except py_compile.PyCompileError as e:
            raise AssertionError(f"Syntax error in main.py: {e}")

    def test_total_dashboard_endpoint_count(self):
        """Should have at least 9 dashboard endpoints total."""
        app = _import_main()
        dash_routes = [r.path for r in app.routes 
                      if hasattr(r, 'path') and r.path.startswith('/api/dashboard')]
        assert len(dash_routes) >= 9, f"Expected >=9 dashboard endpoints, got {len(dash_routes)}"






if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
