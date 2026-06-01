"""
PKB-6.3: Experiment Tracker
==============================
Log every experiment run with reproducibility metadata.
Supports A/B testing infrastructure for model comparison.

Output:
  - ai_core/evaluation/experiments.json

Run:
    backend/venv/Scripts/python.exe ai_core/evaluation/experiment_tracker.py
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = PROJECT_ROOT / "ai_core" / "evaluation"
EXPERIMENTS_FILE = EVAL_DIR / "experiments.json"


def get_experiment_hash(params: dict) -> str:
    """Generate deterministic hash from experiment parameters."""
    param_str = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(param_str.encode()).hexdigest()[:12]


def log_experiment(
    experiment_name: str,
    category: str,
    params: dict,
    results: dict,
    tags: list = None,
    notes: str = "",
):
    """
    Log an experiment run to the experiment tracker.
    
    Args:
        experiment_name: Human-readable name
        category: Type of experiment
        params: Input parameters (hyperparameters, config, etc.)
        results: Output metrics (accuracy, loss, time, etc.)
        tags: List of searchable tags
        notes: Free-form notes
    
    Returns:
        The experiment record dict
    """
    exp_id = get_experiment_hash({**params, "name": experiment_name})
    
    record = {
        "id": exp_id,
        "name": experiment_name,
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "params": params,
        "results": results,
        "tags": tags or [],
        "notes": notes,
        "environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
        "duration_sec": results.get("duration_sec", 0),
    }
    

    experiments = []
    if EXPERIMENTS_FILE.exists():
        try:
            with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            experiments = data.get("experiments", [])
        except Exception:
            pass
    

    existing_ids = {e["id"] for e in experiments}
    if exp_id in existing_ids:

        for i, e in enumerate(experiments):
            if e["id"] == exp_id:
                record["run_count"] = e.get("run_count", 1) + 1
                record["last_run"] = datetime.now().isoformat()
                experiments[i] = record
                break
    else:
        record["run_count"] = 1
        experiments.append(record)
    

    data = {
        "total_experiments": len(experiments),
        "last_updated": datetime.now().isoformat(),
        "experiments": experiments,
    }
    
    os.makedirs(EVAL_DIR, exist_ok=True)
    with open(EXPERIMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    return record


def query_experiments(
    category=None,
    tag=None,
    name_contains=None,
    limit=20,
    sort_by="timestamp",
    ascending=False,
):
    """Query experiments with filters."""
    if not EXPERIMENTS_FILE.exists():
        return []
    
    with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    experiments = data.get("experiments", [])
    

    if category:
        experiments = [e for e in experiments if e.get("category") == category]
    if tag:
        experiments = [e for e in experiments if tag in e.get("tags", [])]
    if name_contains:
        experiments = [e for e in experiments if name_contains.lower() in e.get("name", "").lower()]
    

    reverse_sort = not ascending
    if sort_by == "timestamp":
        experiments.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse_sort)
    elif sort_by == "accuracy":
        experiments.sort(key=lambda x: x.get("results", {}).get("accuracy", 0), reverse=reverse_sort)
    elif sort_by == "duration":
        experiments.sort(key=lambda x: x.get("duration_sec", 0), reverse=reverse_sort)
    
    return experiments[:limit]


def compare_experiments(exp_ids: list):
    """Side-by-side comparison of multiple experiments."""
    if not EXPERIMENTS_FILE.exists():
        return {"error": "No experiments file found"}
    
    with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_exps = {e["id"]: e for e in data.get("experiments", [])}
    
    comparison = []
    for eid in exp_ids:
        exp = all_exps.get(eid)
        if exp:
            comparison.append({
                "id": eid,
                "name": exp["name"],
                "category": exp["category"],
                "params": exp["params"],
                "results": exp["results"],
                "timestamp": exp["timestamp"],
            })
    
    return comparison


def get_best_experiment(metric="accuracy", category=None):
    """Find the best experiment by a given metric."""
    exps = query_experiments(category=category, sort_by=metric, ascending=False, limit=1)
    return exps[0] if exps else None






class ABTest:
    """
    Simple A/B testing framework for model comparison.
    
    Usage:
        ab = ABTest(name="cnn_vs_hybrid", description="Compare CNN vs Hybrid on same data")
        ab.set_group_a("CNN SahabatNet", cnn_predict_fn, images, labels)
        ab.set_group_b("Hybrid Engine", hybrid_predict_fn, images, labels)
        results = ab.run()
        winner = ab.declare_winner(metric="accuracy")
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.group_a = None
        self.group_b = None
        self.results = None
        self.test_id = get_experiment_hash({"name": name, "type": "ab_test"})
    
    def set_group_a(self, label: str, predict_fn, data, labels):
        """Set control group (A)."""
        self.group_a = {"label": label, "fn": predict_fn, "data": data, "labels": labels}
    
    def set_group_b(self, label: str, predict_fn, data, labels):
        """Set treatment group (B)."""
        self.group_b = {"label": label, "fn": predict_fn, "data": data, "labels": labels}
    
    def run(self):
        """Execute A/B test on both groups with identical data."""
        import numpy as np
        
        results = {
            "test_id": self.test_id,
            "name": self.name,
            "description": self.description,
            "ran_at": datetime.now().isoformat(),
            "group_a": {"label": self.group_a["label"] if self.group_a else "N/A"},
            "group_b": {"label": self.group_b["label"] if self.group_b else "N/A"},
            "comparison": {},
            "winner": None,
            "significance": None,
        }
        
        for group_key, group in [("a", self.group_a), ("b", self.group_b)]:
            if not group:
                continue
            
            t_start = time.time()
            predictions = []
            for item, true_label in zip(group["data"], group["labels"]):
                try:
                    pred = group["fn"](item)
                    predictions.append({
                        "predicted": pred,
                        "actual": true_label,
                        "correct": pred == true_label,
                    })
                except Exception as e:
                    predictions.append({"error": str(e)})
            
            elapsed = time.time() - t_start
            
            correct = sum(1 for p in predictions if p.get("correct", False))
            total = len(predictions)
            
            group_results = {
                "total_samples": total,
                "correct": correct,
                "accuracy": round(correct / total, 4) if total > 0 else 0,
                "inference_time_total_sec": round(elapsed, 3),
                "inference_time_ms_per_sample": round(elapsed / total * 1000, 2) if total > 0 else 0,
            }
            
            results[f"group_{group_key}"].update(group_results)
            results["comparison"][f"group_{group_key}"] = group_results
        

        ga = results.get("group_a", {}).get("accuracy", 0)
        gb = results.get("group_b", {}).get("accuracy", 0)
        
        if ga > gb:
            results["winner"] = results["group_a"]["label"]
            results["margin"] = round(ga - gb, 4)
        elif gb > ga:
            results["winner"] = results["group_b"]["label"]
            results["margin"] = round(gb - ga, 4)
        else:
            results["winner"] = "tie"
            results["margin"] = 0
        
        self.results = results
        

        log_experiment(
            experiment_name=f"A/B Test: {self.name}",
            category="ab_test",
            params={
                "group_a": results["group_a"]["label"],
                "group_b": results["group_b"]["label"],
            },
            results={
                "winner": results["winner"],
                "margin": results.get("margin", 0),
                **{f"acc_{k}": v.get("accuracy", 0) for k, v in results["comparison"].items()},
            },
            tags=["ab_test", "comparison"],
            notes=self.description,
        )
        
        return results
    
    def declare_winner(self, metric="accuracy"):
        """Return winner based on specified metric."""
        if not self.results:
            return None
        
        ga_val = self.results.get("group_a", {}).get(metric, 0)
        gb_val = self.results.get("group_b", {}).get(metric, 0)
        
        if ga_val >= gb_val:
            return {
                "winner": self.results["group_a"]["label"],
                "value": ga_val,
                "loser": self.results["group_b"]["label"],
                "loser_value": gb_val,
                "margin": round(ga_val - gb_val, 4),
            }
        else:
            return {
                "winner": self.results["group_b"]["label"],
                "value": gb_val,
                "loser": self.results["group_a"]["label"],
                "loser_value": ga_val,
                "margin": round(gb_val - ga_val, 4),
            }


if __name__ == "__main__":

    print("=" * 50)
    print("  PKB-6.3: Experiment Tracker Demo")
    print("=" * 50)
    
    rec = log_experiment(
        experiment_name="Demo: CNN Training Run",
        category="training",
        params={"epochs": 30, "batch_size": 32, "learning_rate": 0.001},
        results={"accuracy": 0.86, "val_accuracy": 0.82, "loss": 0.45, "duration_sec": 245},
        tags=["cnn", "training", "demo"],
        notes="Sample experiment log",
    )
    print(f"Logged: {rec['name']} (id={rec['id']})")
    

    all_exps = query_experiments(limit=5)
    print(f"\nTotal experiments: {len(all_exps)}")
    for e in all_exps:
        acc = e.get("results", {}).get("accuracy", "?")
        print(f"  - [{e['id'][:8]}] {e['name']} (acc={acc})")
