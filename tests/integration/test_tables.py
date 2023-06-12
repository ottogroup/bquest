import pandas as pd
import pytest

from tests.integration import GOOGLE_PROJECT_ID

pytestmark = pytest.mark.integration

if not GOOGLE_PROJECT_ID:
    pytest.skip(
        "authentication with Google Cloud required (current active project will be used for tests)",
        allow_module_level=True,
    )


class TestBigQueryTable:
    def test_create_and_delete_tables_from_json_definition(self, table_def_builder, bq_client) -> None:
        table_def = table_def_builder.from_json(
            "mytable",
            [
                {
                    "name": "han",
                    "movie": {"starwars": [{"part": "1", "rating": 1}]},
                },
                {
                    "name": "lea",
                    "movie": {
                        "starwars": [
                            {"part": "4", "rating": 3},
                            {"part": "6", "rating": 2},
                        ]
                    },
                },
            ],
        )
        table = table_def.load_to_bq(bq_client)
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["name"][0] == "han"
        assert df["name"][1] == "lea"

    def test_create_and_delete_tables_from_dataframe_definition(self, table_def_builder, bq_client) -> None:
        df = pd.DataFrame.from_dict({"row_1": ["bar"], "row_2": ["my"]}, orient="index", columns=["foo"])
        table_def = table_def_builder.from_df("mytable", df)
        table = table_def.load_to_bq(bq_client)
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["foo"][0] == "bar"
        assert df["foo"][1] == "my"
