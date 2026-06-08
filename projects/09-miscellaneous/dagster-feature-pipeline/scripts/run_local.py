"""
Materialise all assets locally without starting the Dagster server.

Usage:
    PYTHONPATH=. python scripts/run_local.py
    PYTHONPATH=. python scripts/run_local.py --csv data/orders.csv
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dagster import materialize
from src.assets.features import (
    raw_orders,
    aggregation_features,
    temporal_features,
    category_features,
    customer_feature_store,
)

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="data/orders.csv")
args = parser.parse_args()

print("=" * 60)
print("  Dagster Feature Pipeline  (local materialisation)")
print("=" * 60)

result = materialize(
    assets=[
        raw_orders,
        aggregation_features,
        temporal_features,
        category_features,
        customer_feature_store,
    ],
    run_config={
        "ops": {
            "raw_orders": {"config": {"csv_path": args.csv}},
        }
    },
)

print()
if result.success:
    store = result.output_for_node("customer_feature_store")
    print(f"  customers : {len(store)}")
    print(f"  features  : {len(store.columns)}")
    print(f"  columns   : {', '.join(store.columns)}")
    print()
    print("  Asset materialisation log:")
    for event in result.get_asset_materialization_events():
        print(f"    ✓ {event.asset_key.path[-1]}")
else:
    print("  Pipeline failed — check logs above.")
    sys.exit(1)
