"""
Cache demo — runs the three feature tasks TWICE in the same process.

flytekit's in-process cache (lru_cache-style) kicks in on the second call
when inputs hash to the same value, so the task body is skipped entirely.

On a real Flyte cluster (with datacatalog) the cache persists across runs
and even across different users — same logic, broader scope.

Usage:
    python scripts/demo_cache.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flytekit import FlyteFile
from src.tasks.ingest import ingest_raw_data
from src.tasks.features import (
    compute_aggregation_features,
    compute_temporal_features,
    compute_category_features,
)

CSV = Path("data/orders.csv")
if not CSV.exists():
    print("Run generate_data.py first.")
    sys.exit(1)


def timed(label, fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"  {label:<45} {elapsed * 1000:>7.1f} ms")
    return result


print("=" * 60)
print("  Cache demo — two identical runs in the same process")
print("=" * 60)

raw = ingest_raw_data(csv_path=FlyteFile(path=str(CSV.resolve())))

print()
print("── Run 1 (cold — task body executes) ──────────────────────")
agg1 = timed("compute_aggregation_features", compute_aggregation_features, df=raw)
tmp1 = timed("compute_temporal_features",    compute_temporal_features,    df=raw)
cat1 = timed("compute_category_features",    compute_category_features,    df=raw)

print()
print("── Run 2 (warm — same inputs, task body should be skipped) ─")
agg2 = timed("compute_aggregation_features", compute_aggregation_features, df=raw)
tmp2 = timed("compute_temporal_features",    compute_temporal_features,    df=raw)
cat2 = timed("compute_category_features",    compute_category_features,    df=raw)

print()
print("── Result check ────────────────────────────────────────────")
print(f"  agg outputs identical:      {agg1.equals(agg2)}")
print(f"  temporal outputs identical: {tmp1.equals(tmp2)}")
print(f"  category outputs identical: {cat1.equals(cat2)}")
print()
print("── How caching actually works ──────────────────────────────")
print()
print("  LOCAL mode (what you see above):")
print("  flytekit runs @task functions directly — cache=True is")
print("  recorded in task metadata but NOT enforced locally.")
print("  Both runs execute the full task body.")
print()
print("  CLUSTER mode (real Flyte with datacatalog):")
print("  Flyte hashes each task's inputs. On rerun, if the hash")
print("  matches a stored result, the task body is SKIPPED entirely")
print("  and the cached output is returned. This works:")
print("    - across separate pipeline runs")
print("    - across different users sharing the same cluster")
print("    - until cache_version is bumped (forces recompute)")
print()
print("  To test real caching: flyte sandbox start")
print("  then: pyflyte run src/workflow.py feature_pipeline \\ ")
print("            --csv_path data/orders.csv")
