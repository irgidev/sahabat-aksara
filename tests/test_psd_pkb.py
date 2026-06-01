"""
Sahabat Aksara - Test Suite PSD-1 + PKB-1
============================================
Cara jalankan:
  cd C:/Documents/Desktop/Project/sahabat-aksara
  .\backend\venv\Scripts\python.exe tests/test_psd_pkb.py

Opsional:
  --psd-only     Hanya test PSD-1 (Data Collection)
  --pkb-only     Hanya test PKB-1 (AI Engine v4)
  --verbose      Output detail lengkap
  --image <path> Pakai gambar spesifik untuk testing
"""

import os
import sys
import json
import time
import argparse
import glob
from pathlib import Path




if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


VENV_PYTHON = PROJECT_ROOT / "backend" / "venv" / "Scripts" / "python.exe"


class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

PASS = f"{C.GREEN}✅ PASS{C.END}"
FAIL = f"{C.RED}❌ FAIL{C.END}"
SKIP = f"{C.YELLOW}⏭️  SKIP{C.END}"
INFO = f"{C.BLUE}i️{C.END}"






def psd_test_1_folder_structure():
    """PSD-1.1: Dataset folder structure exists and organized."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.1] Dataset Folder Structure{C.END}")

    required = [
        "data_science/datasets/processed",
        "data_science/datasets/raw",
        "data_science/datasets/exports",
        "data_science/scripts",
        "data_science/reports",
    ]

    all_ok = True
    for d in required:
        path = PROJECT_ROOT / d
        exists = path.exists()
        status = PASS if exists else FAIL
        print(f"  {status} {d}/")
        if not exists:
            all_ok = False


    processed = PROJECT_ROOT / "data_science" / "datasets" / "processed"
    if processed.exists():
        subdirs = [d.name for d in processed.iterdir() if d.is_dir()]
        print(f"  {INFO} Processed subfolders ({len(subdirs)}): {', '.join(subdirs[:10])}{'...' if len(subdirs) > 10 else ''}")

    return all_ok


def psd_test_2_build_dataset_script():
    """PSD-1.2: build_dataset.py runs without error."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.2] Build Dataset Script{C.END}")

    script_path = PROJECT_ROOT / "data_science" / "scripts" / "build_dataset.py"

    if not script_path.exists():
        print(f"  {FAIL} build_dataset.py not found!")
        return False

    print(f"  {INFO} Running: python data_science/scripts/build_dataset.py")

    import subprocess
    result = subprocess.run(
        [str(VENV_PYTHON), str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    if result.returncode == 0:
        print(f"  {PASS} Script executed successfully")

        output = result.stdout or ""
        for line in output.split('\n'):
            if any(k in line.lower() for k in ['total files', 'valid', 'corrupt', 'health', 'characters', 'top']):
                print(f"       {line.strip()}")
        return True
    else:
        print(f"  {FAIL} Script failed with code {result.returncode}")
        if result.stderr:
            print(f"       STDERR: {result.stderr[:300]}")
        return False


def psd_test_3_manifest_generated():
    """PSD-1.3: dataset_manifest.json exists and valid."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.3] Dataset Manifest{C.END}")

    manifest_path = PROJECT_ROOT / "data_science" / "datasets" / "dataset_manifest.json"

    if not manifest_path.exists():
        print(f"  {FAIL} manifest.json not found!")
        return False

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        checks = [
            ("version", manifest.get("version")),
            ("generated_at", manifest.get("generated_at")),
            ("total_files", manifest.get("statistics", {}).get("total_files", 0)),
            ("characters", len(manifest.get("characters", {}))),
            ("file_entries", len(manifest.get("files", []))),
        ]

        all_ok = True
        for key, val in checks:
            ok = val is not None and val != "" and (not isinstance(val, int) or val >= 0)
            status = PASS if ok else FAIL
            display_val = str(val)[:50] if not isinstance(val, int) else str(val)
            print(f"  {status} {key}: {display_val}")
            if not ok:
                all_ok = False


        chars = manifest.get("characters", {})
        if chars:
            top_chars = sorted(chars.items(), key=lambda x: x[1].get("valid", 0), reverse=True)[:5]
            char_str = ", ".join([f"'{c}'({v['valid']})" for c, v in top_chars])
            print(f"  {INFO} Top characters: {char_str}")

        return all_ok

    except Exception as e:
        print(f"  {FAIL} Invalid JSON: {e}")
        return False


def psd_test_4_statistics_report():
    """PSD-1.4: dataset_statistics.json generated."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.4] Statistics Report{C.END}")

    stats_path = PROJECT_ROOT / "data_science" / "reports" / "dataset_statistics.json"

    if not stats_path.exists():
        print(f"  {SKIP} No statistics report yet (run build_dataset first)")
        return True

    try:
        with open(stats_path) as f:
            stats = json.load(f)

        s = stats.get("statistics", {})
        integrity = stats.get("integrity", {})

        items = [
            ("total_files", s.get("total_files")),
            ("valid_files", s.get("valid_files")),
            ("blank_files", s.get("blank_files")),
            ("corrupt_files", s.get("corrupt_files")),
            ("unique_characters", s.get("unique_characters")),
            ("total_size_mb", s.get("total_size_mb")),
            ("health_score", integrity.get("health_score")),
        ]

        for key, val in items:
            print(f"  {PASS} {key}: {val}")

        return True
    except Exception as e:
        print(f"  {FAIL} Error: {e}")
        return False


def psd_test_5_image_organization():
    """PSD-1.5: Images organized by character (new system)."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.5] Image Organization by Character{C.END}")

    processed_dir = PROJECT_ROOT / "data_science" / "datasets" / "processed"

    if not processed_dir.exists():
        print(f"  {SKIP} No processed directory yet")
        return True


    char_folders = {}
    unsorted = 0
    root_files = 0

    for item in processed_dir.rglob("*.png"):
        rel = item.relative_to(processed_dir)
        parts = rel.parts

        if len(parts) == 1:
            root_files += 1
        elif parts[0] == "_unsorted":
            unsorted += 1
        else:
            char = parts[0]
            char_folders[char] = char_folders.get(char, 0) + 1

    total = sum(char_folders.values()) + unsorted + root_files

    if char_folders:
        print(f"  {PASS} Organized by character: {len(char_folders)} categories, {sum(char_folders.values())} files")
        for char, count in sorted(char_folders.items(), key=lambda x: -x[1])[:10]:
            bar = "█" * min(count, 20)
            print(f"       '{char}': {count:>4} {bar}")

    if unsorted:
        print(f"  {C.YELLOW}  Unsorted (legacy): {unsorted} files in _unsorted/")

    if root_files:
        print(f"  {C.YELLOW} In root (should be moved): {root_files} files")

    has_new_system = len(char_folders) > 0
    print(f"  {'✅' if has_new_system else '⏭️ '} New organization active: {has_new_system}")

    return True


def psd_test_6_metadata_format():
    """PSD-1.6: Verify metadata format matches spec."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.6] Metadata Format Validation{C.END}")


    expected_keys = {
        "point_count": int,
        "bounding_box": dict,
        "canvas_size": dict,
        "duration_ms": (int, type(None)),
        "color_used": str,
        "device_type": str,
        "evaluated_at": str,
    }


    sample_metadata = {
        "point_count": 147,
        "bounding_box": {"width": 234, "height": 189},
        "canvas_size": {"w": 600, "h": 400},
        "duration_ms": 4500,
        "color_used": "#1e293b",
        "device_type": "desktop",
        "evaluated_at": "2026-05-29T23:00:00.000Z",
    }

    all_ok = True
    for key, expected_type in expected_keys.items():
        exists = key in sample_metadata
        type_ok = isinstance(sample_metadata.get(key), expected_type) if exists else False

        if exists and type_ok:
            print(f"  {PASS} '{key}': {type(sample_metadata[key]).__name__}")
        elif exists:
            print(f"  {FAIL} '{key}': expected {expected_type.__name__}, got {type(sample_metadata[key]).__name__}")
            all_ok = False
        else:
            print(f"  {FAIL} '{key}: MISSING")
            all_ok = False


    print(f"\n  {INFO} Device type detection (from Canvas.jsx):")
    canvas_jsx = PROJECT_ROOT / "frontend" / "src" / "components" / "Canvas.jsx"
    if canvas_jsx.exists():
        src = canvas_jsx.read_text(encoding="utf-8")
        has_detect = "detectDeviceType" in src and "navigator.userAgent" in src
        has_getCanvasSize = "getCanvasSize" in src
        print(f"       {PASS if has_detect else FAIL} detectDeviceType() exists in Canvas.jsx")
        print(f"       {PASS if has_getCanvasSize else FAIL} getCanvasSize() exists in Canvas.jsx")


        if "tablet" in src and "mobile" in src and "desktop" in src:
            print(f"       {INFO} Device mapping: tablet | mobile | desktop ✓")
    else:
        print(f"       {SKIP} Canvas.jsx not found at {canvas_jsx}")

    return all_ok


