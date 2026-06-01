"""
CNN Training Pipeline for Sahabat Aksara
==========================================
Train a lightweight Convolutional Neural Network for handwriting character recognition.

Architecture: "SahabatNet-v1"
  Input(64,64,1) → Conv2D(32)→BN→ReLU→MaxPool→Dropout
              → Conv2D(64)→BN→ReLU→MaxPool→Dropout
              → Conv2D(128)→BN→ReLU→MaxPool→Dropout
              → Flatten → Dense(256)→BN→ReLU→Dropout → Dense(62) → Softmax

  Total params: ~1.29M (lightweight for CPU inference)
  Target inference: <100ms/image on CPU

Features:
  - Custom SahabatNet architecture with BatchNorm + Dropout
  - Training callbacks: EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, CSVLogger
  - Automatic fallback to synthetic data if real labels insufficient
  - Training history logging (JSON + plot)
  - Model export to .h5 (Keras) format

Usage:
    python ai_core/training/train_cnn.py
    python ai_core/training/train_cnn.py --epochs 100 --batch-size 32 --lr 0.001

Author: Sahabat Aksara AI Team (PKB-3 Phase 1)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers, callbacks, regularizers


from data_generator import (
    create_generators,
    SyntheticDataGenerator,
    NUM_CLASSES,
    ALL_CHARS,
    CHAR_TO_IDX,
    IDX_TO_CHAR,
)


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"






def build_sahabatnet_v1(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    num_classes: int = NUM_CLASSES,
    dropout_rate: float = 0.25,
    l2_reg: float = 0.001,
) -> keras.Model:
    """
    Build SahabatNet-v1 — Lightweight CNN for handwriting recognition.
    
    Architecture:
        Input(64,64,1)
        → Conv2D(32, 3×3, padding='same') → BN → ReLU → MaxPool(2×2) → Dropout
        → Conv2D(64, 3×3, padding='same') → BN → ReLU → MaxPool(2×2) → Dropout
        → Conv2D(128, 3×3, padding='same') → BN → ReLU → MaxPool(2×2) → Dropout
        → Flatten
        → Dense(256) → BN → ReLU → Dropout(0.5)
        → Dense(num_classes) → Softmax
    
    Args:
        input_shape: Input image dimensions (H, W, C)
        num_classes: Number of output classes (default: 62)
        dropout_rate: Dropout rate for conv layers
        l2_reg: L2 regularization strength
    
    Returns:
        Compiled Keras model
    """
    reg = regularizers.l2(l2_reg)
    
    model = models.Sequential([

        layers.Conv2D(32, (3, 3), padding='same', kernel_regularizer=reg,
                      input_shape=input_shape, name='conv1'),
        layers.BatchNormalization(name='bn1'),
        layers.Activation('relu', name='relu1'),
        layers.MaxPooling2D((2, 2), name='pool1'),
        layers.Dropout(dropout_rate, name='drop1'),
        

        layers.Conv2D(64, (3, 3), padding='same', kernel_regularizer=reg,
                      name='conv2'),
        layers.BatchNormalization(name='bn2'),
        layers.Activation('relu', name='relu2'),
        layers.MaxPooling2D((2, 2), name='pool2'),
        layers.Dropout(dropout_rate, name='drop2'),
        

        layers.Conv2D(128, (3, 3), padding='same', kernel_regularizer=reg,
                      name='conv3'),
        layers.BatchNormalization(name='bn3'),
        layers.Activation('relu', name='relu3'),
        layers.MaxPooling2D((2, 2), name='pool3'),
        layers.Dropout(dropout_rate, name='drop3'),
        

        layers.Flatten(name='flatten'),
        layers.Dense(256, kernel_regularizer=reg, name='dense1'),
        layers.BatchNormalization(name='bn_dense'),
        layers.Activation('relu', name='relu_dense'),
        layers.Dropout(0.5, name='drop_dense'),
        

        layers.Dense(num_classes, activation='softmax', name='output'),
    ], name='SahabatNet-v1')
    
    return model


def build_sahabnet_tiny(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    num_classes: int = NUM_CLASSES,
) -> keras.Model:
    """
    Build SahabatNet-Tiny — Ultra-lightweight variant for very small datasets.
    
    Only 2 conv blocks, ~150K params.
    Good for <500 samples or fast prototyping.
    """
    model = models.Sequential([
        layers.Conv2D(16, (3, 3), padding='same', activation='relu',
                      input_shape=input_shape, name='conv1'),
        layers.MaxPooling2D((2, 2), name='pool1'),
        layers.Dropout(0.25, name='drop1'),
        
        layers.Conv2D(32, (3, 3), padding='same', activation='relu',
                      name='conv2'),
        layers.MaxPooling2D((2, 2), name='pool2'),
        layers.Dropout(0.25, name='drop2'),
        
        layers.Flatten(name='flatten'),
        layers.Dense(64, activation='relu', name='dense1'),
        layers.Dropout(0.5, name='drop_dense'),
        
        layers.Dense(num_classes, activation='softmax', name='output'),
    ], name='SahabatNet-Tiny')
    
    return model






def get_callbacks(
    checkpoint_dir: str,
    patience: int = 7,
    min_lr: float = 1e-6,
) -> list:
    """Create standard training callbacks."""
    return [
        callbacks.EarlyStopping(
            monitor='val_loss',
            patience=patience,
            restore_best_weights=True,
            verbose=1,
            mode='min',
        ),
        callbacks.ModelCheckpoint(
            filepath=os.path.join(checkpoint_dir, 'best_model.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            save_weights_only=False,
            verbose=1,
            mode='max',
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=min_lr,
            verbose=1,
        ),
        callbacks.CSVLogger(
            os.path.join(checkpoint_dir, 'training_log.csv'),
            separator=',',
            append=False,
        ),
    ]






def train_cnn(
    image_dir: Optional[str] = None,
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    architecture: str = "v1",
    patience: int = 7,
    use_synthetic: bool = True,
    synthetic_samples: int = 500,
    output_dir: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Full CNN training pipeline.
    
    Args:
        image_dir: Directory with training images (None = synthetic only)
        epochs: Maximum training epochs
        batch_size: Samples per batch
        learning_rate: Initial learning rate
        architecture: "v1" (full) or "tiny" (lightweight)
        patience: Early stopping patience
        use_synthetic: Fall back to synthetic data if real data insufficient
        synthetic_samples: Number of synthetic samples for fallback
        output_dir: Where to save model and logs
        seed: Random seed
    
    Returns:
        Dictionary with training results:
            - model: trained Keras model
            - history: training history dict
            - metrics: final accuracy/loss on validation set
            - config: training configuration used
    """

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 65)
    print("  SAHABATNET CNN TRAINING PIPELINE")
    print("=" * 65)
    print(f"  Architecture : {architecture}")
    print(f"  Epochs       : {epochs}")
    print(f"  Batch size   : {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Output dir   : {output_dir}")
    print()
    

    np.random.seed(seed)
    tf.random.set_seed(seed)
    

    target_size = (64, 64)
    input_shape = (*target_size, 1)
    
    if architecture == "tiny":
        model = build_sahabnet_tiny(input_shape=input_shape)
    else:
        model = build_sahabatnet_v1(input_shape=input_shape)
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=learning_rate),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')],
    )
    

    model.summary(print_fn=lambda x: print(f"  {x}"))
    
    total_params = sum(p.numpy().size for p in model.trainable_variables)
    print(f"\n  Total trainable parameters: {total_params:,}\n")
    

    if image_dir is not None and Path(image_dir).exists():
        train_gen, val_data = create_generators(
            image_dir=image_dir,
            batch_size=batch_size,
            target_size=target_size,
            synthetic_samples=synthetic_samples,
            seed=seed,
        )
    else:

        print("  [Data] Using SYNTHETIC dataset")
        train_gen = SyntheticDataGenerator(
            num_samples=synthetic_samples,
            image_size=target_size,
            batch_size=batch_size,
            augment=True,
            seed=seed,
        )
        val_data = train_gen.get_validation_data()
    

    cb_list = get_callbacks(output_dir, patience=patience)
    
    start_time = time.time()
    
    if isinstance(val_data, tuple):
        X_val, y_val = val_data
        history = model.fit(
            train_gen,
            epochs=epochs,
            validation_data=(X_val, y_val),
            callbacks=cb_list,
            verbose=1,
        )
    else:
        history = model.fit(
            train_gen,
            epochs=epochs,
            validation_data=val_data,
            callbacks=cb_list,
            verbose=1,
        )
    
    training_time = time.time() - start_time
    print(f"\n  Training completed in {training_time:.1f}s ({training_time/60:.1f}min)")
    

    if isinstance(val_data, tuple):
        X_val, y_val = val_data
        eval_results = model.evaluate(X_val, y_val, verbose=0)
    else:
        eval_results = model.evaluate(val_data, verbose=0)
    
    metric_names = ['loss', 'accuracy', 'top_3_accuracy']
    final_metrics = dict(zip(metric_names, [float(r) for r in eval_results]))
    
    print("\n  Final Validation Metrics:")
    for name, val in final_metrics.items():
        print(f"    {name}: {val:.4f}")
    


    model_path = os.path.join(output_dir, 'weights.h5')
    model.save(model_path)
    print(f"\n  Model saved to: {model_path}")
    print(f"  Model size: {os.path.getsize(model_path) / 1024:.1f} KB")
    

    hist_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    history_path = os.path.join(output_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(hist_dict, f, indent=2)
    print(f"  History saved to: {history_path}")
    

    arch_info = {
        'architecture': f'SahabatNet-{architecture.upper()}',
        'input_shape': list(input_shape),
        'num_classes': NUM_CLASSES,
        'total_params': int(total_params),
        'training_config': {
            'epochs': epochs,
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'patience': patience,
            'seed': seed,
            'use_synthetic': isinstance(train_gen, SyntheticDataGenerator),
            'synthetic_samples': synthetic_samples if isinstance(train_gen, SyntheticDataGenerator) else None,
        },
        'final_metrics': final_metrics,
        'training_time_seconds': round(training_time, 1),
        'trained_at': datetime.now().isoformat(),
        'classes': ALL_CHARS,
    }
    arch_path = os.path.join(output_dir, 'architecture.json')
    with open(arch_path, 'w') as f:
        json.dump(arch_info, f, indent=2)
    print(f"  Architecture saved to: {arch_path}")
    

    return {
        'model': model,
        'history': hist_dict,
        'metrics': final_metrics,
        'config': arch_info['training_config'],
        'model_path': model_path,
        'history_path': history_path,
        'arch_path': arch_path,
        'training_time': training_time,
    }


def plot_training_history(history: Dict[str, list], save_path: Optional[str] = None):
    """Plot training curves (loss & accuracy vs epoch)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('SahabatNet Training Curves', fontsize=14, fontweight='bold')
    

    if 'loss' in history:
        axes[0].plot(history['loss'], label='Training Loss', color='#3498db')
    if 'val_loss' in history:
        axes[0].plot(history['val_loss'], label='Validation Loss', color='#e74c3c')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Loss Curve')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    

    if 'accuracy' in history:
        axes[1].plot(history['accuracy'], label='Training Accuracy', color='#3498db')
    if 'val_accuracy' in history:
        axes[1].plot(history['val_accuracy'], label='Validation Accuracy', color='#27ae60')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Accuracy Curve')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  Training curves saved to: {save_path}")
    else:
        plt.show()






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SahabatNet CNN")
    parser.add_argument("--image-dir", type=str, default=None,
                        help="Directory containing training images")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Maximum training epochs (default: 100)")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size (default: 32)")
    parser.add_argument("--lr", type=float, default=0.001,
                        help="Learning rate (default: 0.001)")
    parser.add_argument("--arch", type=str, default="v1",
                        choices=["v1", "tiny"],
                        help="Architecture: v1 (full) or tiny (lightweight)")
    parser.add_argument("--patience", type=int, default=7,
                        help="Early stopping patience (default: 7)")
    parser.add_argument("--synthetic", type=int, default=500,
                        help="Number of synthetic samples for fallback (default: 500)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for model artifacts")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip plotting training curves")
    args = parser.parse_args()
    

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    image_dir = args.image_dir or str(PROJECT_ROOT / "data_science" / "datasets" / "augmented" / "_unsorted")
    output_dir = args.output_dir or str(PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple")
    

    results = train_cnn(
        image_dir=image_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        architecture=args.arch,
        patience=args.patience,
        use_synthetic=True,
        synthetic_samples=args.synthetic,
        output_dir=output_dir,
    )
    

    if not args.no_plot:
        plot_path = os.path.join(output_dir, 'training_curves.png')
        try:
            plot_training_history(results['history'], save_path=plot_path)
        except Exception as e:
            print(f"  Could not plot training curves: {e}")
    
    print("\n" + "=" * 65)
    print("  TRAINING COMPLETE!")
    print("=" * 65)
    print(f"  Accuracy     : {results['metrics']['accuracy'] * 100:.1f}%")
    print(f"  Top-3 Acc    : {results['metrics']['top_3_accuracy'] * 100:.1f}%")
    print(f"  Loss         : {results['metrics']['loss']:.4f}")
    print(f"  Time         : {results['training_time']:.1f}s")
    print(f"  Model path   : {results['model_path']}")
