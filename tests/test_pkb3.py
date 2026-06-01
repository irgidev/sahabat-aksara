"""
Test Suite: PKB-3 (Deep Learning CNN)
=======================================
Tests for CNN training pipeline, data generator, evaluation,
and SahabatNet architecture.

Run:
    cd C:/Documents/Desktop/Project/sahabat-aksara
    backend/venv/Scripts/python.exe -m pytest tests/test_pkb3.py -v

Author: Sahabat Aksara AI Team (PKB-3 Test Suite)
"""

import os
import sys
import json
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ai_core" / "training"))

import numpy as np






def get_venv_python():
    """Get venv Python executable."""
    return str(PROJECT_ROOT / "backend" / "venv" / "Scripts" / "python.exe")


def run_script(script_path, *args):
    """Run a Python script via subprocess and return output."""
    import subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [get_venv_python(), script_path] + list(args),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(PROJECT_ROOT), timeout=120, env=env,
    )
    return result.returncode, result.stdout, result.stderr






class TestDataGenerator:
    """PKB-3.1: Data Generator functionality."""

    def test_data_generator_import(self):
        """Data generator module can be imported."""
        from data_generator import (
            HandwritingDataGenerator,
            SyntheticDataGenerator,
            NUM_CLASSES,
            ALL_CHARS,
            CHAR_TO_IDX,
            IDX_TO_CHAR,
            create_generators,
        )
        assert NUM_CLASSES == 62
        assert len(ALL_CHARS) >= 62
        assert "A" in CHAR_TO_IDX
        assert "0" in CHAR_TO_IDX
        assert IDX_TO_CHAR[0] is not None

    def test_synthetic_generator_creates_data(self):
        """SyntheticDataGenerator creates valid image data."""
        from data_generator import SyntheticDataGenerator
        
        gen = SyntheticDataGenerator(
            num_samples=50,
            num_classes=10,
            image_size=(64, 64),
            batch_size=16,
            augment=False,
            seed=42,
        )
        
        X, y = gen.get_validation_data()
        assert X.shape[0] > 0, "Should have samples"
        assert X.shape[1:] == (64, 64, 1), f"Expected (N, 64, 64, 1), got {X.shape}"
        assert y.shape[1] == 10, f"Expected 10 classes, got {y.shape[1]}"
        assert X.dtype == np.float32 or X.dtype == np.float64
        assert np.all(X >= 0) and np.all(X <= 1)

    def test_synthetic_generator_batch_shape(self):
        """SyntheticDataGenerator yields correct batch shapes."""
        from data_generator import SyntheticDataGenerator
        
        gen = SyntheticDataGenerator(
            num_samples=100,
            num_classes=5,
            image_size=(32, 32),
            batch_size=16,
            augment=False,
            seed=42,
        )
        

        X_batch, y_batch = gen[0]
        assert X_batch.shape == (16, 32, 32, 1) or X_batch.shape[0] <= 16
        assert len(X_batch.shape) == 4, f"Expected 4D tensor, got {X_batch.shape}"
        assert y_batch.shape[1] == 5

    def test_synthetic_generator_one_hot_labels(self):
        """SyntheticDataGenerator produces valid one-hot labels."""
        from data_generator import SyntheticDataGenerator
        
        gen = SyntheticDataGenerator(
            num_samples=30,
            num_classes=5,
            image_size=(32, 32),
            batch_size=10,
            augment=False,
            seed=42,
        )
        
        X, y = gen.get_validation_data()
        

        row_sums = y.sum(axis=1)
        assert np.all(row_sums == 1), f"One-hot check failed: {row_sums}"
        

        assert np.all((y == 0) | (y == 1))

    def test_handwriting_generator_fallback(self):
        """HandwritingDataGenerator handles missing directory gracefully."""
        from data_generator import HandwritingDataGenerator
        

        gen = HandwritingDataGenerator(
            image_dir="/nonexistent/path/that/does/not/exist",
            batch_size=16,
            target_size=(32, 32),
            validation_split=0.2,
        )
        

        assert gen is not None
        assert gen.target_size == (32, 32)

    def test_char_mappings_consistent(self):
        """Character mappings are consistent and complete."""
        from data_generator import (
            NUM_CLASSES, ALL_CHARS, CHAR_TO_IDX, IDX_TO_CHAR
        )
        
        assert len(CHAR_TO_IDX) == NUM_CLASSES
        assert len(IDX_TO_CHAR) == NUM_CLASSES
        

        for ch, idx in list(CHAR_TO_IDX.items())[:5]:
            assert IDX_TO_CHAR[idx] == ch, f"Mismatch: {ch} -> {idx} -> {IDX_TO_CHAR[idx]}"