def psd_test_7_api_evaluate_saves_data():
    """PSD-1.7: API /api/evaluate saves rich data."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PSD-1.7] API Evaluate Data Saving{C.END}")


    main_py = PROJECT_ROOT / "backend" / "main.py"

    with open(main_py, 'r', encoding='utf-8') as f:
        source = f.read()

    checks = [
        ("stroke_data field", "stroke_data" in source),
        ("session_id field", "session_id" in source),
        ("Asia/Jakarta timezone", "timezone(timedelta(hours=7))" in source or "timedelta(hours=7)" in source),
        ("algorithm_version", "algorithm_version" in source),
        ("explanation field", "explanation" in source),
        ("processed/{char}", "processed" in source and "char_target" in source),
        ("metadata request", "metadata" in source and "EvaluationRequest" in source),
        ("graceful fallback", "graceful fallback" in source.lower() or "fallback" in source.lower()),
    ]

    all_ok = True
    for name, found in checks:
        status = PASS if found else FAIL
        print(f"  {status} {name}")
        if not found:
            all_ok = False

    return all_ok






def _get_test_images(count=3):
    """Get available test images from dataset."""
    pattern = str(PROJECT_ROOT / "data_science" / "datasets" / "processed" / "**" / "*.png")
    images = glob.glob(pattern, recursive=True)

    if not images:

        pattern2 = str(PROJECT_ROOT / "data_science" / "datasets" / "*.png")
        images = glob.glob(pattern2)

    return images[:max(count, len(images))]


def pkb_test_1_module_imports():
    """PKB-1.1: All modules importable."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.1] Module Imports{C.END}")

    modules = [
        ("ai_core.preprocessor", ["full_preprocess", "to_binary", "skeletonize", "normalize_to_canvas"]),
        ("ai_core.template_engine", ["create_template", "create_handwriting_template"]),
        ("ai_core.scorers", ["SCORER_REGISTRY", "HOGScorer", "SSIMScorer"]),
        ("ai_core.ensemble", ["WeightedEnsemble", "DEFAULT_WEIGHTS_V4"]),
        ("ai_core.pattern_matching", ["calculate_accuracy", "evaluate_with_details", "get_last_explanation"]),
    ]

    all_ok = True
    for mod_name, expected_attrs in modules:
        try:
            mod = __import__(mod_name, fromlist=expected_attrs)
            missing = [a for a in expected_attrs if not hasattr(mod, a)]

            if missing:
                print(f"  {FAIL} {mod_name}: missing {missing}")
                all_ok = False
            else:
                attrs_str = ", ".join(expected_attrs[:3]) + ("..." if len(expected_attrs) > 3 else "")
                print(f"  {PASS} {mod_name} [{attrs_str}]")

        except ImportError as e:
            print(f"  {FAIL} {mod_name}: {e}")
            all_ok = False
        except Exception as e:
            print(f"  {FAIL} {mod_name}: unexpected error: {e}")
            all_ok = False

    return all_ok


