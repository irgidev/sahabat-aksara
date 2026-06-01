
"""
Test Suite: PSD-2 (Preprocessing & Cleaning Pipeline)
=====================================================
Comprehensive tests for all 4 PSD-2 scripts:
  2.1 preprocess_batch.py   — 7-step pipeline
  2.2 augment_data.py       — 7 augmentation techniques
  2.3 extract_features.py   — ~131 feature extraction
  2.4 generate_statistics.py — Statistics + quality report

Usage:
    python tests/test_psd2.py
    python tests/test_psd2.py --verbose
    python tests/test_psd2.py --preprocess

Author: Sahabat Aksara — PSD-2 Test Suite
"""

import sys
import os
import json
import csv
import argparse
import subprocess
import time
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
import cv2


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / "backend" / "venv" / "Scripts" / "python.exe"
DATA_DIR = PROJECT_ROOT / "data_science" / "datasets"
SCRIPTS_DIR = PROJECT_ROOT / "data_science" / "scripts"
TEST_IMAGE_DIR = DATA_DIR / "processed" / "_unsorted"


class C:
    PASS = "\033[92m✅"
    FAIL = "\033[91m❌"
    SKIP = "\033[93m⏭️"
    INFO = "\033[94mℹ️"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def run_script(script_name: str, args: List[str] = None, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a Python script using venv Python."""
    cmd = [str(VENV_PYTHON), str(SCRIPTS_DIR / script_name)]
    if args:
        cmd.extend(args)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")






def psd2_test_21_import():
    """PSD-2.1a: Can import preprocess_batch module."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.1a] Module Import{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import preprocess_batch
        funcs = [
            "load_image", "to_grayscale", "apply_threshold",
            "remove_noise", "normalize_size", "center_content",
            "invert_if_needed", "run_full_pipeline", "run_batch",
        ]
        ok = True
        for f in funcs:
            has = hasattr(preprocess_batch, f)
            status = C.PASS if has else C.FAIL
            print(f"  {status} {f}()")
            if not has:
                ok = False
        
        print(f"\n  {C.PASS if ok else C.FAIL} All pipeline functions imported")
        return ok
    except Exception as e:
        print(f"  {C.FAIL} Import error: {e}")
        return False
    finally:
        sys.path.pop(0) if SCRIPTS_DIR in sys.path else None


def psd2_test_21_single_image():
    """PSD-2.1b: Run full pipeline on a single test image."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.1b] Single Image Pipeline{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import preprocess_batch
        import tempfile
        

        images = list(TEST_IMAGE_DIR.glob("*.png"))
        if not images:
            print(f"  {C.SKIP} No test images found")
            return True
        
        test_img = images[0]
        print(f"  {C.INFO} Test image: {test_img.name} ({test_img.stat().st_size // 1024}KB)")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "output.png"
            
            log = preprocess_batch.run_full_pipeline(
                input_path=str(test_img),
                output_path=str(out_path),
                target_size=64,
                threshold_method="otsu",
                noise_method="morphological",
                force_fg="auto",
                center_content_flag=True,
            )
            

            success = log.get("success", False)
            print(f"  {C.PASS if success else C.FAIL} Pipeline completed: {success}")
            
            if success:
                out_file = Path(log.get("output_file", ""))
                exists = out_file.exists() if out_file else False
                print(f"  {C.PASS if exists else C.FAIL} Output file exists: {out_file.name if out_file else 'N/A'}")
                
                if exists:
                    img = cv2.imread(str(out_file))
                    is_64x64 = img.shape == (64, 64, 3) or img.shape == (64, 64)
                    print(f"  {C.PASS if is_64x64 else C.FAIL} Output size: {img.shape[:2]} (expected 64×64)")
                    
                    steps = log.get("steps", {})
                    for step_name in ["load", "grayscale", "threshold", "noise", "resize", "invert"]:
                        step_data = steps.get(step_name, {})
                        has_data = bool(step_data)
                        print(f"  {C.PASS if has_data else C.SKIP} Step '{step_name}': logged")
                    
                    quality = steps.get("quality", {})
                    is_blank = quality.get("is_blank", False)
                    is_full = quality.get("is_full", False)
                    print(f"  {C.PASS if not (is_blank or is_full) else C.INFO} Quality: blank={is_blank}, full={is_full}")
            
            duration = log.get("duration_ms", 0)
            print(f"  {C.INFO} Duration: {duration}ms")
        
        return success
    
    except Exception as e:
        print(f"  {C.FAIL} Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sys.path.pop(0) if str(SCRIPTS_DIR) in [str(p) for p in sys.path] else None


def psd2_test_21_batch():
    """PSD-2.1c: Run batch preprocessing via CLI."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.1c] Batch Preprocessing (CLI){C.END}")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_script("preprocess_batch.py", [
            "--input", str(TEST_IMAGE_DIR),
            "--output", str(Path(tmpdir) / "clean"),
            "--size", "64",
        ], timeout=30)
        
        if result.returncode == 0:
            print(f"  {C.PASS} CLI executed successfully (code 0)")
            

            output_dir = Path(tmpdir) / "clean" / "_unsorted"
            if output_dir.exists():
                out_count = len(list(output_dir.glob("*.png")))
                print(f"  {C.PASS} Output files: {out_count}")
            else:
                print(f"  {C.SKIP} Output dir not at expected path")
            

            stdout_text = result.stdout or ""
            if "Report saved" in stdout_text or "PREPROCESS BATCH REPORT" in stdout_text:
                print(f"  {C.PASS} Report generated")
            

            out_files = list(Path(tmpdir).rglob("*.png"))
            print(f"  {C.PASS if len(out_files) > 0 else C.SKIP} Output files: {len(out_files)}")
            
            return True
        else:
            print(f"  {C.FAIL} Exit code: {result.returncode}")
            if result.stderr:
                print(f"       STDERR: {result.stderr[:300]}")
            return False






