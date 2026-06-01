"""
CNN Evaluation & Analysis for Sahabat Aksara
================================================
Comprehensive evaluation of trained CNN model:
  - Confusion matrix (62×62 or reduced)
  - Top-K accuracy (K=1,3,5)
  - Per-class accuracy analysis
  - Failure case analysis (worst predictions)
  - Inference time benchmark
  - Comparison with classical ML baselines

Usage:
    python ai_core/training/evaluate_cnn.py --model-path ai_core/models/deep/cnn_simple/weights.h5

Author: Sahabat Aksara AI Team (PKB-3 Phase 4)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import tensorflow as tf
from tensorflow import keras






def load_cnn_model(model_path: str) -> keras.Model:
    """Load trained CNN model from .h5 file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    model = keras.models.load_model(model_path)
    print(f"[Load] Model loaded from {model_path}")
    print(f"       Input shape: {model.input_shape}")
    print(f"       Output shape: {model.output_shape}")
    return model


def load_training_history(history_path: str) -> Dict[str, list]:
    """Load training history JSON."""
    with open(history_path, 'r') as f:
        return json.load(f)


def load_architecture_info(arch_path: str) -> Dict[str, Any]:
    """Load architecture metadata JSON."""
    with open(arch_path, 'r') as f:
        return json.load(f)






def evaluate_model(
    model: keras.Model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation on test set.
    
    Returns dict with:
        - loss, accuracy, top_k_accuracy
        - confusion_matrix
        - per_class_metrics
        - confused_pairs
        - inference_time_ms
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report,
        top_k_accuracy_score as sklearn_top_k,
    )
    
    if class_names is None:
        from data_generator import ALL_CHARS
        class_names = list(ALL_CHARS[:y_test.shape[1]])
    

    start_time = time.time()
    loss, acc, top3_acc = model.evaluate(X_test, y_test, verbose=0)
    eval_time = time.time() - start_time
    

    y_true = np.argmax(y_test, axis=1)
    

    n_samples = len(X_test)
    start_time = time.time()
    y_proba = model.predict(X_test, verbose=0)
    pred_time = time.time() - start_time
    inference_ms = (pred_time / n_samples) * 1000
    
    y_pred = np.argmax(y_proba, axis=1)
    

    cm = confusion_matrix(y_true, y_pred)
    


    present_labels = sorted(set(y_true.tolist() + y_pred.tolist()))
    present_names = [class_names[i] for i in present_labels]
    
    report = classification_report(y_true, y_pred, labels=present_labels,
                                   target_names=present_names,
                                   output_dict=True, zero_division=0)
    
    per_class = {}
    for i, name in enumerate(class_names):
        key = str(i) if str(i) in report else name
        if key in report:
            per_class[name] = {
                'precision': round(report[key].get('precision', 0), 4),
                'recall': round(report[key].get('recall', 0), 4),
                'f1': round(report[key].get('f1-score', 0), 4),
                'support': int(report[key].get('support', 0)),
            }
    

    top5_acc = float(sklearn_top_k(y_true, y_proba, k=5, labels=np.arange(len(class_names))))
    

    n_cm = cm.shape[0]
    confused_pairs = []
    for i in range(n_cm):
        for j in range(n_cm):
            if i != j and cm[i][j] > 0:
                confused_pairs.append({
                    'true': class_names[i] if i < len(class_names) else str(i),
                    'predicted': class_names[j] if j < len(class_names) else str(j),
                    'count': int(cm[i][j]),
                })
    
    confused_pairs.sort(key=lambda x: x['count'], reverse=True)
    

    failures = []
    for idx in range(n_samples):
        if y_true[idx] != y_pred[idx]:
            failures.append({
                'index': idx,
                'true_label': class_names[y_true[idx]],
                'predicted': class_names[y_pred[idx]],
                'confidence': round(float(y_proba[idx, y_pred[idx]]), 4),
                'true_confidence': round(float(y_proba[idx, y_true[idx]]), 4),
            })
    
    failures.sort(key=lambda x: x['confidence'], reverse=True)
    
    return {
        'loss': round(float(loss), 6),
        'accuracy': round(float(acc), 6),
        'top_3_accuracy': round(float(top3_acc), 6),
        'top_5_accuracy': round(top5_acc, 6),
        'inference_time_total_s': round(pred_time, 4),
        'inference_time_per_image_ms': round(inference_ms, 2),
        'n_test_samples': n_samples,
        'confusion_matrix': cm.tolist(),
        'per_class_metrics': per_class,
        'confused_pairs': confused_pairs[:20],
        'failure_cases': failures[:20],
        'class_names': class_names,
    }