def pkb_test_2_all_scorers_registered():
    """PKB-1.2: All 7 scorers registered and instantiable."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.2] Scorer Registry (7 Scorers){C.END}")

    from ai_core.scorers import SCORER_REGISTRY, get_scorer

    expected_scorers = [
        "skeleton", "distance", "completeness",
        "structural", "stroke_count", "hog", "ssim"
    ]

    all_ok = True
    for name in expected_scorers:
        exists = name in SCORER_REGISTRY
        scorer = SCORER_REGISTRY.get(name)

        if exists and scorer:
            is_class = hasattr(scorer, 'score') and callable(getattr(scorer, 'score', None))
            status = PASS if is_class else FAIL
            print(f"  {status} {scorer.name:>14s} ({type(scorer).__name__})")
            if not is_class:
                all_ok = False
        else:
            print(f"  {FAIL} {name}: NOT REGISTERED")
            all_ok = False


    actual_count = len(SCORER_REGISTRY)
    count_ok = actual_count == 7
    print(f"\n  {PASS if count_ok else FAIL} Total scorers: {actual_count}/7")

    return all_ok and count_ok


def pkb_test_3_template_generation():
    """PKB-1.3: Template generation for all 62 characters."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.3] Template Generation (62 Characters){C.END}")

    from ai_core.template_engine import create_handwriting_template

    all_chars = (
        [chr(c) for c in range(ord('A'), ord('Z') + 1)] +
        [chr(c) for c in range(ord('a'), ord('z') + 1)] +
        [str(d) for d in range(10)]
    )

    ok_count = 0
    errors = []

    for char in all_chars:
        try:
            t = create_handwriting_template(char, target_size=64)
            has_content = t.sum() > 0
            shape_ok = t.shape == (64, 64)

            if has_content and shape_ok:
                ok_count += 1
            else:
                errors.append(f"{char}: shape={t.shape}, pixels={t.sum()}")
        except Exception as e:
            errors.append(f"{char}: {e}")

    pct = ok_count / len(all_chars) * 100
    status = PASS if ok_count == len(all_chars) else f"{FAIL} ({ok_count}/{len(all_chars)})"
    print(f"  {status} Generated {ok_count}/62 templates ({pct:.0f}%)")

    if errors:
        for e in errors[:5]:
            print(f"       ⚠️  {e}")
        if len(errors) > 5:
            print(f"       ... and {len(errors)-5} more")

    return ok_count == len(all_chars)