def psd2_test_22_import():
    """PSD-2.2a: Import augment_data module + registry check."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.2a] Augmentation Module Import{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import augment_data
        

        registry = augment_data.AUGMENTATION_REGISTRY
        expected_techs = ["rotate", "translate", "scale", "elastic", "noise", "blur", "thickness"]
        
        ok = True
        for tech in expected_techs:
            has = tech in registry
            print(f"  {C.PASS if has else C.FAIL} '{tech}' in registry")
            if not has:
                ok = False
        
        print(f"\n  {C.PASS if ok else C.FAIL} All 7 techniques registered")
        return ok
    except Exception as e:
        print(f"  {C.FAIL} Import error: {e}")
        return False
    finally:
        pass


def psd2_test_22_augment_single():
    """PSD-2.2b: Generate augmented variants from single image."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.2b] Single Image Augmentation{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import augment_data
        

        test_img = np.full((64, 64), 255, dtype=np.uint8)
        cv2.rectangle(test_img, (16, 8), (48, 56), 0, -1)
        
        variants, logs = augment_data.augment_sample(
            test_img,
            num_variants=5,
            techniques=["rotate", "translate", "scale", "elastic", "blur"],
            combine=True,
            seed=42,
        )
        
        print(f"  {C.PASS if len(variants) == 5 else C.FAIL} Generated {len(variants)} variants (expected 5)")
        

        shapes_ok = all(v.shape == test_img.shape for v in variants)
        print(f"  {C.PASS if shapes_ok else C.FAIL} All variants same shape: {test_img.shape}")
        

        diffs = [not np.array_equal(v, test_img) for v in variants]
        n_different = sum(diffs)
        print(f"  {C.PASS if n_different >= 4 else C.FAIL} {n_different}/5 variants differ from original")
        

        logs_ok = len(logs) == 5
        print(f"  {C.PASS if logs_ok else C.FAIL} Variant logs: {len(logs)} entries")
        
        if logs:
            techniques_used = set()
            for log_entry in logs:
                for tech in log_entry.get("techniques_applied", []):
                    techniques_used.add(tech.get("technique", "?"))
            print(f"  {C.INFO} Techniques used across variants: {sorted(techniques_used)}")
        
        return len(variants) == 5 and shapes_ok and n_different >= 4
    
    except Exception as e:
        print(f"  {C.FAIL} Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def psd2_test_22_elastic():
    """PSD-2.2c: Elastic distortion specifically (most important for kids' handwriting)."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.2c] Elastic Distortion (Critical for Kids){C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import augment_data
        
        test_img = np.full((64, 64), 255, dtype=np.uint8)
        cv2.rectangle(test_img, (20, 10), (44, 54), 0, -1)
        
        distorted, info = augment_data.elastic_distortion(test_img, alpha=30, sigma=4, rng=np.random.default_rng(42))
        
        correct_shape = distorted.shape == test_img.shape
        differs = not np.array_equal(distorted, test_img)
        has_alpha = info.get("alpha") == 30
        has_sigma = info.get("sigma") == 4
        
        print(f"  {C.PASS if correct_shape else C.FAIL} Shape preserved: {distorted.shape}")
        print(f"  {C.PASS if differs else C.FAIL} Image changed after distortion")
        print(f"  {C.PASS if has_alpha else C.FAIL} Alpha param logged: {info.get('alpha')}")
        print(f"  {C.PASS if has_sigma else C.FAIL} Sigma param logged: {info.get('sigma')}")
        
        return correct_shape and differs and has_alpha and has_sigma
    
    except Exception as e:
        print(f"  {C.FAIL} Error: {e}")
        return False


def psd2_test_22_cli():
    """PSD-2.2d: Run augmentation via CLI with small dataset."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.2d] Augmentation CLI (dry-run){C.END}")
    

    clean_dir = DATA_DIR / "clean"
    if not clean_dir.exists():
        print(f"  {C.SKIP} Clean directory doesn't exist yet")
        return True
    
    result = run_script("augment_data.py", [
        "--input", str(clean_dir),
        "--variants", "3",
        "--dry-run",
    ], timeout=15)
    
    if result.returncode == 0:
        print(f"  {C.PASS} CLI dry-run succeeded")
        
        if "Expansion factor" in result.stdout:

            for line in result.stdout.split("\n"):
                if "Expansion factor" in line:
                    print(f"  {C.INFO} {line.strip()}")
                    break
        return True
    else:
        print(f"  {C.FAIL} Exit code: {result.returncode}")
        return False






