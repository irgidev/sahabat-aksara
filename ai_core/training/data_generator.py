"""
Data Generator for Handwriting CNN Training
============================================
Custom Keras Sequence that loads images on-the-fly from folder structure,
applies real-time augmentation, and yields batches for training.

Supports:
  - Folder-based dataset: datasets/clean/{CHAR}/image.png
  - On-the-fly augmentation (rotation, shift, zoom, noise)
  - Train/val/test split
  - One-hot label encoding (62 classes: A-Z, a-z, 0-9)

Usage:
    gen = HandwritingDataGenerator(
        image_dir="data_science/datasets/augmented",
        batch_size=32,
        target_size=(64, 64),
        augment=True,
    )
    model.fit(gen, epochs=50, validation_data=val_gen)

Author: Sahabat Aksara AI Team
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import cv2


try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    keras = None



UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
DIGITS = list("0123456789")
ALL_CHARS = UPPERCASE + LOWERCASE + DIGITS
CHAR_TO_IDX = {ch: idx for idx, ch in enumerate(ALL_CHARS)}
IDX_TO_CHAR = {idx: ch for ch, idx in CHAR_TO_IDX.items()}
NUM_CLASSES = len(ALL_CHARS)


def get_char_from_filename(filepath: str) -> Optional[str]:
    """
    Extract character target from filename.
    
    Supports patterns:
      - 'A_001.png' → 'A'
      - 'a_sample.png' → 'a'
      - '5_write.png' → '5'
      - Folder-based: clean/A/abc123.png → 'A'
    """
    name = Path(filepath).stem
    

    parent = Path(filepath).parent.name
    if parent and parent in CHAR_TO_IDX:
        return parent
    

    if name and name[0] in CHAR_TO_IDX:
        return name[0]
    

    for delim in ["_", "-", " "]:
        parts = name.split(delim)
        if parts and parts[0] in CHAR_TO_IDX:
            return parts[0]
    
    return None


class HandwritingDataGenerator(keras.utils.Sequence if keras else object):
    """
    Custom data generator for handwriting image classification.
    
    Loads images from disk on-the-fly (memory-efficient),
    applies optional augmentation, and yields (X, y) batches.
    
    Args:
        image_dir: Root directory containing images (flat or per-char folders)
        batch_size: Number of samples per batch
        target_size: Resize images to (H, W)
        augment: Apply random augmentations (rotation, shift, zoom, noise)
        color_mode: 'grayscale' or 'rgb'
        shuffle: Shuffle data each epoch
        subset: 'training', 'validation', or 'test' (for split)
        validation_split: Fraction of data for validation
        seed: Random seed for reproducibility
        max_per_class: Limit samples per class (for balanced loading)
    """
    
    def __init__(
        self,
        image_dir: str,
        batch_size: int = 32,
        target_size: Tuple[int, int] = (64, 64),
        augment: bool = False,
        color_mode: str = "grayscale",
        shuffle: bool = True,
        subset: str = "training",
        validation_split: float = 0.2,
        seed: int = 42,
        max_per_class: Optional[int] = None,
    ):
        self.image_dir = Path(image_dir)
        self.batch_size = batch_size
        self.target_size = target_size
        self.augment = augment
        self.color_mode = color_mode
        self.shuffle = shuffle
        self.subset = subset
        self.validation_split = validation_split
        self.seed = seed
        self.max_per_class = max_per_class
        self.channels = 1 if color_mode == "grayscale" else 3
        

        self.filepaths, self.labels = self._discover_files()
        

        self._split_data()
        

        self._on_epoch_begin()
        
        print(f"[DataGenerator] {self.subset}: {len(self.indexes)} images, "
              f"{len(np.unique(self.labels))} classes, "
              f"batch_size={batch_size}")
    
    def _discover_files(self) -> Tuple[List[str], List[int]]:
        """Find all image files and extract labels."""
        filepaths = []
        labels = []
        
        extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        

        for ext in extensions:
            for fp in sorted(self.image_dir.rglob(f"*{ext}")):
                char = get_char_from_filename(str(fp))
                if char is not None:
                    filepaths.append(str(fp))
                    labels.append(CHAR_TO_IDX[char])
        

        if not filepaths:
            print(f"[DataGenerator] WARNING: No labeled files found in {self.image_dir}")
            print("  Generating synthetic labels from file ordering...")
            for ext in extensions:
                for fp in sorted(self.image_dir.rglob(f"*{ext}")):
                    filepaths.append(str(fp))

                    idx = hash(fp.stem) % NUM_CLASSES
                    labels.append(idx)
        
        return filepaths, np.array(labels, dtype=np.int32)
    
    def _split_data(self):
        """Split data into train/validation sets."""
        n_total = len(self.filepaths)
        n_val = int(n_total * self.validation_split)
        
        rng = np.random.RandomState(self.seed)
        indices = rng.permutation(n_total)
        
        if self.subset == "training":
            self.indexes = indices[n_val:]
        elif self.subset == "validation":
            self.indexes = indices[:n_val]
        else:
            self.indexes = indices
    
    def _on_epoch_begin(self):
        """Reset index at start of each epoch."""
        self.current_idx = 0
        if self.shuffle:
            rng = np.random.RandomState(self.seed + self.epoch if hasattr(self, 'epoch') else 0)
            rng.shuffle(self.indexes)
    
    def __len__(self) -> int:
        """Number of batches per epoch."""
        return max(1, (len(self.indexes) + self.batch_size - 1) // self.batch_size)
    
    def __getitem__(self, batch_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate one batch of data."""
        start = batch_idx * self.batch_size
        end = min(start + self.batch_size, len(self.indexes))
        batch_indexes = self.indexes[start:end]
        
        X = np.zeros((len(batch_indexes), *self.target_size, self.channels), dtype=np.float32)
        y = np.zeros((len(batch_indexes), NUM_CLASSES), dtype=np.float32)
        
        for i, idx in enumerate(batch_indexes):
            img_path = self.filepaths[idx]
            img = self._load_image(img_path)
            
            if self.augment:
                img = self._augment(img)
            
            X[i] = img
            y[i, self.labels[idx]] = 1.0
        
        return X, y
    
    def _load_image(self, path: str) -> np.ndarray:
        """Load and preprocess a single image."""
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:

            img = np.zeros((*self.target_size, self.channels), dtype=np.float32)
            return img
        

        img = cv2.resize(img, (self.target_size[1], self.target_size[0]))
        

        img = img.astype(np.float32) / 255.0
        

        if len(img.shape) == 2:
            img = img[:, :, np.newaxis]
        if self.channels == 1 and img.shape[-1] != 1:
            img = img[:, :, :1]
        elif self.channels == 3 and img.shape[-1] == 1:
            img = np.repeat(img, 3, axis=-1)
        
        return img
    
    def _augment(self, img: np.ndarray) -> np.ndarray:
        """Apply random augmentations for training robustness."""
        rng = np.random.RandomState()
        

        has_channel = len(img.shape) == 3
        n_channels = img.shape[2] if has_channel else 1
        target_h, target_w = self.target_size
        

        if has_channel:
            img_2d = img[:, :, 0]
        else:
            img_2d = img
        

        if rng.random() > 0.5:
            angle = rng.uniform(-15, 15)
            h, w = img_2d.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            img_2d = cv2.warpAffine(img_2d, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        

        if rng.random() > 0.5:
            dx = int(rng.uniform(-0.1, 0.1) * img_2d.shape[1])
            dy = int(rng.uniform(-0.1, 0.1) * img_2d.shape[0])
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            img_2d = cv2.warpAffine(img_2d, M, (img_2d.shape[1], img_2d.shape[0]),
                                borderMode=cv2.BORDER_REPLICATE)
        

        if rng.random() > 0.5:
            scale = rng.uniform(0.85, 1.15)
            h, w = img_2d.shape[:2]
            new_h, new_w = int(h * scale), int(w * scale)
            img_2d = cv2.resize(img_2d, (new_w, new_h))

            start_h = max(0, (new_h - target_h) // 2)
            start_w = max(0, (new_w - target_w) // 2)
            img_2d = img_2d[start_h:start_h + target_h, start_w:start_w + target_w]

            if img_2d.shape[0] < target_h or img_2d.shape[1] < target_w:
                padded = np.zeros((target_h, target_w), dtype=img_2d.dtype)
                padded[:img_2d.shape[0], :img_2d.shape[1]] = img_2d
                img_2d = padded
        

        if rng.random() > 0.7:
            noise = rng.normal(0, 0.02, img_2d.shape).astype(np.float32)
            img_2d = np.clip(img_2d.astype(np.float32) + noise, 0, 1)
        else:
            img_2d = img_2d.astype(np.float32)
        

        if rng.random() > 0.5:
            factor = rng.uniform(0.8, 1.2)
            img_2d = np.clip(img_2d * factor, 0, 1)
        

        if n_channels == 1:
            return img_2d[:, :, np.newaxis].astype(np.float32)
        else:
            return np.stack([img_2d] * n_channels, axis=-1).astype(np.float32)
    
    def on_epoch_end(self):
        """Called at end of each epoch."""
        if hasattr(self, 'epoch'):
            self.epoch += 1
        else:
            self.epoch = 1
        self._on_epoch_begin()
    
    def get_class_distribution(self) -> Dict[str, int]:
        """Return count of samples per class for current subset."""
        dist = {}
        for idx in self.indexes:
            ch = IDX_TO_CHAR.get(self.labels[idx], "?")
            dist[ch] = dist.get(ch, 0) + 1
        return dist


class SyntheticDataGenerator(keras.utils.Sequence if keras else object):
    """
    Fallback generator that creates synthetic handwriting-like images
    when real labeled data is insufficient.
    
    Generates simple geometric shapes representing characters
    for demonstration/training purposes.
    """
    
    def __init__(
        self,
        num_samples: int = 500,
        num_classes: int = 62,
        image_size: Tuple[int, int] = (64, 64),
        batch_size: int = 32,
        augment: bool = True,
        seed: int = 42,
    ):
        self.num_samples = num_samples
        self.num_classes = min(num_classes, NUM_CLASSES)
        self.image_size = image_size
        self.batch_size = batch_size
        self.augment = augment
        self.seed = seed
        

        self.X, self.y = self._generate_synthetic_data()
        

        rng = np.random.RandomState(seed)
        indices = rng.permutation(num_samples)
        n_val = num_samples // 5
        self.train_idx = indices[n_val:]
        self.val_idx = indices[:n_val]
        
        self.current_train = 0
        self.current_val = 0
    
    def _generate_synthetic_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic character images using OpenCV drawing."""
        rng = np.random.RandomState(self.seed)
        
        X = np.zeros((self.num_samples, *self.image_size, 1), dtype=np.float32)
        y = np.zeros((self.num_samples,), dtype=np.int32)
        
        for i in range(self.num_samples):
            cls = i % self.num_classes
            y[i] = cls
            

            canvas = np.ones((self.image_size[0], self.image_size[1]), dtype=np.uint8) * 255
            

            ch = IDX_TO_CHAR.get(cls, "?")
            font_scale = rng.uniform(1.5, 3.0)
            thickness = rng.uniform(1, 4)
            

            cx = self.image_size[1] // 2 + rng.randint(-8, 9)
            cy = self.image_size[0] // 2 + rng.randint(-8, 9)
            

            cv2.putText(canvas, ch, (cx, cy),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                       0, int(thickness), cv2.LINE_AA)
            

            canvas = 255 - canvas
            

            if rng.random() > 0.3:
                noise = rng.randint(0, 30, canvas.shape, dtype=np.uint8)
                canvas = cv2.add(canvas, noise)
            

            if rng.random() > 0.5:
                ksize = rng.choice([1, 3])
                canvas = cv2.GaussianBlur(canvas, (ksize, ksize), 0)
            
            X[i, :, :, 0] = canvas.astype(np.float32) / 255.0
        
        return X, y
    
    def __len__(self):
        return max(1, (len(self.train_idx) + self.batch_size - 1) // self.batch_size)
    
    def __getitem__(self, idx):
        start = idx * self.batch_size
        end = min(start + self.batch_size, len(self.train_idx))
        batch_idx = self.train_idx[start:end]
        
        X_batch = self.X[batch_idx].copy()
        y_batch = self.y[batch_idx]
        

        if self.augment:
            rng = np.random.RandomState(self.seed + idx)
            for i in range(len(X_batch)):
                if rng.random() > 0.5:

                    angle = rng.uniform(-10, 10)
                    M = cv2.getRotationMatrix2D(
                        (self.image_size[1]//2, self.image_size[0]//2), angle, 1.0)
                    img = (X_batch[i, :, :, 0] * 255).astype(np.uint8)
                    img = cv2.warpAffine(img, M, self.image_size,
                                        borderMode=cv2.BORDER_REPLICATE)
                    X_batch[i, :, :, 0] = img.astype(np.float32) / 255.0
        

        y_onehot = np.zeros((len(y_batch), self.num_classes), dtype=np.float32)
        for i, label in enumerate(y_batch):
            y_onehot[i, label] = 1.0
        
        return X_batch, y_onehot
    
    def get_validation_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return full validation set."""
        X_val = self.X[self.val_idx]
        y_val = self.y[self.val_idx]
        y_onehot = np.zeros((len(y_val), self.num_classes), dtype=np.float32)
        for i, label in enumerate(y_val):
            y_onehot[i, label] = 1.0
        return X_val, y_onehot


def create_generators(
    image_dir: str,
    batch_size: int = 32,
    target_size: Tuple[int, int] = (64, 64),
    validation_split: float = 0.2,
    use_synthetic_fallback: bool = True,
    synthetic_samples: int = 500,
    seed: int = 42,
) -> tuple:
    """
    Convenience function to create train+val generators.
    
    Returns:
        (train_gen, val_gen) or (train_gen, val_synthetic_X, val_synthetic_y)
    
    If real data has enough labeled files (>20), uses HandwritingDataGenerator.
    Otherwise falls back to SyntheticDataGenerator.
    """
    from pathlib import Path
    
    p = Path(image_dir)
    if p.exists():

        n_images = len(list(p.rglob("*.png")) + list(p.rglob("*.jpg")))
        
        if n_images >= 20:

            train_gen = HandwritingDataGenerator(
                image_dir=image_dir,
                batch_size=batch_size,
                target_size=target_size,
                augment=True,
                subset="training",
                validation_split=validation_split,
                seed=seed,
            )
            val_gen = HandwritingDataGenerator(
                image_dir=image_dir,
                batch_size=batch_size,
                target_size=target_size,
                augment=False,
                subset="validation",
                validation_split=validation_split,
                seed=seed,
            )
            return train_gen, val_gen
    

    if use_synthetic_fallback:
        print(f"[create_generators] Using SYNTHETIC data ({synthetic_samples} samples)")
        gen = SyntheticDataGenerator(
            num_samples=synthetic_samples,
            image_size=target_size,
            batch_size=batch_size,
            augment=True,
            seed=seed,
        )
        X_val, y_val = gen.get_validation_data()
        return gen, (X_val, y_val)
    
    raise ValueError(f"No images found in {image_dir} and synthetic fallback disabled")


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("  Data Generator Test")
    print("=" * 60)
    
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    AUG_DIR = PROJECT_ROOT / "data_science" / "datasets" / "augmented" / "_unsorted"
    
    try:
        train_gen, val_data = create_generators(
            str(AUG_DIR),
            batch_size=16,
            target_size=(64, 64),
            synthetic_samples=200,
        )
        

        if isinstance(train_gen, HandwritingDataGenerator):
            X_batch, y_batch = train_gen[0]
            print(f"\n  Batch shape: X={X_batch.shape}, y={y_batch.shape}")
            print(f"  Batches per epoch: {len(train_gen)}")
            print(f"  Class distribution: {train_gen.get_class_distribution()}")
        elif isinstance(train_gen, SyntheticDataGenerator):
            X_batch, y_batch = train_gen[0]
            print(f"\n  Batch shape: X={X_batch.shape}, y={y_batch.shape}")
            print(f"  Batches per epoch: {len(train_gen)}")
            if isinstance(val_data, tuple):
                print(f"  Validation: X={val_data[0].shape}, y={val_data[1].shape}")
        
        print("\n  Data Generator OK!")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
