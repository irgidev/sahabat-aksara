"""
Sahabat Aksara — AI Core Module (PKB)
Pattern recognition, ML models, and inference engine.
"""

from .pattern_matching import (
    calculate_accuracy,
    create_template,
    create_handwriting_template,
    evaluate_with_details,
    run_benchmark,
    get_last_explanation,
)

__version__ = "4.0.0"
__all__ = [
    "calculate_accuracy",
    "create_template",
    "create_handwriting_template",
    "evaluate_with_details",
    "run_benchmark",
    "get_last_explanation",
]
