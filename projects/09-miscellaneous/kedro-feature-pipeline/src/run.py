"""
Local runner — builds the DataCatalog from catalog.yml and runs the pipeline.

Usage:
    python src/run.py
    python src/run.py --only merge_features   # run a single node

No kedro CLI or project scaffold required.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from kedro.io import DataCatalog
from kedro.runner import SequentialRunner
from kedro_datasets.pandas import CSVDataset, ParquetDataset
from src.pipeline import create_pipeline


def build_catalog() -> DataCatalog:
    catalog_path = Path("conf/base/catalog.yml")
    with open(catalog_path) as f:
        conf = yaml.safe_load(f)

    datasets = {}
    type_map = {
        "pandas.CSVDataset": CSVDataset,
        "pandas.ParquetDataset": ParquetDataset,
    }
    for name, cfg in conf.items():
        ds_type = type_map[cfg["type"]]
        kwargs = {"filepath": cfg["filepath"]}
        if "load_args" in cfg:
            kwargs["load_args"] = cfg["load_args"]
        datasets[name] = ds_type(**kwargs)

    return DataCatalog(datasets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Run only this node name")
    args = parser.parse_args()

    catalog = build_catalog()
    pipe = create_pipeline()

    if args.only:
        pipe = pipe.filter(node_names=[args.only])

    print("=" * 60)
    print("  Kedro Feature Pipeline  (local run)")
    print("=" * 60)
    print(f"  Nodes: {[n.name for n in pipe.nodes]}")
    print()

    runner = SequentialRunner()
    runner.run(pipe, catalog)

    store = catalog.load("customer_feature_store")
    print()
    print("=" * 60)
    print(f"  Done!  {store.shape[0]} customers × {store.shape[1]} features")
    print(f"  Output → data/03_output/customer_feature_store.parquet")
    print("=" * 60)


if __name__ == "__main__":
    main()