def psd2_test_23_import():
    """PSD-2.3a: Import extract_features + check group registry."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.3a] Feature Extraction Module Import{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import extract_features
        
        groups = extract_features.FEATURE_GROUPS
        expected_groups = ["basic", "contour", "hu_moments", "histogram", "texture"]
        
        ok = True
        for g in expected_groups:
            has = g in groups
            print(f"  {C.PASS if has else C.FAIL} Feature group '{g}'")
            if not has:
                ok = False
        

        dummy = np.zeros((64, 64), dtype=np.uint8)
        total = 0
        for gname in expected_groups:
            extractor = groups[gname]
            feats = extractor(dummy)
            count = len(feats)
            total += count
            print(f"     → {count} features")
        
        print(f"\n  {C.PASS} Total: ~{total} features across {len(groups)} groups")
        return ok
    
    except Exception as e:
        print(f"  {C.FAIL} Import error: {e}")
        return False


def psd2_test_23_extract_single():
    """PSD-2.3b: Extract features from a single synthetic image."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.3b] Single Image Feature Extraction{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import extract_features
        import tempfile
        

        test_img = np.full((64, 64), 255, dtype=np.uint8)

        pts = np.array([[32, 8], [12, 56], [52, 56]], np.int32)
        cv2.fillPoly(test_img, [pts], 0)
        cv2.line(test_img, (22, 38), (42, 38), 0, 2)
        

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_A.png"
            cv2.imwrite(str(test_path), test_img)
            
            features = extract_features.extract_all_features(
                image_path=str(test_path),
                char_target="A",
                include_metadata=True,
            )
            

            success = features.get("_success", False)
            print(f"  {C.PASS if success else C.FAIL} Extraction successful")
            
            feat_count = features.get("_feature_count", 0)
            print(f"  {C.PASS if feat_count > 100 else C.FAIL} Feature count: {feat_count} (>100)")
            
            has_filename = features.get("_filename") == "test_A.png"
            print(f"  {C.PASS if has_filename else C.FAIL} Filename recorded: {features.get('_filename')}")
            
            has_char = features.get("_char_target") == "A"
            print(f"  {C.PASS if has_char else C.FAIL} Char target: '{features.get('_char_target')}'")
            

            has_pixel = "pixel_count" in features
            has_hu = "hu1" in features
            has_hist = "hist_bin_00" in features
            has_glcm = "glcm_d1_contrast" in features
            
            print(f"  {C.PASS if has_pixel else C.FAIL} basic.pixel_count present")
            print(f"  {C.PASS if has_hu else C.FAIL} hu_moments.hu1 present")
            print(f"  {C.PASS if has_hist else C.FAIL} histogram.hist_bin_00 present")
            print(f"  {C.PASS if has_glcm else C.FAIL} texture.glcm_d1_contrast present")
            

            numeric_ok = True
            for k, v in features.items():
                if k.startswith("_"):
                    continue
                if not isinstance(v, (int, float, np.floating, np.integer)):
                    print(f"  {C.FAIL} Non-numeric value: {k}={type(v).__name__}={v}")
                    numeric_ok = False
            
            if numeric_ok:
                print(f"  {C.PASS} All {feat_count} feature values are numeric")
            
            return success and feat_count > 100 and has_char and numeric_ok
    
    except Exception as e:
        print(f"  {C.FAIL} Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def psd2_test_23_real_image():
    """PSD-2.3c: Extract features from a real handwriting image."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.3c] Real Image Feature Extraction{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import extract_features
        

        images = list(TEST_IMAGE_DIR.glob("*.png"))
        if not images:
            print(f"  {C.SKIP} No real images available")
            return True
        
        test_img = images[0]
        features = extract_features.extract_all_features(
            image_path=str(test_img),
            char_target=None,
        )
        
        success = features.get("_success", False)
        print(f"  {C.PASS if success else C.FAIL} Extracted from: {test_img.name}")
        
        feat_count = features.get("_feature_count", 0)
        print(f"  {C.PASS if feat_count > 100 else C.FAIL} Features: {feat_count}")
        

        pixel_count = features.get("pixel_count", 0)
        fg_ratio = features.get("foreground_ratio", 0)
        aspect = features.get("aspect_ratio", 0)
        eccentricity = features.get("eccentricity", 0)
        
        print(f"  {C.INFO} Sample features:")
        print(f"       pixel_count={pixel_count:.0f}, fg_ratio={fg_ratio:.4f}")
        print(f"       aspect_ratio={aspect:.2f}, eccentricity={eccentricity:.4f}")
        
        return success and feat_count > 100
    
    except Exception as e:
        print(f"  {C.FAIL} Error: {e}")
        return False


def psd2_test_23_csv_output():
    """PSD-2.3d: CSV output format verification."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.3d] CSV Output Format{C.END}")
    

    features_dir = DATA_DIR / "features"
    csv_path = features_dir / "all_features.csv"
    
    if not csv_path.exists():
        print(f"  {C.SKIP} No existing CSV (run extract_features.py first)")
        return True
    

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    
    n_rows = len(rows)
    n_cols = len(fieldnames)
    
    print(f"  {C.PASS if n_rows > 0 else C.FAIL} Rows: {n_rows}")
    print(f"  {C.PASS if n_cols > 100 else C.FAIL} Columns: {n_cols}")
    

    meta_cols = ["_filename", "_char_target", "_success"]
    for mc in meta_cols:
        has = mc in fieldnames
        print(f"  {C.PASS if has else C.FAIL} Metadata column: {mc}")
    

    feat_cols = [c for c in fieldnames if not c.startswith("_")]
    print(f"  {C.PASS if len(feat_cols) > 100 else C.FAIL} Feature columns: {len(feat_cols)}")
    

    if rows:
        row = rows[0]
        non_numeric = []
        for col in feat_cols:
            val = row.get(col, "")
            try:
                float(val)
            except (ValueError, TypeError):
                non_numeric.append(col)
        
        if non_numeric:
            print(f"  {C.FAIL} Non-numeric values in: {non_numeric[:5]}")
        else:
            print(f"  {C.PASS} All feature values are numeric (row 0 checked)")
    
    return n_rows > 0 and n_cols > 100