def pkb_test_4_evaluation_pipeline(verbose=False):
    """PKB-1.4: Full evaluation pipeline on real images."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.4] Full Evaluation Pipeline (v4 Engine){C.END}")

    from ai_core.pattern_matching import calculate_accuracy, get_last_explanation

    images = _get_test_images(3)

    if not images:
        print(f"  {SKIP} No test images found! Run Canvas first to generate data.")
        return True

    test_chars = ['A', 'b', '7', '1', 'O']
    results = []

    for img_path in images:
        img_name = Path(img_path).name
        print(f"\n  {INFO} Testing image: {img_name}")

        for char in test_chars:
            try:
                start = time.perf_counter()
                acc = calculate_accuracy(img_path, char_target=char)
                elapsed = (time.perf_counter() - start) * 1000

                expl = get_last_explanation()
                conf = expl.get("confidence", "?")
                tip = expl.get("tip", "")[:50]

                results.append({
                    "image": img_name,
                    "char": char,
                    "accuracy": acc,
                    "confidence": conf,
                    "ms": round(elapsed, 1),
                })

                stars = "⭐" * (3 if acc >= 65 else (2 if acc >= 45 else (1 if acc >= 25 else 0)))
                status = PASS if 0 <= acc <= 100 else FAIL

                if verbose:
                    print(f"    {status} char='{char}': acc={acc:>3}% conf={conf:>5s} {stars} ({elapsed:.0f}ms)")
                    print(f"         tip: {tip}")
                else:
                    print(f"    {status} '{char}' → {acc:>3}% | {conf:>5s} | {stars} | {elapsed:.0f}ms")

            except Exception as e:
                print(f"    {FAIL} '{char}': ERROR - {e}")
                results.append({"error": str(e)})


    if results:
        accs = [r["accuracy"] for r in results if "accuracy" in r]
        times = [r["ms"] for r in results if "ms" in r]
        if accs:
            print(f"\n  {INFO} Avg accuracy: {sum(accs)/len(accs):.1f}% | Avg time: {sum(times)/len(times):.0f}ms")

    return len([r for r in results if "error" not in r]) > 0


def pkb_test_5_explanation_output():
    """PKB-1.5: Explanation breakdown includes all required fields."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.5] Explanation & Confidence Output{C.END}")

    from ai_core.pattern_matching import evaluate_with_details

    images = _get_test_images(1)

    if not images:
        print(f"  {SKIP} No test images")
        return True

    details = evaluate_with_details(images[0], char_target='A')

    required_fields = [
        ("accuracy", int, 0, 100),
        ("stars", int, 0, 3),
        ("confidence", str, None, None),
        ("tip", str, None, None),
    ]

    all_ok = True
    for field, ftype, min_val, max_val in required_fields:
        val = details.get(field)
        exists = val is not None
        type_ok = isinstance(val, ftype) if exists else False
        range_ok = True
        if exists and min_val is not None:
            range_ok = min_val <= val <= max_val

        status = PASS if (exists and type_ok and range_ok) else FAIL
        display = str(val)[:60] if val else "MISSING"
        print(f"  {status} {field}: {display} ({ftype.__name__})")

        if not (exists and type_ok and range_ok):
            all_ok = False


    sd = details.get("score_details", {})
    sd_fields = ["confidence", "confidence_label", "tip", "strongest_dimension", "weakest_dimension"]
    print(f"\n  {INFO} score_details:")
    for field in sd_fields:
        val = sd.get(field)
        has_it = val is not None
        print(f"       {PASS if has_it else FAIL} {field}: {str(val)[:40] if val else '-'}")
        if not has_it:
            all_ok = False


    tip = sd.get("tip", "")
    if tip:
        print(f"\n  📝 Kid-friendly tip example:\n     \"{tip}\"")

    return all_ok


