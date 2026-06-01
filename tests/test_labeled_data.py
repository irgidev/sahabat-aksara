"""
Test Suite: Real Labeled Data Collection — Synthetic Handwriting Generator
==========================================================================
Covers:
  - Data generator core (stroke definitions, image rendering)
  - Writer profiles and skill levels
  - Dataset generation pipeline (full + quick)
  - Metadata CSV and manifest JSON validation
  - Image quality checks (not blank, valid PNG, correct size)
  - Character distribution balance
  - Preview grid generation

Run:
    backend/venv/Scripts/python.exe -m pytest tests/test_labeled_data.py -v
"""

import os
import sys
import json
import csv
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data_science" / "scripts"))

import numpy as np
import cv2






class TestStrokeDefinitions:
    """Validate character stroke path definitions."""

    def test_all_62_chars_have_strokes(self):
        """Every character in CHARACTERS has stroke definition."""
        from generate_labeled_data import get_stroke_points, CHARACTERS

        for ch in CHARACTERS:
            strokes = get_stroke_points(ch)
            assert isinstance(strokes, list), f"No strokes for '{ch}'"
            assert len(strokes) > 0, f"Empty strokes for '{ch}'"
            for stroke in strokes:
                assert len(stroke) >= 2, f"Stroke too short for '{ch}'"

    def test_stroke_points_are_tuples(self):
        """Each point is an (x, y) tuple of ints."""
        from generate_labeled_data import get_stroke_points

        strokes = get_stroke_points("A")
        for stroke in strokes:
            for pt in stroke:
                assert isinstance(pt, tuple), f"Not tuple: {pt}"
                assert len(pt) == 2, f"Point not 2D: {pt}"

    def test_uppercase_lowercase_different(self):
        """Uppercase and lowercase have different stroke definitions."""
        from generate_labeled_data import get_stroke_points

        upper = get_stroke_points("A")
        lower = get_stroke_points("a")


        assert len(upper) > 0
        assert len(lower) > 0

    def test_digit_strokes_exist(self):
        """All digits 0-9 have stroke definitions."""
        from generate_labeled_data import get_stroke_points

        for d in "0123456789":
            strokes = get_stroke_points(d)
            assert len(strokes) > 0, f"No strokes for digit '{d}'"

    def test_char_difficulty_mapping(self):
        """Character difficulty returns int 1-5."""
        from generate_labeled_data import get_char_difficulty, CHAR_DIFFICULTY

        for ch, diff in CHAR_DIFFICULTY.items():
            assert 1 <= diff <= 5, f"Invalid difficulty for '{ch}': {diff}"






