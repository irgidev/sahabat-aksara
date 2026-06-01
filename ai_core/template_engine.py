"""
Sahabat Aksara — Template Engine Module (PKB-1)
Generates handwriting-style templates for all 62 characters (A-Z, a-z, 0-9).
Extracted from pattern_matching.py v3 for modularity.
"""

import cv2
import numpy as np


def create_template(char: str, target_size: int = 64) -> np.ndarray:
    """
    Creates a HANDWRITING-STYLE template that resembles how a child would write.
    FIX
    Uses moderate font scale with thicker line to simulate crayon/pencil.
    """
    template = np.zeros((target_size, target_size), dtype=np.uint8)

    font = cv2.FONT_HERSHEY_SIMPLEX
    text = char.upper() if char.isupper() else (char.lower() if char.islower() else char)


    thickness = 3


    if char.isupper():
        font_scale = 2.4
    elif char.islower():
        font_scale = 1.9
    elif char.isdigit():
        font_scale = 2.4
    else:
        font_scale = 2.4

    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x = (target_size - text_width) // 2
    y = (target_size + text_height) // 2

    cv2.putText(template, text, (x, y), font, font_scale, 255, thickness, cv2.LINE_AA)

    return template


def create_handwriting_template(char: str, target_size: int = 64) -> np.ndarray:
    """
    Advanced template: creates base template with generous dilation + softening.
    FIX
    Uses multi-pass dilation for natural edge variation (like crayon strokes).
    """
    base = create_template(char, target_size)



    kernel_main = np.ones((4, 4), np.uint8)
    thick = cv2.dilate(base, kernel_main, iterations=2)



    kernel_cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8)
    softened = cv2.dilate(thick, kernel_cross, iterations=1)

    return softened


def get_all_templates(target_size: int = 64) -> dict:
    """
    Generate templates for ALL 62 characters at once.
    Returns dict mapping character -> normalized binary template.
    
    Useful for batch processing and ML training data generation.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from .preprocessor import to_binary, normalize_to_canvas

    templates = {}
    

    for c in range(ord('A'), ord('Z') + 1):
        char = chr(c)
        raw = create_handwriting_template(char, target_size)
        binary = to_binary(raw)
        normed = normalize_to_canvas(binary, target_size=target_size)
        templates[char] = normed
    

    for c in range(ord('a'), ord('z') + 1):
        char = chr(c)
        raw = create_handwriting_template(char, target_size)
        binary = to_binary(raw)
        normed = normalize_to_canvas(binary, target_size=target_size)
        templates[char] = normed
    

    for d in range(10):
        char = str(d)
        raw = create_handwriting_template(char, target_size)
        binary = to_binary(raw)
        normed = normalize_to_canvas(binary, target_size=target_size)
        templates[char] = normed
    
    return templates