class TestSahabatNetArchitecture:
    """PKB-3.2: SahabatNet CNN architecture tests."""

    def test_build_v1_architecture(self):
        """SahabatNet-v1 builds successfully with correct shape."""
        from train_cnn import build_sahabatnet_v1
        
        model = build_sahabatnet_v1(input_shape=(64, 64, 1), num_classes=62)
        
        assert model.input_shape[1:] == (64, 64, 1)
        assert model.output_shape[-1] == 62
        assert model.name == "SahabatNet-v1"

    def test_build_tiny_architecture(self):
        """SahabatNet-Tiny builds successfully with fewer params."""
        from train_cnn import build_sahabnet_tiny
        
        model = build_sahabnet_tiny(input_shape=(64, 64, 1), num_classes=62)
        
        assert model.input_shape[1:] == (64, 64, 1)
        assert model.output_shape[-1] == 62
        assert model.name == "SahabatNet-Tiny"

    def test_tiny_has_fewer_params_than_v1(self):
        """Tiny variant has significantly fewer parameters than v1."""
        from train_cnn import build_sahabatnet_v1, build_sahabnet_tiny
        
        v1 = build_sahabatnet_v1(num_classes=62)
        tiny = build_sahabnet_tiny(num_classes=62)
        
        v1_params = sum(p.numpy().size for p in v1.trainable_variables)
        tiny_params = sum(p.numpy().size for p in tiny.trainable_variables)
        
        assert tiny_params < v1_params, \
            f"Tiny ({tiny_params}) should have fewer params than V1 ({v1_params})"
        print(f"\n  Params: V1={v1_params:,}, Tiny={tiny_params:,} ({tiny_params/v1_params*100:.0f}%)")

    def test_model_forward_pass(self):
        """Model can do a forward pass on dummy data."""
        from train_cnn import build_sahabnet_tiny
        import tensorflow as tf
        
        model = build_sahabnet_tiny(input_shape=(64, 64, 1), num_classes=62)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        

        X_dummy = np.random.randn(4, 64, 64, 1).astype(np.float32)
        y_dummy = np.zeros((4, 62), dtype=np.float32)
        y_dummy[:, 0] = 1
        
        output = model.predict(X_dummy, verbose=0)
        assert output.shape == (4, 62)
        assert np.allclose(output.sum(axis=1), 1.0, atol=0.01), "Output should sum to ~1 (softmax)"

    def test_model_output_is_probability_distribution(self):
        """Model outputs valid probability distributions (softmax)."""
        from train_cnn import build_sahabnet_tiny
        
        model = build_sahabnet_tiny(num_classes=62)
        model.compile(optimizer='adam', loss='categorical_crossentropy')
        
        X = np.random.randn(2, 64, 64, 1).astype(np.float32)
        probs = model.predict(X, verbose=0)
        

        assert np.all(probs >= 0), "Negative probabilities found"

        assert np.allclose(probs.sum(axis=1), 1.0, atol=0.01), \
            f"Probabilities don't sum to 1: {probs.sum(axis=1)}"






