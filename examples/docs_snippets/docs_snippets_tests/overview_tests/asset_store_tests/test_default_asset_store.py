from dagster import execute_pipeline
from dagster.seven import TemporaryDirectory
from docs_snippets.overview.asset_stores.default_asset_store import my_pipeline


def test_default_asset_store():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"asset_store": {"config": {"base_dir": tmpdir}}}},
        )