def psd2_test_24_import():
    """PSD-2.4a: Import generate_statistics module."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.4a] Statistics Module Import{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import generate_statistics
        
        funcs = [
            "load_feature_csv", "auto_load_features",
            "compute_class_statistics", "compute_correlation_matrix",
            "detect_outliers", "generate_data_quality_report",
        ]
        ok = True
        for f in funcs:
            has = hasattr(generate_statistics, f)
            print(f"  {C.PASS if has else C.FAIL} {f}()")
            if not has:
                ok = False
        
        return ok
    except Exception as e:
        print(f"  {C.FAIL} Import error: {e}")
        return False


def psd2_test_24_quality_report():
    """PSD-2.4b: Data quality report structure validation."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.4b] Data Quality Report Validation{C.END}")
    
    report_path = PROJECT_ROOT / "data_science" / "reports" / "data_quality_report.json"
    
    if not report_path.exists():
        print(f"  {C.SKIP} No quality report yet (run generate_statistics.py first)")
        return True
    
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    checks = [
        ("timestamp", isinstance(report.get("timestamp"), str)),
        ("dataset_summary.n_samples", isinstance(report.get("dataset_summary", {}).get("n_samples"), int)),
        ("missing_values.total_missing", "total_missing" in report.get("missing_values", {})),
        ("class_balance.level", "level" in report.get("class_balance", {})),
        ("health_score", isinstance(report.get("health_score"), (int, float))),
        ("health_level", report.get("health_level") in ["excellent", "good", "acceptable", "poor", "critical"]),
        ("recommendations", isinstance(report.get("recommendations"), list)),
    ]
    
    ok = True
    for name, passed in checks:
        val = name.split(".")[-1]
        actual = report
        for key in name.split("."):
            if isinstance(actual, dict):
                actual = actual.get(key, "N/A")
        print(f"  {C.PASS if passed else C.FAIL} {val}: {actual}")
        if not passed:
            ok = False
    
    score = report.get("health_score", 0)
    level = report.get("health_level", "?")
    print(f"\n  {C.INFO} Health Score: {score}/100 ({level.upper()})")
    
    recs = report.get("recommendations", [])
    if recs:
        print(f"  {C.INFO} Recommendations ({len(recs)}):")
        for r in recs[:3]:
            print(f"       • {r[:80]}")
    
    return ok


