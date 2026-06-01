"""
Sahabat Aksara — Preprocessor Module (PKB-1)
Image preprocessing: binary conversion, skeletonization, normalization.
Extracted from pattern_matching.py v3 for modularity.
"""

import cv2
import numpy as np
from scipy import ndimage


def to_binary(img, threshold=50):
    """Convert image to strict binary (black=0, white=255)."""
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    return binary


def skeletonize(binary_img):
    """
    Thin image to 1-pixel-wide skeleton using Zhang-Suen algorithm.
    Removes stroke-thickness bias entirely — core fairness feature.
    """

    inverted = (binary_img == 0).astype(np.uint8)


    from skimage.morphology import thin
    skeleton = thin(inverted).astype(np.uint8) * 255


    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(skeleton, connectivity=8)
    cleaned = np.zeros_like(skeleton)
    min_size = 3
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_size:
            cleaned[labels == i] = 255

    return cleaned


def compute_distance_field(binary_img):
    """
    Compute Euclidean distance transform.
    Each white pixel = distance to nearest black pixel (edge of stroke).
    Used for tolerance-based scoring.
    """
    inverted = (binary_img == 0).astype(np.uint8)
    dist = ndimage.distance_transform_edt(inverted)
    return dist


def extract_contours_simplified(binary_img):
    """Extract contours and return simplified polygon points."""
    contours, _ = cv2.findContours(
        binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    simplified = []
    for c in contours:
        if len(c) > 3:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            simplified.append(approx)
    return simplified


def get_bounding_info(binary_img):
    """Get bounding box, centroid, aspect ratio of content."""
    coords = cv2.findNonZero(binary_img)
    if coords is None:
        return None
    x, y, w, h = cv2.boundingRect(coords)
    M = cv2.moments(binary_img, True)
    cx = int(M['m10'] / M['m00']) if M['m00'] > 0 else w // 2
    cy = int(M['m01'] / M['m00']) if M['m00'] > 0 else h // 2
    return {
        'x': x, 'y': y, 'w': w, 'h': h,
        'cx': cx, 'cy': cy,
        'aspect': w / max(1, h),
        'area': w * h,
        'pixel_count': len(coords),
    }


def normalize_to_canvas(img, target_size=64, padding_ratio=0.15):
    """
    Crop to content -> scale to fill canvas (with padding) -> center on black canvas.
    Preserves aspect ratio.
    """
    coords = cv2.findNonZero(img)
    if coords is None:
        return np.zeros((target_size, target_size), dtype=np.uint8)

    x, y, w, h = cv2.boundingRect(coords)
    if w <= 0 or h <= 0:
        return np.zeros((target_size, target_size), dtype=np.uint8)

    cropped = img[y:y+h, x:x+w]

    padding = int(target_size * padding_ratio)
    available = target_size - 2 * padding

    scale = available / max(w, h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((target_size, target_size), dtype=np.uint8)
    start_x = (target_size - new_w) // 2
    start_y = (target_size - new_h) // 2
    canvas[start_y:start_y+new_h, start_x:start_x+new_w] = resized

    return canvas


def full_preprocess(image_path: str, target_size: int = 64) -> dict:
    """
    Run full preprocessing pipeline on an image file.
    Returns dict with all processed representations.
    
    Keys in result:
      - raw: original grayscale
      - binary: strict black/white
      - normalized: cropped + scaled + centered
      - skeleton: 1-pixel thin version
      - distance_field: Euclidean distance transform
      - bounding_info: bbox, centroid, aspect ratio
    """
    user_raw = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if user_raw is None:
        raise ValueError(f"Cannot read image: {image_path}")

    binary = to_binary(user_raw)
    normalized = normalize_to_canvas(binary, target_size=target_size)

    try:
        skeleton = skeletonize(normalized)
    except ImportError:
        print("[Preprocessor] Warning: scikit-image not available, using erosion fallback")
        kernel = np.ones((2, 2), np.uint8)
        skeleton = cv2.erode(normalized, kernel, iterations=1)

    dist_field = compute_distance_field(normalized)
    bounding_info = get_bounding_info(normalized)

    return {
        'raw': user_raw,
        'binary': binary,
        'normalized': normalized,
        'skeleton': skeleton,
        'distance_field': dist_field,
        'bounding_info': bounding_info,
    }
