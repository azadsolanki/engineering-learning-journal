"""
Cache demo — runs the flow TWICE to show Prefect's persistent cache in action.

Unlike Flyte's local mode, Prefect's cache IS enforced locally. The first run
computes and stores results under ~/.prefect/storage. The second run with
identical inputs reads from cache — task bodies are skipped.

Watch the task status in the output:
  Run 1 → "Finished in state Completed()"
  Run 2 → "Finished in state Cached()"

Usage:
    python scripts/demo_cache.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.flow import feature_pipeline

CSV = "data/orders.csv"

print("=" * 60)
print("  Prefect Cache Demo")
print("=" * 60)

print("\n── Run 1 (cold — task bodies execute) ──────────────────────")
result1 = feature_pipeline(csv_path=CSV)
print(f"Output → {result1}")

print("\n── Run 2 (warm — feature tasks should be CACHED) ───────────")
print("Watch for: 'Finished in state Cached()' in task logs above")
result2 = feature_pipeline(csv_path=CSV)
print(f"Output → {result2}")

print("\n── Notes ─────────────────────────────────────────────────────")
print("Cache is keyed on task inputs (INPUTS policy).")
print("Expiry: 24 hours (set in cache_expiration on each @task).")
print("To bust: change the input CSV or remove ~/.prefect/storage/.")