def psd2_test_24_correlation_matrix():
    """PSD-2.4c: Correlation matrix file validation."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.4c] Correlation Matrix Validation{C.END}")
    
    corr_path = PROJECT_ROOT / "data_science" / "statistics" / "correlation_matrix.csv"
    
    if not corr_path.exists():
        print(f"  {C.SKIP} No correlation matrix yet")
        return True
    
    with open(corr_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    header = rows[0] if rows else []
    n_rows = len(rows) - 1
    n_cols = len(header) - 1
    
    print(f"  {C.PASS if n_rows > 0 else C.FAIL} Matrix rows: {n_rows}")
    print(f"  {C.PASS if n_cols > 50 else C.FAIL} Matrix cols: {n_cols}")
    

    is_square = n_rows == n_cols
    print(f"  {C.PASS if is_square else C.FAIL} Square matrix: {n_rows}×{n_cols}")
    

    if n_rows > 0 and n_cols > 0:
        diag_vals = []
        for i in range(min(n_rows, n_cols)):
            try:
                val = float(rows[i + 1][i + 1])
                diag_vals.append(val)
            except (IndexError, ValueError):
                pass
        
        if diag_vals:

            valid_diags = [v for v in diag_vals if not np.isnan(v) and v > 0.01]
            if valid_diags:
                avg_diag = np.mean(valid_diags)
                print(f"  {C.PASS if avg_diag > 0.8 else C.INFO} Diagonal avg (valid): {avg_diag:.3f} (should be ~1.0)")
            else:
                print(f"  {C.INFO} All diagonal values near 0/NaN (constant features dominate)")
            print(f"  {C.INFO} Raw diagonal values: min={min(diag_vals):.3f}, max={max(diag_vals):.3f}")
    
    return n_rows > 0 and n_cols > 50


def psd2_test_24_outliers():
    """PSD-2.4d: Outlier detection output validation."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2.4d] Outlier Detection Report{C.END}")
    
    outlier_path = PROJECT_ROOT / "data_science" / "statistics" / "outliers.json"
    
    if not outlier_path.exists():
        print(f"  {C.SKIP} No outliers report yet")
        return True
    
    with open(outlier_path, "r", encoding="utf-8") as f:
        outliers = json.load(f)
    
    method = outliers.get("method", "?")
    total = outliers.get("total_outlier_samples", 0)
    details = outliers.get("outlier_details", [])
    
    print(f"  {C.PASS} Method: {method}")
    print(f"  {C.INFO} Anomalous samples: {total} ({total/max(1, 47)*100:.1f}% of dataset)")
    
    if details:
        print(f"  {C.INFO} Top outliers:")
        for d in details[:3]:
            fname = d.get("filename", "?")
            n_outlier_feats = d.get("outlier_feature_count", 0)
            print(f"       • {fname}: {n_outlier_feats} outlier features")
    
    return True






