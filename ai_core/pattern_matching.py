"""
Sahabat Aksara - AI Pattern Matching Engine v4 (Facade)
=========================================================
Refactored from monolithic v3 into modular architecture (PKB-1).

Architecture:
  pattern_matching.py  ← THIS FILE (public API / facade)
    ├── preprocessor.py     Image preprocessing (binary, skeleton, normalize)
    ├── template_engine.py   Template generation for all 62 characters
    ├── scorers.py           7 scoring methods (skeleton, distance, completeness,
    │                          structural, stroke_count, HOG, SSIM)
    └── ensemble.py          Weighted combination + config-driven weights
                             + confidence + explanation + kid-friendly tips

v4 Improvements over v3:
  - Modular architecture (easy to test, extend, swap scorers)
  - NEW: HOG scorer (gradient-based shape matching)
  - NEW: SSIM scorer (structural similarity, human-like perception)
  - Config-driven ensemble weights (JSON file, per-character tuning)
  - Confidence interval ("how sure are we?")
  - Explanation breakdown + kid-friendly tip per character
  - Backward compatible: calculate_accuracy() and create_template() still work

Backward-compatible API:
  - calculate_accuracy(image_path, char_target) -> int (0-100)
  - create_template(char, target_size) -> numpy array
  - create_handwriting_template(char, target_size) -> numpy array
"""

import os
import sys
import cv2


_parent_dir = os.path.dirname(os.path.abspath(__file__))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)


from .preprocessor import (
    full_preprocess,
    to_binary,
    skeletonize,
    normalize_to_canvas,
    get_bounding_info,
)

from .template_engine import (
    create_template as _create_template,
    create_handwriting_template as _create_handwriting_template,
    get_all_templates,
)

from ai_core.scorers_v8 import score_v8 as v8_score






def calculate_accuracy(image_path: str, char_target: str = 'A') -> int:
    """
    V8 Feature-Based Scoring Engine.
    NO free points. NO template matching. Character-specific feature rules.
    Returns integer accuracy 0-100.

    FIX v9: No double-normalization. main.py already normalizes to 128x128.
    We only do binary conversion here, NOT re-normalize.
    """
    try:
        import cv2
        import numpy as np




        raw = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if raw is None:
            print(f'[V8 Eval] Cannot read image: {image_path}')
            return 0


        _, user_img = cv2.threshold(raw, 50, 255, cv2.THRESH_BINARY)


        final_score, details = v8_score(user_img, char_target=char_target)


        backend_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
        )
        os.makedirs(backend_dir, exist_ok=True)
        cv2.imwrite(os.path.join(backend_dir, "debug_user.png"), user_img)


        global _last_explanation
        _last_explanation = {
            'confidence': 'high' if final_score >= 70 else ('medium' if final_score >= 45 else 'low'),
            'tip': _v8_tip(final_score, char_target),
            'breakdown': [(k, str(v)) for k, v in details.get('feats', {}).items()] + 
                       [('anti', str(details.get('anti', [])))],
        }

        return int(max(0, min(100, round(final_score))))

    except Exception as e:
        print(f"[V8 Eval] Error: {e}")
        import traceback
        traceback.print_exc()
        return 0
        return 0



_last_explanation = None


def get_last_explanation() -> dict:
    """Return the explanation from the most recent evaluate call."""
    global _last_explanation
    return _last_explanation or {}



def create_template(char: str, target_size: int = 64):
    """Backward-compatible wrapper."""
    return _create_template(char, target_size)


def create_handwriting_template(char: str, target_size: int = 64):
    """Backward-compatible wrapper."""
    return _create_handwriting_template(char, target_size)


def _v8_tip(score, char):
    """Generate kid-friendly tip based on V8 score."""
    if score >= 80: return f'Luar biasa! Huruf {char} sempurna!'
    if score >= 70: return f'Bagus sekali! Huruf {char} sudah mirip!'
    if score >= 45: return f'Lumayan! Ayo coba lagi tulis huruf {char}!'
    if score >= 20: return f'Tetap semangat! Huruf {char} butuh latihan lagi.'
    return f'Yuk coba tulis {char} dari awal! Pasti bisa!'






def evaluate_with_details(image_path: str, char_target: str = 'A') -> dict:
    """
    Full evaluation with complete breakdown (for API / dashboard use).
    Returns dict with score, stars, confidence, explanation, tip.

    Use this when you need more than just the accuracy number.
    """
    accuracy = calculate_accuracy(image_path, char_target)
    explanation = get_last_explanation()


    stars = 3 if accuracy >= 65 else (2 if accuracy >= 45 else (1 if accuracy >= 25 else 0))

    return {
        "accuracy": accuracy,
        "stars": stars,
        "confidence": explanation.get("confidence", "medium"),
        "breakdown": explanation.get("breakdown", []),
        "tip": explanation.get("tip", ""),
        "score_details": explanation,
    }


def run_benchmark(image_path: str, char_target: str = 'A') -> dict:
    """
    Run evaluation and return raw per-scorer breakdown.
    Useful for debugging and model comparison.
    """
    accuracy = calculate_accuracy(image_path, char_target)
    explanation = get_last_explanation()

    return {
        "char_target": char_target,
        "final_accuracy": accuracy,
        "confidence": explanation.get("confidence"),
        "per_scorer": explanation.get("breakdown", []),
        "kid_tip": explanation.get("tip", ""),
    }
