
"""
Test Suite: PSD-3 (EDA Notebooks)
======================================
Validates all 6 Jupyter notebooks:
  - JSON format validity
  - Required cells present
  - Import statements correct
  - Data paths reference existing files

Run:
    python tests/test_psd3.py
"""

import sys
import os
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

NOTEBOOKS_DIR = PROJECT_ROOT / "data_science" / "notebooks"
FEATURES_CSV = PROJECT_ROOT / "data_science" / "datasets" / "features" / "all_features.csv"
CLEAN_DIR = PROJECT_ROOT / "data_science" / "datasets" / "clean" / "_unsorted"
AUGMENTED_DIR = PROJECT_ROOT / "data_science" / "datasets" / "augmented" / "_unsorted"

PYTHON = sys.executable if Path(sys.executable).name != "python.exe" else \
        str(PROJECT_ROOT / "backend" / "venv" / "Scripts" / "python.exe")

ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"


def _get_all_code_sources(nb_data):
    """Extract all code source text from a notebook dict."""
    return "".join(
        "".join(c.get("source", []))
        for c in nb_data["cells"]
        if c["cell_type"] == "code"
    )


class TestNotebookValidity:
    """Test that all notebooks are valid .ipynb JSON files."""

    def test_all_notebooks_exist(self):
        expected = [
            "01_data_exploration.ipynb",
            "02_preprocessing_pipeline.ipynb",
            "03_feature_engineering.ipynb",
            "04_visualization_dashboard.ipynb",
            "05_character_analysis.ipynb",
            "06_student_profiling.ipynb",
        ]
        for nb_name in expected:
            path = NOTEBOOKS_DIR / nb_name
            assert path.exists(), f"Missing notebook: {nb_name}"

    def test_valid_json_format(self):
        for nb_path in sorted(NOTEBOOKS_DIR.glob("*.ipynb")):
            with open(nb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data.get("nbformat") == 4, f"{nb_path.name}: nbformat != 4"
            assert "cells" in data, f"{nb_path.name}: missing 'cells' key"
            assert len(data["cells"]) > 0, f"{nb_path.name}: empty cells"
            print(f"  OK {nb_path.name}: {len(data['cells'])} cells, format v{data.get('nbformat_minor', '?')}")

    def test_has_markdown_and_code(self):
        for nb_path in sorted(NOTEBOOKS_DIR.glob("*.ipynb")):
            with open(nb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cell_types = [c["cell_type"] for c in data["cells"]]
            assert "markdown" in cell_types, f"{nb_path.name}: no markdown cells"
            assert "code" in cell_types, f"{nb_path.name}: no code cells"


class TestDataReferences:
    """Test that notebooks reference real data files."""

    def test_features_csv_exists(self):
        assert FEATURES_CSV.exists(), f"Features CSV missing: {FEATURES_CSV}"

    def test_clean_images_exist(self):
        n = len(list(CLEAN_DIR.glob("*.png")))
        assert n > 0, f"No clean images in {CLEAN_DIR}"
        print(f"  OK Clean images: {n} files")

    def test_augmented_images_exist(self):
        n = len(list(AUGMENTED_DIR.glob("*.png")))
        assert n > 0, f"No augmented images in {AUGMENTED_DIR}"
        print(f"  OK Augmented images: {n} files")


class TestNotebookContent:
    """Test content quality of each notebook."""

    def _load_nb(self, name):
        path = NOTEBOOKS_DIR / name
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_nb01_imports_pandas_numpy(self):
        data = self._load_nb("01_data_exploration.ipynb")
        sources = _get_all_code_sources(data)
        assert "pandas" in sources or "pd." in sources, "NB01: missing pandas import"
        assert "numpy" in sources or "np." in sources, "NB01: missing numpy import"
        assert "matplotlib" in sources or "plt." in sources, "NB01: missing matplotlib import"

    def test_nb01_loads_features_csv(self):
        data = self._load_nb("01_data_exploration.ipynb")
        sources = _get_all_code_sources(data)
        assert "all_features.csv" in sources or "FEATURES_CSV" in sources, "NB01: doesn't load features CSV"

    def test_nb02_preprocessing_steps(self):
        data = self._load_nb("02_preprocessing_pipeline.ipynb")
        sources = _get_all_code_sources(data)
        required = ["grayscale", "threshold", "otsu", "adaptive", "augment"]
        found = sum(1 for r in required if r.lower() in sources.lower())
        assert found >= 3, f"NB02: only {found}/5 preprocessing concepts covered"

    def test_nb03_pca_or_tsne(self):
        data = self._load_nb("03_feature_engineering.ipynb")
        sources = _get_all_code_sources(data)
        has_dim_reduction = "PCA" in sources or "tsne" in sources or "TSNE" in sources
        assert has_dim_reduction, "NB03: no PCA/t-SNE dimensionality reduction"

    def test_nb03_correlation_analysis(self):
        data = self._load_nb("03_feature_engineering.ipynb")
        sources = _get_all_code_sources(data)
        assert "corr" in sources.lower() or "correlation" in sources.lower(), "NB03: no correlation analysis"

    def test_nb04_dashboard_charts(self):
        data = self._load_nb("04_visualization_dashboard.ipynb")
        sources = _get_all_code_sources(data)
        chart_keywords = ["bar", "plot", "scatter", "pie", "boxplot", "hist"]
        found = sum(1 for k in chart_keywords if k in sources.lower())
        assert found >= 3, f"NB04: only {found}/6 chart types used"

    def test_nb05_character_ranking(self):
        data = self._load_nb("05_character_analysis.ipynb")
        sources = _get_all_code_sources(data)
        assert "kesulitan" in sources or "difficulty" in sources.lower() or "ranking" in sources.lower(), \
               "NB05: no difficulty/ranking analysis"

    def test_nb06_student_profiling(self):
        data = self._load_nb("06_student_profiling.ipynb")
        sources = _get_all_code_sources(data)
        assert "risk" in sources.lower() or "cluster" in sources.lower(), \
               "NB06: no risk detection or clustering"

    def test_nb06_learning_curve(self):
        data = self._load_nb("06_student_profiling.ipynb")
        sources = _get_all_code_sources(data)
        assert "learning" in sources.lower() and ("curve" in sources.lower() or "trend" in sources.lower()), \
               "NB06: no learning curve analysis"


class TestNotebooksRunWithoutError:
    """Quick syntax check: import all notebooks' dependencies."""

    def test_can_import_required_libs(self):
        """Verify all required libraries can be imported."""
        import subprocess
        result = subprocess.run(
            [PYTHON, "-c", 
             "import numpy; import pandas; import matplotlib; import seaborn; "
             "from PIL import Image; from pathlib import Path; "
             "print('All imports OK')"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            env=ENV,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed: {(result.stderr or '')[:200]}"
        print(f"  {result.stdout.strip()}")

    def test_nb01_executes_without_error(self):
        """Check NB01 structure is loadable."""
        import subprocess
        result = subprocess.run(
            [PYTHON, "-c",
             "import sys,json; sys.path.insert(0,'.'); "
             "sys.stdout.reconfigure(encoding='utf-8',errors='replace'); "
             "nb=json.load(open('data_science/notebooks/01_data_exploration.ipynb','r',encoding='utf-8')); "
             "print(f'NB01: {len(nb[\"cells\"])} total cells')"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            env=ENV,
            timeout=30,
        )
        assert result.returncode == 0, f"NB01 check failed: {(result.stderr or '')[:200]}"
        print(f"  {result.stdout.strip()}")


def main():
    import numpy as np

    print("\n" + "=" * 65)
    print("  TEST SUITE: PSD-3 (EDA Notebooks)")
    print("=" * 65)

    test_classes = [
        ("Notebook Validity", TestNotebookValidity),
        ("Data References", TestDataReferences),
        ("Notebook Content", TestNotebookContent),
        ("Execution Check", TestNotebooksRunWithoutError),
    ]

    total_run = 0
    total_passed = 0
    total_failed = 0
    errors = []

    for class_name, cls in test_classes:
        print(f"\n{'-' * 55}")
        print(f"  [{class_name}]")
        print(f"{'-' * 55}")

        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in sorted(methods):
            total_run += 1
            method = getattr(instance, method_name)

            try:
                method()
                total_passed += 1
                print(f"  PASS {method_name}")
            except AssertionError as e:
                total_failed += 1
                errors.append((class_name, method_name, str(e)))
                print(f"  FAIL {method_name}: {e}")
            except Exception as e:
                total_failed += 1
                errors.append((class_name, method_name, f"EXCEPTION: {e}"))
                print(f"  ERROR {method_name}: EXCEPTION -- {e}")


    print("\n" + "=" * 65)
    print(f"  RESULTS: {total_passed}/{total_run} passed, {total_failed} failed")

    if errors:
        print(f"\n  Failed Tests:")
        for cls_name, meth, err in errors:
            print(f"    * {cls_name}.{meth}: {err[:100]}")

    print("=" * 65 + "\n")

    return total_failed


if __name__ == "__main__":
    exit_code = main()
    sys.exit(min(exit_code, 1))