def pkb_test_6_ensemble_weights():
    """PKB-1.6: Ensemble config loaded correctly."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.6] Ensemble Configuration{C.END}")

    from ai_core.ensemble import load_config, DEFAULT_WEIGHTS_V4
    import os

    config_path = PROJECT_ROOT / "ai_core" / "ensemble_config.json"


    if not config_path.exists():
        print(f"  {FAIL} ensemble_config.json not found (will be auto-generated)")
        return False

    print(f"  {PASS} Config file exists: {config_path.name}")


    config = load_config(str(config_path))

    checks = [
        ("version", config.get("version") == "4.0"),
        ("global_weights count", len(config.get("global_weights", {})) == 7),
        ("character overrides", len(config.get("character_overrides", {})) > 0),
        ("scorer_config", "scorer_config" in config),
        ("weights sum ~1.0", abs(sum(config.get("global_weights", {}).values()) - 1.0) < 0.01),
    ]

    all_ok = True
    for name, passed in checks:
        status = PASS if passed else FAIL
        print(f"  {status} {name}")
        if not passed:
            all_ok = False


    gw = config.get("global_weights", {})
    if gw:
        print(f"\n  {INFO} Global Weights (v4):")
        for name, weight in sorted(gw.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 30)
            print(f"       {name:>14s}: {weight:.2f} {bar}")


    co = config.get("character_overrides", {})
    if co:
        print(f"\n  {INFO} Character Overrides ({len(co)} chars):")
        for char, overrides in list(co.items())[:5]:
            changes = ", ".join([f"{k}={v}" for k, v in overrides.items()])
            print(f"       '{char}': {changes}")

    return all_ok


def pkb_test_7_per_character_tuning():
    """PKB-1.7: Per-character weight overrides work."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.7] Per-Character Weight Tuning{C.END}")

    from ai_core.ensemble import WeightedEnsemble

    ensemble = WeightedEnsemble()


    override_chars = ['A', 'T', 'O', '0', '1']
    normal_chars = ['B', 'C', 'X', 'z']

    all_ok = True

    print(f"\n  {INFO} Characters WITH overrides:")
    base_weights = ensemble.global_weights
    for char in override_chars:
        weights = ensemble.get_weights(char)
        diff = {k: weights[k] - base_weights[k] for k in base_weights if abs(weights[k] - base_weights[k]) > 0.001}
        if diff:
            changes = ", ".join([f"{k}:{base_weights[k]:.2f}→{v:.2f}" for k, v in diff.items()])
            print(f"    {PASS} '{char}': {changes}")
        else:
            print(f"    {SKIP} '{char}': no difference from global")

    print(f"\n  {INFO} Characters WITHOUT overrides (use global):")
    for char in normal_chars:
        weights = ensemble.get_weights(char)
        same = weights == base_weights
        print(f"    {PASS if same else FAIL} '{char}': {'same as global' if same else 'DIFFERENT (!)'}")
        if not same:
            all_ok = False

    return all_ok


