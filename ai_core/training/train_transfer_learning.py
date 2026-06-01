"""
Transfer Learning Pipeline for Sahabat Aksara
=================================================
Fine-tune pre-trained models (MobileNetV2 / EfficientNet) 
for handwriting character recognition.

Strategy:
  1. Load base model (pre-trained on ImageNet) — WITHOUT top layer
  2. Freeze base layers → train custom classification head (10 epochs)
  3. Unfreeze last N layers → fine-tune entire network (10 epochs, low LR)
  4. Compare: Transfer Learning vs CNN-from-scratch vs Classical ML

Base Models Supported:
  - MobileNetV2: ~3.4M params, very lightweight, good for CPU inference
  - EfficientNetB0: ~5.3M params, better accuracy/param tradeoff

Usage:
    python ai_core/training/train_transfer_learning.py --base-model mobilenet --epochs 20

Author: Sahabat Aksara AI Team (PKB-4 Phase 3)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers, callbacks, applications


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


from data_generator import (
    SyntheticDataGenerator,
    NUM_CLASSES,
    ALL_CHARS,
)






def build_mobilenet_transfer(
    input_shape: Tuple[int, int, int] = (96, 96, 3),
    num_classes: int = NUM_CLASSES,
    dropout_rate: float = 0.3,
    include_top: bool = False,
    weights: str = "imagenet",
) -> keras.Model:
    """
    Build MobileNetV2 transfer learning model.
    
    Architecture:
        Input(96,96,3)
        → MobileNetV2 (pretrained, frozen initially)
        → GlobalAveragePooling2D
        → Dense(256) → BN → ReLU → Dropout
        → Dense(num_classes) → Softmax
    
    Args:
        input_shape: Image dimensions (H, W, C). MobileNetV2 min is 32×32.
        num_classes: Number of output classes
        dropout_rate: Dropout rate for classifier head
        include_top: Whether to include ImageNet classifier (False!)
        weights: Pretrained weights ('imagenet' or None)
    
    Returns:
        Keras Model with frozen base + trainable head
    """

    base_model = applications.MobileNetV2(
        weights=weights,
        include_top=False,
        input_shape=input_shape,
        pooling=None,
    )
    

    base_model.trainable = False
    

    inputs = keras.Input(shape=input_shape, name="input_image")
    

    x = inputs
    x = applications.mobilenet_v2.preprocess_input(x)
    

    x = base_model(x, training=False)
    

    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.Dropout(dropout_rate, name="head_dropout_1")(x)
    x = layers.Dense(256, name="head_dense_1")(x)
    x = layers.BatchNormalization(name="head_bn_1")(x)
    x = layers.Activation("relu", name="head_relu_1")(x)
    x = layers.Dropout(dropout_rate * 1.5, name="head_dropout_2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", 
                          name="output")(x)
    
    model = keras.Model(inputs, outputs, name="MobileNetV2-Transfer")
    
    return model, base_model


def build_efficientnet_transfer(
    input_shape: Tuple[int, int, int] = (96, 96, 3),
    num_classes: int = NUM_CLASSES,
    dropout_rate: float = 0.3,
) -> keras.Model:
    """
    Build EfficientNetB0 transfer learning model.
    
    Similar to MobileNet but generally achieves better accuracy
    at similar parameter count.
    """
    try:
        base_model = applications.EfficientNetB0(
            weights="imagenet",
            include_top=False,
            input_shape=input_shape,
        )
    except (ValueError, AttributeError):
        print("  [Warning] EfficientNet not available, falling back to MobileNetV2")
        return build_mobilenet_transfer(input_shape, num_classes, dropout_rate)
    
    base_model.trainable = False
    
    inputs = keras.Input(shape=input_shape)
    x = applications.efficientnet.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(256)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(dropout_rate * 1.5)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    
    model = keras.Model(inputs, outputs, name="EfficientNetB0-Transfer")
    return model, base_model






class RGBDataGenerator(keras.utils.Sequence if keras else object):
    """
    Data generator that converts grayscale handwriting images to RGB
    for transfer learning models that expect 3-channel input.
    
    Converts: (H, W, 1) grayscale → (H, W, 3) RGB by repeating channels.
    Also resizes to target size expected by base model.
    """
    
    def __init__(
        self,
        image_size: Tuple[int, int] = (96, 96),
        batch_size: int = 32,
        augment: bool = True,
        **kwargs
    ):
        self.image_size = image_size
        self.batch_size = batch_size
        self.augment = augment
        

        self._inner_gen = SyntheticDataGenerator(
            image_size=image_size,
            batch_size=batch_size,
            augment=augment,
            **{k: v for k, v in kwargs.items() 
               if k in ("num_samples", "num_classes", "seed")}
        )
        

        self.num_samples = getattr(self._inner_gen, 'num_samples', 0)
        self.num_classes = getattr(self._inner_gen, 'num_classes', NUM_CLASSES)
    
    def get_validation_data(self):
        """Return validation data (converted to RGB)."""
        X, y = self._inner_gen.get_validation_data()
        if X.shape[-1] == 1:
            X = np.repeat(X, 3, axis=-1)
        return X, y
    
    def __len__(self):
        return len(self._inner_gen)
    
    def __getitem__(self, idx):
        X_gray, y = self._inner_gen[idx]
        

        if X_gray.shape[-1] == 1:
            X_rgb = np.repeat(X_gray, 3, axis=-1)
        elif X_gray.shape[-1] == 3:
            X_rgb = X_gray
        else:
            X_rgb = np.stack([X_gray] * 3, axis=-1)
        
        return X_rgb, y






def train_transfer_learning(
    base_model_name: str = "mobilenet",
    image_size: Tuple[int, int] = (96, 96),
    epochs_head: int = 15,
    epochs_finetune: int = 10,
    batch_size: int = 16,
    lr_head: float = 1e-3,
    lr_finetune: float = 1e-5,
    unfreeze_fraction: float = 0.2,
    dropout_rate: float = 0.3,
    patience: int = 5,
    n_synthetic: int = 500,
    output_dir: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Two-phase transfer learning pipeline.
    
    Phase 1: Train only the classification head (base frozen)
    Phase 2: Unfreeze last N% of base layers, fine-tune entire net
    
    Args:
        base_model_name: "mobilenet" or "efficientnet"
        image_size: Input image size (model-dependent)
        epochs_head: Epochs for phase 1 (head training)
        epochs_finetune: Epochs for phase 2 (fine-tuning)
        batch_size: Samples per batch
        lr_head: Learning rate for phase 1
        lr_finetune: Learning rate for phase 2 (much lower!)
        unfreeze_fraction: Fraction of base layers to unfreeze (0-1)
        dropout_rate: Dropout rate for head
        patience: Early stopping patience
        n_synthetic: Number of synthetic training samples
        output_dir: Where to save artifacts
        seed: Random seed
        
    Returns:
        Training results dict
    """
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_transfer")
    
    os.makedirs(output_dir, exist_ok=True)
    
    input_shape = (*image_size, 3)
    
    print("=" * 65)
    print("  TRANSFER LEARNING PIPELINE")
    print("=" * 65)
    print(f"  Base model   : {base_model_name}")
    print(f"  Input size   : {image_size} (RGB)")
    print(f"  Phase 1      : {epochs_head} epochs (frozen base)")
    print(f"  Phase 2      : {epochs_finetune} epochs (fine-tuning)")
    print(f"  Output dir   : {output_dir}")
    print()
    

    np.random.seed(seed)
    tf.random.set_seed(seed)
    

    if base_model_name.lower() == "efficientnet":
        model, base_model = build_efficientnet_transfer(
            input_shape=input_shape,
            num_classes=NUM_CLASSES,
            dropout_rate=dropout_rate,
        )
    else:
        model, base_model = build_mobilenet_transfer(
            input_shape=input_shape,
            num_classes=NUM_CLASSES,
            dropout_rate=dropout_rate,
        )
    
    model.compile(
        optimizer=optimizers.Adam(learning_rate=lr_head),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3')],
    )
    
    model.summary(print_fn=lambda x: print(f"  {x}"))
    
    total_params = sum(p.numpy().size for p in model.trainable_variables)
    total_all = sum(p.numpy().size for p in model.variables)
    print(f"\n  Trainable params : {total_params:,} / {total_all:,} total")
    

    train_gen = RGBDataGenerator(
        image_size=image_size,
        batch_size=batch_size,
        augment=True,
        num_samples=n_synthetic,
        seed=seed,
    )
    
    val_data_gen = RGBDataGenerator(
        image_size=image_size,
        batch_size=batch_size,
        augment=False,
        num_samples=max(n_synthetic // 5, 50),
        seed=seed + 100,
    )
    X_val, y_val = val_data_gen.get_validation_data()
    

    if X_val.shape[-1] == 1:
        X_val_rgb = np.repeat(X_val, 3, axis=-1)
    else:
        X_val_rgb = X_val
    
    print(f"\n[Data] Training: {len(train_gen)} batches, "
          f"Validation: {X_val_rgb.shape[0]} samples")
    

    cb_list = [
        callbacks.EarlyStopping(
            monitor='val_loss', patience=patience,
            restore_best_weights=True, verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5,
            patience=3, min_lr=1e-7, verbose=1,
        ),
        callbacks.CSVLogger(
            os.path.join(output_dir, 'transfer_log.csv'),
            append=False,
        ),
    ]
    

    print("\n" + "=" * 60)
    print("  PHASE 1: Training Classification Head (Base Frozen)")
    print("=" * 60)
    
    start_phase1 = time.time()
    history_phase1 = model.fit(
        train_gen,
        epochs=epochs_head,
        validation_data=(X_val_rgb, y_val),
        callbacks=cb_list,
        verbose=1,
    )
    phase1_time = time.time() - start_phase1
    

    print("\n" + "=" * 60)
    print(f"  PHASE 2: Fine-Tuning (Unfreeze last {unfreeze_fraction*100:.0f}% of base)")
    print("=" * 60)
    

    base_model.trainable = True
    n_base_layers = len(base_model.layers)
    n_unfreeze = max(1, int(n_base_layers * unfreeze_fraction))
    

    for layer in base_model.layers[:-n_unfreeze]:
        layer.trainable = False
    for layer in base_model.layers[-n_unfreeze:]:
        layer.trainable = True
    

    model.compile(
        optimizer=optimizers.Adam(learning_rate=lr_finetune),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3')],
    )
    
    trainable_after = sum(p.numpy().size for p in model.trainable_variables)
    print(f"  Now training {trainable_after:,} parameters "
          f"(unfroze {n_unfreeze}/{n_base_layers} base layers)")
    
    start_phase2 = time.time()
    history_phase2 = model.fit(
        train_gen,
        epochs=epochs_finetune,
        validation_data=(X_val_rgb, y_val),
        callbacks=cb_list,
        verbose=1,
    )
    phase2_time = time.time() - start_phase2
    
    total_time = phase1_time + phase2_time
    print(f"\n  Phase 1: {phase1_time:.1f}s | Phase 2: {phase2_time:.1f}s | Total: {total_time:.1f}s")
    

    eval_results = model.evaluate(X_val_rgb, y_val, verbose=0)
    metric_names = ['loss', 'accuracy', 'top_3_accuracy']
    final_metrics = dict(zip(metric_names, [float(r) for r in eval_results]))
    
    print("\n  Final Validation Metrics:")
    for name, val in final_metrics.items():
        print(f"    {name}: {val:.4f}")
    

    model_path = os.path.join(output_dir, 'weights.h5')
    model.save(model_path)
    print(f"\n  Model saved: {model_path} ({os.path.getsize(model_path)/1024:.1f} KB)")
    

    combined_history = {}
    for key in set(list(history_phase1.history.keys()) + list(history_phase2.history.keys())):
        combined_history[key] = (
            history_phase1.history.get(key, []) +
            history_phase2.history.get(key, [])
        )
    
    hist_path = os.path.join(output_dir, 'training_history.json')
    with open(hist_path, 'w') as f:
        json.dump({k: [float(v) for v in vals] for k, vals in combined_history.items()},
                   f, indent=2)
    
    arch_info = {
        "architecture": f"{base_model_name.title()}Transfer",
        "base_model": base_model_name,
        "input_shape": list(input_shape),
        "num_classes": NUM_CLASSES,
        "total_params": int(total_all),
        "trainable_params_final": int(trainable_after),
        "training_config": {
            "epochs_phase1": epochs_head,
            "epochs_phase2": epochs_finetune,
            "lr_head": lr_head,
            "lr_finetune": lr_finetune,
            "unfreeze_fraction": unfreeze_fraction,
            "batch_size": batch_size,
            "seed": seed,
            "synthetic_samples": n_synthetic,
        },
        "final_metrics": final_metrics,
        "phase_times": {
            "phase1_seconds": round(phase1_time, 1),
            "phase2_seconds": round(phase2_time, 1),
            "total_seconds": round(total_time, 1),
        },
        "classes": ALL_CHARS[:NUM_CLASSES],
        "trained_at": __import__('datetime').datetime.now().isoformat(),
    }
    
    arch_path = os.path.join(output_dir, 'architecture.json')
    with open(arch_path, 'w') as f:
        json.dump(arch_info, f, indent=2)
    
    return {
        "model": model,
        "history": combined_history,
        "metrics": final_metrics,
        "config": arch_info["training_config"],
        "model_path": model_path,
        "arch_path": arch_path,
        "training_time": total_time,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Transfer Learning Model")
    parser.add_argument("--base-model", type=str, default="mobilenet",
                        choices=["mobilenet", "efficientnet"],
                        help="Base model architecture")
    parser.add_argument("--epochs", type=int, default=25,
                        help="Total epochs (split between phases)")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr-head", type=float, default=1e-3)
    parser.add_argument("--lr-finetune", type=float, default=1e-5)
    parser.add_argument("--synthetic", type=int, default=500)
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()
    
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    output_dir = args.output_dir or str(PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_transfer")
    
    results = train_transfer_learning(
        base_model_name=args.base_model,
        epochs_head=args.epochs * 3 // 5,
        epochs_finetune=args.epochs * 2 // 5,
        batch_size=args.batch_size,
        lr_head=args.lr_head,
        lr_finetune=args.lr_finetune,
        n_synthetic=args.synthetic,
        output_dir=output_dir,
    )
    
    print("\n" + "=" * 65)
    print("  TRANSFER LEARNING COMPLETE!")
    print("=" * 65)
    print(f"  Accuracy     : {results['metrics']['accuracy']*100:.1f}%")
    print(f"  Top-3 Acc    : {results['metrics']['top_3_accuracy']*100:.1f}%")
    print(f"  Loss         : {results['metrics']['loss']:.4f}")
    print(f"  Time         : {results['training_time']:.1f}s")
    print(f"  Model path   : {results['model_path']}")