def plot_confusion_matrix(
    cm_data: List[List[int]],
    class_names: List[str],
    save_path: str,
    title: str = "CNN Confusion Matrix",
    max_classes: int = 25,
):
    """Plot confusion matrix heatmap."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    cm = np.array(cm_data)
    n = len(class_names)
    

    if n > max_classes:

        row_sums = cm.sum(axis=1) - np.diag(cm)
        top_indices = np.argsort(row_sums)[-max_classes:]
        cm = cm[np.ix_(top_indices, top_indices)]
        display_names = [class_names[i] for i in top_indices]
        title += f" (Top-{max_classes} Most Confused)"
    else:
        display_names = class_names
    
    fig_size = max(8, min(18, len(display_names) * 0.55))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    

    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-10) * 100
    
    sns.heatmap(cm_norm, annot=True, fmt='.0f', cmap='Blues',
                xticklabels=display_names, yticklabels=display_names,
                ax=ax, cbar_kws={'label': 'Percentage (%)'})
    
    ax.set_xlabel('Predicted Label', fontsize=11)
    ax.set_ylabel('True Label', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Confusion matrix saved: {save_path}")


def plot_per_class_accuracy(
    per_class: Dict[str, Dict],
    save_path: str,
):
    """Plot bar chart of per-class accuracy (recall)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    names = sorted(per_class.keys())
    recalls = [per_class[n]['recall'] for n in names]
    precisions = [per_class[n]['precision'] for n in names]
    
    fig, ax = plt.subplots(figsize=(max(12, len(names)*0.35), 6))
    
    x = np.arange(len(names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, precisions, width, label='Precision', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, recalls, width, label='Recall', color='#27ae60', alpha=0.8)
    
    ax.set_ylabel('Score')
    ax.set_title('Per-Class Precision & Recall', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)
    ax.legend()
    ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Target 80%')
    ax.set_ylim(0, 1.05)
    ax.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Per-class metrics saved: {save_path}")


def plot_failure_cases(
    X_test: np.ndarray,
    failure_cases: List[Dict],
    class_names: List[str],
    save_path: str,
    max_show: int = 16,
):
    """Plot grid of worst failure cases."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    n_show = min(max_show, len(failure_cases))
    if n_show == 0:
        print("  No failures to show!")
        return
    
    cols = 4
    rows = (n_show + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(14, 3*rows))
    fig.suptitle("CNN Failure Cases (Worst Predictions)", fontsize=14, fontweight='bold')
    
    axes_flat = axes.flat if rows > 1 or cols > 1 else [axes]
    
    for i in range(rows * cols):
        ax = axes_flat[i]
        if i < n_show:
            fc = failure_cases[i]
            idx = fc['index']
            img = X_test[idx]
            
            if img.shape[-1] == 1:
                img_disp = img[:, :, 0]
            else:
                img_disp = img
            
            ax.imshow(img_disp, cmap='gray')
            ax.set_title(
                f"T:{fc['true_label']} P:{fc['predicted']}\n"
                f"Conf: {fc['confidence']:.2f}",
                fontsize=9, color='red' if fc['true_label'] != fc['predicted'] else 'green'
            )
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Failure cases saved: {save_path}")






def generate_comparison_report(
    cnn_results: Dict,
    classical_results_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate comparison table: CNN vs Classical ML models.
    
    If classical results exist at training_results.json, include them.
    """
    from data_generator import ALL_CHARS
    
    report = {
        'cnn': {
            'accuracy': cnn_results.get('accuracy', 0),
            'top_3_accuracy': cnn_results.get('top_3_accuracy', 0),
            'top_5_accuracy': cnn_results.get('top_5_accuracy', 0),
            'inference_ms': cnn_results.get('inference_time_per_image_ms', 0),
            'type': 'Deep Learning (CNN)',
        },
        'comparison_generated_at': __import__('datetime').datetime.now().isoformat(),
    }
    

    if classical_results_path and Path(classical_results_path).exists():
        try:
            with open(classical_results_path, 'r') as f:
                classical = json.load(f)
            
            if 'models' in classical:
                report['classical_models'] = {}
                for mname, mdata in classical['models'].items():
                    report['classical_models'][mname] = {
                        'accuracy': mdata.get('test_accuracy', 0),
                        'inference_ms': mdata.get('timing', {}).get('inference_ms', 0),
                        'type': 'Classical ML',
                    }
        except Exception as e:
            report['classical_load_error'] = str(e)
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"  Comparison report saved: {output_path}")
    
    return report