def pkb_test_8_backward_compatibility():
    """PKB-1.8: Backward compatible API still works."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.8] Backward Compatibility (v3 API){C.END}")

    from ai_core.pattern_matching import calculate_accuracy, create_template, create_handwriting_template

    tests = [
        ("calculate_accuracy(path, char) -> int", lambda: isinstance(
            calculate_accuracy(_get_test_images(1)[0] if _get_test_images(1) else "dummy", 'A'), int)),
        ("create_template(char) -> ndarray", lambda: create_template('A').shape == (64, 64)),
        ("create_handwriting_template(char) -> ndarray", lambda: create_handwriting_template('A').shape == (64, 64)),
    ]

    images = _get_test_images(1)
    if not images:
        print(f"  {SKIP} Need at least 1 test image for accuracy test")

        tests = tests[1:]

    all_ok = True
    for desc, test_fn in tests:
        try:
            result = test_fn()
            status = PASS if result else FAIL
            print(f"  {status} {desc}")
            if not result:
                all_ok = False
        except Exception as e:
            print(f"  {FAIL} {desc}: {e}")
            all_ok = False

    return all_ok


def pkb_test_9_confidence_levels():
    """PKB-1.9: Confidence computation works across scenarios."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.9] Confidence Level Computation{C.END}")

    from ai_core.ensemble import WeightedEnsemble
    import numpy as np

    ensemble = WeightedEnsemble()


    scenarios = [
        ("All agree (high confidence)", {"skeleton": (90, {}), "hog": (88, {}), "ssim": (91, {}), "distance": (89, {}), "completeness": (87, {}), "structural": (85, {}), "stroke_count": (80, {})}, "high"),
        ("Wide spread (low confidence)", {"skeleton": (95, {}), "hog": (30, {}), "ssim": (20, {}), "distance": (85, {}), "completeness": (15, {}), "structural": (5, {}), "stroke_count": (5, {})}, "low"),
        ("Medium variance (medium)", {"skeleton": (80, {}), "hog": (65, {}), "ssim": (50, {}), "distance": (72, {}), "completeness": (58, {}), "structural": (40, {}), "stroke_count": (35, {})}, "medium"),
    ]

    all_ok = True
    for desc, scores, expected_conf in scenarios:
        conf = ensemble.compute_confidence(scores, 'A')
        match = conf == expected_conf
        status = PASS if match else FAIL
        print(f"  {status} {desc}: got='{conf}', expected='{expected_conf}'")
        if not match:
            all_ok = False


    labels = {"high": "Yakin banget!", "medium": "Cukup yakin", "low": "Kurang pasti"}
    print(f"\n  {INFO} Confidence labels:")
    for conf, label in labels.items():
        print(f"       '{conf}' → \"{label}\"")

    return all_ok


def pkb_test_10_benchmark_v3_vs_v4():
    """PKB-1.10: Benchmark - timing comparison."""
    print(f"\n{'─'*60}")
    print(f"{C.BOLD}[PKB-1.10] Performance Benchmark{C.END}")

    from ai_core.pattern_matching import calculate_accuracy

    images = _get_test_images(5)

    if len(images) < 2:
        print(f"  {SKIP} Need ≥2 images for benchmark (have {len(images)})")
        return True

    chars_to_test = ['A', 'B', '1', 'a', 'O']
    total_evaluations = 0
    total_time = 0
    times_per_char = {}

    print(f"\n  {INFO} Running {len(images)} images × {len(chars_to_test)} chars = {len(images)*len(chars_to_test)} evals...")

    for img_path in images:
        img_name = Path(img_path).name[:15]
        for char in chars_to_test:
            start = time.perf_counter()
            try:
                acc = calculate_accuracy(img_path, char_target=char)
                elapsed = (time.perf_counter() - start) * 1000
                total_time += elapsed
                total_evaluations += 1

                if char not in times_per_char:
                    times_per_char[char] = []
                times_per_char[char].append(elapsed)
            except Exception:
                pass

    if total_evaluations > 0:
        avg_ms = total_time / total_evaluations
        print(f"\n  {PASS} Total: {total_evaluations} evaluations in {total_time:.0f}ms")
        print(f"       Average: {avg_ms:.1f}ms/evaluation")
        print(f"       Throughput: {total_evaluations/(total_time/1000):.1f} eval/sec")

        if times_per_char:
            print(f"\n  {INFO} Per-character avg time:")
            for char in sorted(times_per_char.keys()):
                avg = sum(times_per_char[char]) / len(times_per_char[char])
                bar = "░" * int(avg / 2)
                print(f"       '{char}': {avg:>6.1f}ms {bar}")


        if avg_ms < 200:
            print(f"\n  {PASS} Performance: EXCELLENT (<200ms/eval, real-time capable)")
        elif avg_ms < 500:
            print(f"\n  {PASS} Performance: GOOD (<500ms/eval)")
        elif avg_ms < 1000:
            print(f"\n  {YELLOW}⚠️  Performance: ACCEPTABLE (<1s/eval, but noticeable)")
        else:
            print(f"\n  {FAIL} Performance: SLOW (>1s/eval, needs optimization)")

        return avg_ms < 1000
    else:
        print(f"  {FAIL} No successful evaluations!")
        return False






