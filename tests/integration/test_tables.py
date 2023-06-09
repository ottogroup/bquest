import google.auth as google_auth
import pandas as pd
import pytest
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery as bq

from bquest.tables import BQTableDefinitionBuilder

pytestmark = pytest.mark.integration


try:
    _, GOOGLE_PROJECT_ID = google_auth.default()
except DefaultCredentialsError:
    pytest.skip(
        "authentication with Google Cloud required (current active project will be used for tests)",
        allow_module_level=True,
    )


class TestBigQueryTable:
    def setup_method(self) -> None:
        self.table_def_builder = BQTableDefinitionBuilder(GOOGLE_PROJECT_ID, dataset="bquest", location="europe-west1")

    def test_create_and_delete_tables_from_json_definition(self) -> None:
        table_def = self.table_def_builder.from_json(
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
        table = table_def.load_to_bq(bq.Client(project=GOOGLE_PROJECT_ID))
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["name"][0] == "han"
        assert df["name"][1] == "lea"

    def test_create_and_delete_tables_from_dataframe_definition(self) -> None:
        df = pd.DataFrame.from_dict({"row_1": ["bar"], "row_2": ["my"]}, orient="index", columns=["foo"])
        table_def = self.table_def_builder.from_df("mytable", df)
        table = table_def.load_to_bq(bq.Client(project=GOOGLE_PROJECT_ID))
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["foo"][0] == "bar"
        assert df["foo"][1] == "my"