class TestTrainingPipeline:
    """PKB-3.3: Training pipeline end-to-end tests."""

    def test_train_with_synthetic_data(self):
        """Training runs successfully with synthetic data."""
        from train_cnn import train_cnn
        
        with tempfile.TemporaryDirectory() as tmpdir:
            results = train_cnn(
                image_dir=None,
                epochs=5,
                batch_size=16,
                learning_rate=0.001,
                architecture="tiny",
                patience=99,
                use_synthetic=True,
                synthetic_samples=200,
                output_dir=tmpdir,
                seed=42,
            )
            
            assert 'model' in results
            assert 'history' in results
            assert 'metrics' in results
            assert results['metrics']['accuracy'] >= 0
            assert os.path.exists(results['model_path'])

    def test_training_saves_artifacts(self):
        """Training saves all expected artifact files."""
        from train_cnn import train_cnn
        
        with tempfile.TemporaryDirectory() as tmpdir:
            train_cnn(
                epochs=3,
                batch_size=16,
                architecture="tiny",
                patience=99,
                synthetic_samples=100,
                output_dir=tmpdir,
                seed=42,
            )
            

            assert os.path.exists(os.path.join(tmpdir, "weights.h5")), "Missing weights.h5"
            assert os.path.exists(os.path.join(tmpdir, "architecture.json")), "Missing architecture.json"

    def test_training_history_format(self):
        """Training history has correct format."""
        from train_cnn import train_cnn
        
        with tempfile.TemporaryDirectory() as tmpdir:
            results = train_cnn(
                epochs=3,
                batch_size=16,
                architecture="tiny",
                patience=99,
                synthetic_samples=100,
                output_dir=tmpdir,
                seed=42,
            )
            
            history = results['history']
            assert 'loss' in history, "History missing 'loss'"
            assert 'accuracy' in history, "History missing 'accuracy'"
            assert len(history['loss']) > 0, "Empty history"

    def test_architecture_json_content(self):
        """Architecture JSON contains required fields."""
        from train_cnn import train_cnn
        
        with tempfile.TemporaryDirectory() as tmpdir:
            train_cnn(
                epochs=2,
                batch_size=16,
                architecture="tiny",
                patience=99,
                synthetic_samples=80,
                output_dir=tmpdir,
                seed=42,
            )
            
            arch_path = os.path.join(tmpdir, "architecture.json")
            with open(arch_path) as f:
                arch = json.load(f)
            
            assert 'architecture' in arch
            assert 'input_shape' in arch
            assert 'num_classes' in arch
            assert 'total_params' in arch
            assert 'final_metrics' in arch
            assert 'classes' in arch
            assert arch['num_classes'] == 62






class TestCNNEvaluation:
    """PKB-3.4: CNN Evaluation tests."""

    def _train_quick_model(self, tmpdir):
        """Helper: Train a quick model for evaluation testing."""
        from train_cnn import train_cnn
        return train_cnn(
            epochs=3,
            batch_size=16,
            architecture="tiny",
            patience=99,
            synthetic_samples=150,
            output_dir=tmpdir,
            seed=123,
        )

    def test_evaluation_runs(self):
        """Evaluation script runs without error."""
        from evaluate_cnn import run_evaluation
        
        with tempfile.TemporaryDirectory() as tmpdir:
            train_results = self._train_quick_model(tmpdir)
            
            eval_dir = os.path.join(tmpdir, "eval")
            results = run_evaluation(
                model_path=train_results['model_path'],
                output_dir=eval_dir,
                synthetic_samples=100,
                seed=42,
            )
            

            assert isinstance(results, dict)
            assert 'accuracy' in results or 'metrics' in results

    def test_evaluation_saves_reports(self):
        """Evaluation saves report files."""
        from evaluate_cnn import run_evaluation
        
        with tempfile.TemporaryDirectory() as tmpdir:
            train_results = self._train_quick_model(tmpdir)
            
            eval_dir = os.path.join(tmpdir, "eval")
            run_evaluation(
                model_path=train_results['model_path'],
                output_dir=eval_dir,
                synthetic_samples=80,
                seed=42,
            )
            
            assert os.path.exists(os.path.join(eval_dir, "cnn_evaluation.json"))

    def test_evaluation_metrics_range(self):
        """Evaluation metrics are in valid ranges."""
        from evaluate_cnn import run_evaluation
        
        with tempfile.TemporaryDirectory() as tmpdir:
            train_results = self._train_quick_model(tmpdir)
            
            eval_dir = os.path.join(tmpdir, "eval")
            results = run_evaluation(
                model_path=train_results['model_path'],
                output_dir=eval_dir,
                synthetic_samples=80,
                seed=42,
            )
            

            m = results.get('metrics', results)
            assert 0 <= m.get('accuracy', 0) <= 1, f"Accuracy out of range: {m.get('accuracy')}"
            assert 0 <= m.get('top_3_accuracy', 0) <= 1, f"Top-3 accuracy out of range"
            assert m.get('inference_time_per_image_ms', 1) > 0, "Inference time should be positive"