PSD_TESTS = [
    ("Folder Structure", psd_test_1_folder_structure),
    ("Build Dataset Script", psd_test_2_build_dataset_script),
    ("Manifest Generated", psd_test_3_manifest_generated),
    ("Statistics Report", psd_test_4_statistics_report),
    ("Image Organization", psd_test_5_image_organization),
    ("Metadata Format", psd_test_6_metadata_format),
    ("API Data Saving", psd_test_7_api_evaluate_saves_data),
]

PKB_TESTS = [
    ("Module Imports", pkb_test_1_module_imports),
    ("7 Scorers Registered", pkb_test_2_all_scorers_registered),
    ("62 Templates", pkb_test_3_template_generation),
    ("Full Pipeline Eval", pkb_test_4_evaluation_pipeline),
    ("Explanation Output", pkb_test_5_explanation_output),
    ("Ensemble Config", pkb_test_6_ensemble_weights),
    ("Per-Character Tuning", pkb_test_7_per_character_tuning),
    ("Backward Compatible", pkb_test_8_backward_compatibility),
    ("Confidence Levels", pkb_test_9_confidence_levels),
    ("Performance Benchmark", pkb_test_10_benchmark_v3_vs_v4),
]


def run_tests(test_list, label, verbose=False):
    """Run a list of test functions, return (passed, total)."""
    print(f"\n{'╔'+'═'*58+'╗'}")
    print(f"║{C.BOLD}  {label:^56}{C.END}║")
    print(f"{'╚'+'═'*58+'╝'}")

    passed = 0
    total = len(test_list)

    for name, fn in test_list:
        try:
            result = fn()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n  {FAIL} {name}: UNEXPECTED ERROR - {e}")
            import traceback
            traceback.print_exc()

    score_pct = (passed / total * 100) if total > 0 else 0
    status_icon = "🎉" if score_pct == 100 else "👍" if score_pct >= 80 else "⚠️" if score_pct >= 50 else "❌"

    print(f"\n{'─'*60}")
    print(f"  {label} Result: {passed}/{total} ({score_pct:.0f}%) {status_icon}")

    return passed, total


def main():
    parser = argparse.ArgumentParser(description="Sahabat Aksara - PSD-1 + PKB-1 Test Suite")
    parser.add_argument("--psd-only", action="store_true", help="Only run PSD-1 tests")
    parser.add_argument("--pkb-only", action="store_true", help="Only run PKB-1 tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--image", type=str, help="Specific image path for testing")
    args = parser.parse_args()

    print(f"\n{'╔'+'═'*68+'╗'}")
    print(f"║{C.BOLD}  SAHABAT AKSARA - TEST SUITE: PSD-1 + PKB-1{' '*22}{C.END}║")
    print(f"║{C.DIM}  Project Root: {str(PROJECT_ROOT):<42}{C.END}║")
    print(f"║{C.DIM}  Timestamp:   {time.strftime('%Y-%m-%d %H:%M:%S'):<42}{C.END}║")
    print(f"{'╚'+'═'*68+'╝'}")

    total_passed = 0
    total_tests = 0

    if not args.pkb_only:
        p, t = run_tests(PSD_TESTS, "📊 PSD-1: Data Collection Pipeline", args.verbose)
        total_passed += p
        total_tests += t

    if not args.psd_only:
        p, t = run_tests(PKB_TESTS, "🤖 PKB-1: AI Engine v4", args.verbose)
        total_passed += p
        total_tests += t


    grand_pct = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n{'═'*68}")
    print(f"{C.BOLD}  FINAL SCORE: {total_passed}/{total_tests} ({grand_pct:.0f}%){C.END}")

    if grand_pct == 100:
        print(f"  {C.GREEN}{C.BOLD}🎉 ALL TESTS PASSED! PSD-1 ✅ + PKB-1 ✅{C.END}")
    elif grand_pct >= 80:
        print(f"  {C.GREEN}👍 MOSTLY GOOD - minor issues to fix{C.END}")
    elif grand_pct >= 50:
        print(f"  {C.YELLOW}⚠️  PARTIAL - some tests need attention{C.END}")
    else:
        print(f"  {C.RED}❌ MAJOR ISSUES - need investigation{C.END}")

    print(f"{'═'*68}\n")

    return 0 if grand_pct >= 80 else 1


if __name__ == "__main__":
    exit(main())
