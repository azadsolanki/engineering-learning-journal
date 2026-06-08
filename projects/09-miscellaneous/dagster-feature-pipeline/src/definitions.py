"""
Dagster Definitions — the single entry point that registers all assets.

Run locally:
    PYTHONPATH=. dagster asset materialize -f src/definitions.py -a '*'

Or via the UI:
    PYTHONPATH=. dagster dev -f src/definitions.py
    # open http://localhost:3000
"""
from dagster import (
    Definitions,
    define_asset_job,
    AssetSelection,
    load_assets_from_modules,
    ConfigurableResource,
)
from src.assets import features

all_assets = load_assets_from_modules([features])

feature_pipeline_job = define_asset_job(
    name="feature_pipeline_job",
    selection=AssetSelection.all(),
)

defs = Definitions(
    assets=all_assets,
    jobs=[feature_pipeline_job],
)