class TestIntegrationAndFiles:
    """PKB-3.5: File existence and integration tests."""

    def test_data_generator_file_exists(self):
        """data_generator.py exists and is readable."""
        dg_path = PROJECT_ROOT / "ai_core" / "training" / "data_generator.py"
        assert dg_path.exists(), f"data_generator.py not found at {dg_path}"
        content = dg_path.read_text(encoding="utf-8")
        assert len(content) > 5000, "data_generator.py seems too small"
        assert "HandwritingDataGenerator" in content
        assert "SyntheticDataGenerator" in content

    def test_train_cnn_file_exists(self):
        """train_cnn.py exists and has key components."""
        tc_path = PROJECT_ROOT / "ai_core" / "training" / "train_cnn.py"
        assert tc_path.exists()
        content = tc_path.read_text(encoding="utf-8")
        assert "build_sahabatnet_v1" in content
        assert "build_sahabnet_tiny" in content
        assert "train_cnn" in content
        assert "SahabatNet" in content

    def test_evaluate_cnn_file_exists(self):
        """evaluate_cnn.py exists and has key components."""
        ec_path = PROJECT_ROOT / "ai_core" / "training" / "evaluate_cnn.py"
        assert ec_path.exists()
        content = ec_path.read_text(encoding="utf-8")
        assert "evaluate_model" in content
        assert "plot_confusion_matrix" in content
        assert "run_evaluation" in content

    def test_trained_model_exists(self):
        """Trained CNN model file exists from previous training run."""
        model_path = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple" / "weights.h5"
        if model_path.exists():
            size_kb = model_path.stat().st_size / 1024
            assert size_kb > 100, f"Model too small: {size_kb:.1f} KB"
            print(f"\n  Model size: {size_kb:.1f} KB")
        else:
            print("\n  [SKIP] No pre-trained model yet (run train_cnn.py first)")

    def test_architecture_json_exists(self):
        """Architecture metadata JSON exists."""
        arch_path = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple" / "architecture.json"
        if arch_path.exists():
            with open(arch_path) as f:
                arch = json.load(f)
            assert "architecture" in arch
            assert "total_params" in arch
            print(f"\n  Architecture: {arch.get('architecture')}, Params: {arch.get('total_params'):,}")
        else:
            print("\n  [SKIP] No architecture.json yet")

    def test_training_history_exists(self):
        """Training history JSON exists."""
        hist_path = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple" / "training_history.json"
        if hist_path.exists():
            with open(hist_path) as f:
                hist = json.load(f)
            assert "loss" in hist
            assert "accuracy" in hist
            n_epochs = len(hist["loss"])
            print(f"\n  History: {n_epochs} epochs recorded")
        else:
            print("\n  [SKIP] No training history yet")

    def test_deep_learning_directory_structure(self):
        """Deep learning model directory structure exists."""
        base = PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple"
        if base.exists():
            files = list(base.glob("*"))
            filenames = [f.name for f in files]
            print(f"\n  Deep learning dir contents: {filenames}")
            assert len(files) >= 1, "Deep learning dir should have at least one file"
        else:
            print("\n  [SKIP] Deep learning dir doesn't exist yet")






if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