def run_evaluation(
    model_path: str,
    output_dir: Optional[str] = None,
    synthetic_samples: int = 200,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Full evaluation pipeline.
    
    Args:
        model_path: Path to trained CNN weights.h5
        output_dir: Directory for saving reports/plots
        synthetic_samples: Number of test samples (synthetic fallback)
        seed: Random seed
    
    Returns:
        Complete evaluation results dictionary
    """
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "ai_core" / "evaluation")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 65)
    print("  SAHABATNET CNN EVALUATION")
    print("=" * 65)
    

    model = load_cnn_model(model_path)
    

    num_classes = model.output_shape[-1]
    from data_generator import ALL_CHARS, IDX_TO_CHAR
    

    from data_generator import SyntheticDataGenerator
    
    gen = SyntheticDataGenerator(
        num_samples=synthetic_samples,
        num_classes=num_classes,
        augment=False,
        seed=seed + 1,
    )
    X_test, y_test = gen.get_validation_data()
    

    actual_classes = y_test.shape[1]
    class_names = list(ALL_CHARS[:actual_classes])
    
    print(f"\n[Test Data] {X_test.shape[0]} samples, {actual_classes} classes")
    

    results = evaluate_model(model, X_test, y_test, class_names)
    

    print("\n" + "-" * 50)
    print("  EVALUATION RESULTS")
    print("-" * 50)
    print(f"  Accuracy          : {results['accuracy']*100:.2f}%")
    print(f"  Top-3 Accuracy    : {results['top_3_accuracy']*100:.2f}%")
    print(f"  Top-5 Accuracy    : {results['top_5_accuracy']*100:.2f}%")
    print(f"  Loss              : {results['loss']:.4f}")
    print(f"  Inference Time     : {results['inference_time_per_image_ms']:.1f} ms/image")
    print(f"  Test Samples      : {results['n_test_samples']}")
    

    if results['confused_pairs']:
        print(f"\n  Top-5 Confused Pairs:")
        for cp in results['confused_pairs'][:5]:
            print(f"    '{cp['true']}' → '{cp['predicted']}' ({cp['count']}x)")
    

    eval_json_path = os.path.join(output_dir, 'cnn_evaluation.json')
    with open(eval_json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved: {eval_json_path}")
    

    try:
        plot_confusion_matrix(
            results['confusion_matrix'],
            results['class_names'],
            os.path.join(output_dir, 'cnn_confusion_matrix.png'),
        )
        
        plot_per_class_accuracy(
            results['per_class_metrics'],
            os.path.join(output_dir, 'cnn_per_class_metrics.png'),
        )
        
        plot_failure_cases(
            X_test,
            results['failure_cases'],
            results['class_names'],
            os.path.join(output_dir, 'cnn_failure_cases.png'),
        )
    except Exception as e:
        print(f"  Plotting error (non-critical): {e}")
    

    classical_path = str(PROJECT_ROOT / "ai_core" / "evaluation" / "training_results.json")
    comparison = generate_comparison_report(
        results,
        classical_results_path=classical_path,
        output_path=os.path.join(output_dir, 'cnn_vs_classical.json'),
    )
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SahabatNet CNN")
    parser.add_argument("--model-path", type=str,
                        default=None,
                        help="Path to weights.h5 file")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for reports")
    parser.add_argument("--samples", type=int, default=200,
                        help="Number of test samples (default: 200)")
    args = parser.parse_args()
    
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    model_path = args.model_path or str(PROJECT_ROOT / "ai_core" / "models" / "deep" / "cnn_simple" / "weights.h5")
    
    results = run_evaluation(
        model_path=model_path,
        output_dir=args.output_dir,
        synthetic_samples=args.samples,
    )
    
    print("\n" + "=" * 65)
    print("  EVALUATION COMPLETE!")
    print("=" * 65)