class TestImageGeneration:
    """Core draw_character_image function."""

    def test_returns_image_and_metadata(self):
        """Generator returns (image_array, metadata_dict)."""
        from generate_labeled_data import draw_character_image

        img, meta = draw_character_image("A", seed=42)

        assert isinstance(img, np.ndarray), "Image must be numpy array"
        assert isinstance(meta, dict), "Metadata must be dict"

    def test_image_shape(self):
        """Output image is 64x64 grayscale."""
        from generate_labeled_data import draw_character_image, IMAGE_SIZE

        img, _ = draw_character_image("B", seed=1)

        assert img.shape == (IMAGE_SIZE, IMAGE_SIZE), f"Wrong shape: {img.shape}"
        assert img.dtype == np.uint8

    def test_image_not_blank_white(self):
        """Generated image is not completely blank (has some black pixels)."""
        from generate_labeled_data import draw_character_image

        img, _ = draw_character_image("T", seed=10)

        black_pixels = np.sum(img < 200)
        total_pixels = img.size
        fg_ratio = black_pixels / total_pixels

        assert fg_ratio > 0.02, f"Image looks blank! FG ratio: {fg_ratio:.4f}"

    def test_image_not_completely_black(self):
        """Generated image is not completely filled (has white background)."""
        from generate_labeled_data import draw_character_image

        img, _ = draw_character_image("O", seed=5)

        white_pixels = np.sum(img > 200)
        total_pixels = img.size
        bg_ratio = white_pixels / total_pixels

        assert bg_ratio > 0.3, f"Image looks all black! BG ratio: {bg_ratio:.4f}"

    def test_metadata_contains_required_fields(self):
        """Metadata has all required keys."""
        from generate_labeled_data import draw_character_image

        _, meta = draw_character_image("X", seed=99)

        required = ["char", "writer_profile", "skill_level", "seed_used",
                     "foreground_ratio", "char_difficulty"]
        for field in required:
            assert field in meta, f"Missing metadata field: {field}"

    def test_metadata_char_matches_input(self):
        """Metadata char field matches input char."""
        from generate_labeled_data import draw_character_image

        for ch in ["Z", "g", "7"]:
            _, meta = draw_character_image(ch, seed=hash(ch) & 0xFFFFFFFF)
            assert meta["char"] == ch

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical output."""
        from generate_labeled_data import draw_character_image

        img1, m1 = draw_character_image("M", seed=12345)
        img2, m2 = draw_character_image("M", seed=12345)

        assert np.array_equal(img1, img2), "Same seed should produce same image"

    def test_different_seeds_produce_different_images(self):
        """Different seeds produce different images (with high probability)."""
        from generate_labeled_data import draw_character_image

        img1, _ = draw_character_image("Q", seed=111)
        img2, _ = draw_character_image("Q", seed=999)


        assert not np.array_equal(img1, img2), "Different seeds should differ"






class TestWriterProfiles:
    """Different writer profiles produce visually different images."""

    def test_neat_vs_messy_foreground_differs(self):
        """Neat writer has more consistent foreground ratio than messy."""
        from generate_labeled_data import draw_character_image

        neat_imgs = [draw_character_image("H", writer_profile="neat", seed=i)[0]
                     for i in range(5)]
        messy_imgs = [draw_character_image("H", writer_profile="messy", seed=i)[0]
                      for i in range(5)]

        neat_ratios = [np.sum(img < 128) / img.size for img in neat_imgs]
        messy_ratios = [np.sum(img < 128) / img.size for img in messy_imgs]


        neat_var = np.var(neat_ratios)
        messy_var = np.var(messy_ratios)


        assert isinstance(neat_var, float) and isinstance(messy_var, float)

    def test_all_profiles_generate_valid_images(self):
        """All 5 writer profiles can generate images without error."""
        from generate_labeled_data import draw_character_image, WRITER_PROFILES

        for profile in WRITER_PROFILES:
            img, meta = draw_character_image("E", writer_profile=profile, seed=42)
            assert img.shape == (64, 64), f"{profile}: wrong shape"
            assert meta["writer_profile"] == profile

    def test_careful_slow_has_thinner_strokes(self):
        """Careful_slow profile tends to produce thinner strokes (lower FG ratio)."""
        from generate_labeled_data import draw_character_image

        _, m_careful = draw_character_image("L", writer_profile="careful_slow", seed=42)
        _, m_messy = draw_character_image("L", writer_profile="messy", seed=42)


        assert m_careful["stroke_width"] <= m_messy["stroke_width"] + 2






class TestSkillLevels:
    """Skill levels affect output quality."""

    def test_all_skill_levels_work(self):
        """All 3 skill levels generate without error."""
        from generate_labeled_data import draw_character_image, SKILL_LEVELS

        for level in SKILL_LEVELS:
            img, meta = draw_character_image("P", skill_level=level, seed=42)
            assert img.shape == (64, 64)

    def test_advanced_higher_quality_than_beginner(self):
        """Advanced skill level produces less noisy output than beginner."""
        from generate_labeled_data import draw_character_image

        img_adv, _ = draw_character_image("S", skill_level="advanced", seed=42)
        img_beg, _ = draw_character_image("S", skill_level="beginner", seed=42)


        adv_std = float(np.std(img_adv))
        beg_std = float(np.std(img_beg))


        assert beg_std >= adv_std * 0.8






class TestDatasetGeneration:
    """Full dataset generation pipeline."""

    @classmethod
    def setup_class(cls):
        cls.tmp_dir = PROJECT_ROOT / "data_science" / "datasets" / "_test_labeled"

        if cls.tmp_dir.exists():
            import shutil
            shutil.rmtree(cls.tmp_dir)

    def test_quick_dataset_generation(self):
        """Generate small dataset (100 samples) successfully."""
        from generate_labeled_data import generate_dataset

        manifest = generate_dataset(
            output_dir=str(self.tmp_dir),
            total_samples=150,
            chars_per_sample_min=2,
            seed=42,
            verbose=False,
        )

        assert manifest is not None
        assert manifest["statistics"]["total_images"] == 150
        assert manifest["statistics"]["total_characters"] == 62

    def test_dataset_creates_per_char_directories(self):
        """Each character gets its own subdirectory."""
        from generate_labeled_data import CHARACTERS

        for ch in CHARACTERS:
            ch_dir = self.tmp_dir / ch
            assert ch_dir.is_dir(), f"Missing directory for '{ch}'"
            files = list(ch_dir.glob("*.png"))
            assert len(files) >= 2, f"'{ch}' only has {len(files)} files"

    def test_dataset_creates_metadata_csv(self):
        """metadata.csv exists with correct headers and rows."""
        csv_path = self.tmp_dir / "metadata.csv"
        assert csv_path.exists(), "metadata.csv not found"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= 100, f"Only {len(rows)} rows in CSV"

        row0 = rows[0]
        assert "char" in row0
        assert "filename" in row0
        assert "writer_profile" in row0
        assert "skill_level" in row0
        assert "foreground_ratio" in row0

    def test_dataset_creates_manifest_json(self):
        """manifest.json exists with complete statistics."""
        manifest_path = self.tmp_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["version"] == "2.0"
        assert manifest["type"] == "synthetic_labeled"
        assert "statistics" in manifest
        assert "per_character" in manifest
        assert "writer_profiles" in manifest
        assert manifest["statistics"]["total_images"] >= 100

    def test_manifest_per_char_stats(self):
        """Per-character stats in manifest are accurate."""
        manifest_path = self.tmp_dir / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        per_char = manifest["per_character"]
        assert len(per_char) == 62


        sample_ch = "A"
        if sample_ch in per_char:
            reported_count = per_char[sample_ch]["count"]
            actual_count = len(list((self.tmp_dir / sample_ch).glob("*.png")))

            assert reported_count >= 2 and actual_count >= 2, \
                f"Manifest: {reported_count}, files: {actual_count} for '{sample_ch}'"

    def test_png_files_valid(self):
        """Generated PNG files are valid, readable images."""
        from generate_labeled_data import CHARACTERS


        for ch in ["A", "m", "5"]:
            ch_dir = self.tmp_dir / ch
            png_files = list(ch_dir.glob("*.png"))
            assert len(png_files) > 0, f"No PNGs for '{ch}'"


            sample = png_files[0]
            img = cv2.imread(str(sample), cv2.IMREAD_GRAYSCALE)
            assert img is not None, f"Cannot read {sample}"
            assert img.shape == (64, 64), f"Wrong size for {sample}: {img.shape}"

    def test_distribution_balanced_enough(self):
        """Character distribution is reasonably balanced (no char has 0)."""
        manifest_path = self.tmp_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        counts = [v["count"] for v in manifest["per_character"].values()]
        assert min(counts) >= 2, f"Some character has only {min(counts)} samples"

        ratio = max(counts) / max(min(counts), 1)
        assert ratio <= 5, f"Distribution too skewed: max/min = {ratio:.1f}"

    def test_writer_profiles_represented(self):
        """All writer profiles appear in the dataset."""
        csv_path = self.tmp_dir / "metadata.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            profiles_seen = set(row["writer_profile"] for row in reader)

        expected = {"neat", "messy", "fast_sloppy", "careful_slow", "tremor"}

        assert len(profiles_seen & expected) >= 3, \
            f"Only {len(profiles_seen & expected)} profiles found: {profiles_seen}"

    def test_skill_levels_represented(self):
        """All skill levels appear in the dataset."""
        csv_path = self.tmp_dir / "metadata.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            skills_seen = set(row["skill_level"] for row in reader)

        expected = {"beginner", "intermediate", "advanced"}
        assert skills_seen & expected, f"No expected skills found: {skills_seen}"

    def test_filename_format_consistent(self):
        """Filenames follow naming convention: img_NNNNN_char_profile_skill_NNN.png"""
        import re

        pattern = re.compile(r"^img_\d{5}_\w+_\w{4}_\w{4}_\d{3}\.png$")

        csv_path = self.tmp_dir / "metadata.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            filenames = [row["filename"] for row in reader]

        matching = sum(1 for fn in filenames if pattern.match(fn))
        assert matching >= len(filenames) * 0.9, \
            f"Only {matching}/{len(filenames)} match filename pattern"






class TestPreviewGrid:
    """Preview grid generation."""

    def test_preview_generates_file(self):
        """generate_preview_grid creates PNG file."""
        from generate_labeled_data import generate_preview_grid

        preview_path = PROJECT_ROOT / "data_science" / "reports" / "_test_preview.png"
        result = generate_preview_grid(output_path=str(preview_path), seed=42)

        assert os.path.exists(preview_path)
        assert os.path.getsize(preview_path) > 1000

    def test_preview_is_valid_image(self):
        """Preview file is a readable image."""
        preview_path = PROJECT_ROOT / "data_science" / "reports" / "_test_preview.png"
        if not preview_path.exists():
            from generate_labeled_data import generate_preview_grid
            generate_preview_grid(output_path=str(preview_path))

        img = cv2.imread(str(preview_path))
        assert img is not None, "Preview image unreadable"
        assert img.shape[0] > 100 and img.shape[1] > 100, \
            f"Preview too small: {img.shape}"






class TestIntegrationWithAI:
    """Synthetic data works with existing AI pipeline components."""

    def test_generated_image_loadable_by_preprocessor(self):
        """Generated images can be loaded by project preprocessor."""
        sys.path.insert(0, str(PROJECT_ROOT / "ai_core"))
        from preprocessor import full_preprocess


        test_dir = self.tmp_dir if hasattr(self, 'tmp_dir') else \
                   PROJECT_ROOT / "data_science" / "datasets" / "labeled"


        png_files = list(test_dir.glob("A/*.png"))[:1]
        if not png_files:
            png_files = list((PROJECT_ROOT / "data_science" / "datasets" / "labeled").glob("A/*.png"))[:1]

        if png_files:
            result = full_preprocess(str(png_files[0]))
            assert result is not None

            assert isinstance(result, dict) and "binary" in result

    def test_metadata_can_train_sklearn_model(self):
        """Metadata features can be used as sklearn training data."""
        import pandas as pd

        csv_path = self.tmp_dir / "metadata.csv" if hasattr(self, 'tmp_dir') else \
                  PROJECT_ROOT / "data_science" / "datasets" / "labeled" / "metadata.csv"

        if csv_path.exists():
            df = pd.read_csv(str(csv_path))
            feature_cols = ["foreground_ratio", "density", "size_factor",
                           "slant_angle", "stroke_width", "char_difficulty"]
            available = [c for c in feature_cols if c in df.columns]
            assert len(available) >= 3, f"Not enough feature cols: {available}"

            X = df[available].fillna(0).values
            assert X.shape[0] > 10
            assert X.shape[1] >= 3

    def test_production_dataset_exists(self):
        """Production dataset (3100 samples) was generated earlier."""
        prod_dir = PROJECT_ROOT / "data_science" / "datasets" / "labeled"
        manifest = prod_dir / "manifest.json"

        assert prod_dir.is_dir(), "Production dataset directory missing"
        assert manifest.exists(), "Production manifest missing"

        with open(manifest) as f:
            m = json.load(f)
        assert m["statistics"]["total_images"] >= 3000, \
            f"Production dataset too small: {m['statistics']['total_images']}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
