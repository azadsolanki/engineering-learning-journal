"""
Kedro pipeline definition.

A Pipeline is a collection of Nodes wired by named datasets.
The DataCatalog resolves dataset names to actual storage (files, DBs, etc.)
defined in catalog.yml — nodes themselves never reference file paths.
"""
from kedro.pipeline import Pipeline, node, pipeline
from src.nodes.features import (
    ingest_raw_data,
    compute_aggregation_features,
    compute_temporal_features,
    compute_category_features,
    merge_features,
)


def create_pipeline() -> Pipeline:
    return pipeline(
        [
            node(
                func=ingest_raw_data,
                inputs="orders_csv",
                outputs="raw_orders",
                name="ingest_raw_data",
            ),
            node(
                func=compute_aggregation_features,
                inputs="raw_orders",
                outputs="agg_features",
                name="compute_aggregation_features",
            ),
            node(
                func=compute_temporal_features,
                inputs="raw_orders",
                outputs="temporal_features",
                name="compute_temporal_features",
            ),
            node(
                func=compute_category_features,
                inputs="raw_orders",
                outputs="category_features",
                name="compute_category_features",
            ),
            node(
                func=merge_features,
                inputs=["agg_features", "temporal_features", "category_features"],
                outputs="customer_feature_store",
                name="merge_features",
            ),
        ]
    )