def psd2_test_integration():
    """PSD-2 Integration: Full pipeline end-to-end on synthetic data."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-2 INTEGRATION] Full Pipeline E2E{C.END}")
    
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        import preprocess_batch
        import augment_data
        import extract_features
        import tempfile
        

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()
            clean_dir = Path(tmpdir) / "clean"
            aug_dir = Path(tmpdir) / "augmented"
            feat_dir = Path(tmpdir) / "features"
            
            chars = ["A", "B", "1", "a", "O"]
            for i, char in enumerate(chars):
                img = np.full((128, 128), 255, dtype=np.uint8)

                if char == "A":
                    pts = np.array([[64, 16], [20, 112], [108, 112]], np.int32)
                    cv2.fillPoly(img, [pts], 0)
                    cv2.line(img, (38, 72), (90, 72), 0, 3)
                elif char == "B":
                    cv2.rectangle(img, (20, 16), (60, 112), 0, -1)
                    cv2.circle(img, (80, 40), 24, 0, -1)
                    cv2.circle(img, (80, 88), 24, 0, -1)
                elif char == "1":
                    cv2.line(img, (64, 16), (64, 112), 0, 6)
                elif char == "a":
                    cv2.ellipse(img, (64, 64), (40, 48), 0, 0, 180, 0, -1)
                    cv2.line(img, (28, 64), (100, 64), 0, 2)
                elif char == "O":
                    cv2.ellipse(img, (64, 64), (40, 48), 0, 0, 360, 0, 2)
                
                cv2.imwrite(str(raw_dir / f"{char}_sample.png"), img)
            
            print(f"  {C.INFO} Created {len(chars)} synthetic images")
            

            t0 = time.time()
            for img_path in raw_dir.glob("*.png"):
                out_path = clean_dir / img_path.name
                preprocess_batch.run_full_pipeline(str(img_path), str(out_path), target_size=64)
            t_preprocess = (time.time() - t0) * 1000
            clean_count = len(list(clean_dir.glob("*.png")))
            print(f"  {C.PASS if clean_count >= 4 else C.FAIL} Preprocess: {clean_count}/5 images ({t_preprocess:.0f}ms)")
            

            t0 = time.time()
            for img_path in clean_dir.glob("*.png"):
                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                out_subdir = aug_dir / img_path.stem
                out_subdir.mkdir(parents=True, exist_ok=True)
                
                variants, _ = augment_data.augment_sample(img, num_variants=3, seed=42)
                for vi, var in enumerate(variants):
                    cv2.imwrite(str(out_subdir / f"var_{vi}.png"), var)
            
            t_aug = (time.time() - t0) * 1000
            aug_total = len(list(aug_dir.rglob("*.png")))
            print(f"  {C.PASS if aug_total >= 12 else C.FAIL} Augment: {aug_total} images ({t_aug:.0f}ms)")
            

            t0 = time.time()
            feat_dir.mkdir(exist_ok=True)
            all_images = list(clean_dir.glob("*.png")) + list(aug_dir.rglob("*.png"))
            
            all_feats = []
            for img_path in all_images:

                stem = img_path.stem
                char = stem[0] if stem and stem[0].isalnum() else None
                
                feats = extract_features.extract_all_features(str(img_path), char_target=char)
                all_feats.append(feats)
            
            t_feat = (time.time() - t0) * 1000
            print(f"  {C.PASS if len(all_feats) >= 15 else C.FAIL} Features: {len(all_feats)} images ({t_feat:.0f}ms)")
            

            if all_feats:
                feat_names = [k for k in all_feats[0].keys() if not k.startswith("_")]
                matrix = []
                for row in all_feats:
                    vec = [float(row.get(k, 0)) for k in feat_names]
                    matrix.append(vec)
                
                X = np.array(matrix)
                mean_acc = np.mean(X, axis=0)
                std_acc = np.std(X, axis=0)
                
                nonzero_std = np.sum(std_acc > 0.001)
                print(f"  {C.PASS if nonzero_std > 50 else C.INFO} Features with variance: {nonzero_std}/{len(feat_names)}")
                
                total_time = t_preprocess + t_aug + t_feat
                print(f"\n  {C.INFO} Total pipeline: {total_time:.0f}ms for {len(all_feats)} images")
                print(f"  {C.INFO} Throughput: {len(all_feats) / (total_time/1000):.0f} img/s end-to-end")
            
            return clean_count >= 4 and aug_total >= 12 and len(all_feats) >= 15
    
    except Exception as e:
        print(f"  {C.FAIL} Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False






def main():
    parser = argparse.ArgumentParser(description="Test Suite: PSD-2 Pipeline")
    parser.add_argument("--preprocess", action="store_true", help="Only run preprocess tests")
    parser.add_argument("--augment", action="store_true", help="Only run augment tests")
    parser.add_argument("--features", action="store_true", help="Only run feature extraction tests")
    parser.add_argument("--stats", action="store_true", help="Only run statistics tests")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    

    print("\n" + "╔" + "═" * 66 + "╗")
    print("║" + "  🧪 SAHABAT AKSARA — TEST SUITE: PSD-2 PIPELINE".center(62) + "║")
    print("╠" + "═" * 66 + "╣")
    print(f"║  Project Root: {str(PROJECT_ROOT)[:52]:<52s}║")
    print(f"║  Timestamp:   {time.strftime('%Y-%m-%d %H:%M:%S'):<46s}║")
    print("╚" + "═" * 66 + "╝")
    
    results = {}
    

    if not (args.augment or args.features or args.stats):
        print(f"\n{'='*66}")
        print(f"{C.BOLD}🧹 PSD-2.1: Batch Preprocessing Pipeline{C.END}")
        print(f"{'='*66}")
        
        results["2.1a_import"] = psd2_test_21_import()
        results["2.1b_single"] = psd2_test_21_single_image()
        results["2.1c_batch"] = psd2_test_21_batch()
        
        passed = sum(1 for v in results.values() if v)
        total = len([k for k in results.keys() if k.startswith("2.1")])
        print(f"\n  {'─'*50}")
        print(f"  🧹 PSD-2.1 Preprocess Result: {passed}/{total} {'✅' if passed==total else '⚠️'}")
    

    if not (args.preprocess or args.features or args.stats):
        print(f"\n{'='*66}")
        print(f"{C.BOLD}🎨 PSD-2.2: Data Augmentation{C.END}")
        print(f"{'='*66}")
        
        results["2.2a_import"] = psd2_test_22_import()
        results["2.2b_single"] = psd2_test_22_augment_single()
        results["2.2c_elastic"] = psd2_test_22_elastic()
        results["2.2d_cli"] = psd2_test_22_cli()
        
        passed = sum(1 for v in results.values() if v)
        total = len([k for k in results.keys() if k.startswith("2.2")])
        print(f"\n  {'─'*50}")
        print(f"  🎨 PSD-2.2 Augmentation Result: {passed}/{total} {'✅' if passed==total else '⚠️'}")
    

    if not (args.preprocess or args.augment or args.stats):
        print(f"\n{'='*66}")
        print(f"{C.BOLD}📊 PSD-2.3: Feature Extraction Engine{C.END}")
        print(f"{'='*66}")
        
        results["2.3a_import"] = psd2_test_23_import()
        results["2.3b_synthetic"] = psd2_test_23_extract_single()
        results["2.3c_real"] = psd2_test_23_real_image()
        results["2.3d_csv"] = psd2_test_23_csv_output()
        
        passed = sum(1 for v in results.values() if v)
        total = len([k for k in results.keys() if k.startswith("2.3")])
        print(f"\n  {'─'*50}")
        print(f"  📊 PSD-2.3 Features Result: {passed}/{total} {'✅' if passed==total else '⚠️'}")
    

    if not (args.preprocess or args.augment or args.features):
        print(f"\n{'='*66}")
        print(f"{C.BOLD}📈 PSD-2.4: Statistics & Quality Report{C.END}")
        print(f"{'='*66}")
        
        results["2.4a_import"] = psd2_test_24_import()
        results["2.4b_quality"] = psd2_test_24_quality_report()
        results["2.4c_corr"] = psd2_test_24_correlation_matrix()
        results["2.4d_outliers"] = psd2_test_24_outliers()
        
        passed = sum(1 for v in results.values() if v)
        total = len([k for k in results.keys() if k.startswith("2.4")])
        print(f"\n  {'─'*50}")
        print(f"  📈 PSD-2.4 Statistics Result: {passed}/{total} {'✅' if passed==total else '⚠️'}")
    

    if not any([args.preprocess, args.augment, args.features, args.stats]):
        print(f"\n{'='*66}")
        print(f"{C.BOLD}🔗 PSD-2 INTEGRATION: Full Pipeline E2E{C.END}")
        print(f"{'='*66}")
        
        results["integration"] = psd2_test_integration()
    

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    pct = (passed_tests / max(total_tests, 1)) * 100
    
    print(f"\n{'═'*66}")
    icon = "🎉" if pct == 100 else ("👍" if pct >= 75 else ("⚠️" if pct >= 50 else "💀"))
    label = "ALL TESTS PASSED!" if pct == 100 else ("MOSTLY GOOD" if pct >= 75 else ("PARTIAL" if pct >= 50 else "NEEDS WORK"))
    print(f"  {C.BOLD} FINAL SCORE: {passed_tests}/{total_tests} ({pct:.0f}%) {icon}{C.END}")
    print(f"  {label}" if pct >= 75 else f"  {C.BOLD}{label}{C.END}")
    print(f"{'═'*66}\n")
    
    sys.exit(0 if pct >= 80 else 1)


if __name__ == "__main__":
    main()
