from bquest.tables import BQTableDefinitionBuilder

import pandas as pd
from google.cloud import bigquery as bq

PROJECT_ID = "oghub-bquest-dev"


class TestBigQueryTable:
    def setup_method(self) -> None:
        self.table_def_builder = BQTableDefinitionBuilder(
            PROJECT_ID, dataset="bquest"
        )

    def test_create_and_delete_tables_from_json_definition(self) -> None:
        table_def = self.table_def_builder.from_json(
            "mytable",
            [
                {
                    "name": "han",
                    "movie": {
                        "starwars": [{"part": "1", "rating": 1}]
                    },
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
        table = table_def.load_to_bq(bq.Client(project=PROJECT_ID))
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["name"][0] == "han"
        assert df["name"][1] == "lea"

    def test_create_and_delete_tables_from_dataframe_definition(self) -> None:
        df = pd.DataFrame.from_dict(
            {"row_1": ["bar"], "row_2": ["my"]}, orient="index", columns=["foo"]
        )
        table_def = self.table_def_builder.from_df("mytable", df)
        table = table_def.load_to_bq(bq.Client(project=PROJECT_ID))
        try:
            df = table.to_df()
        finally:
            table.delete()

        assert df["foo"][0] == "bar"
        assert df["foo"][1] == "my"
