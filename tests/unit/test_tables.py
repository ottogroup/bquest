from typing import Any

import pandas as pd
import pytest
from mock import MagicMock, patch

from bquest.tables import BQTable, BQTableDefinition, BQTableDefinitionBuilder

pytestmark = pytest.mark.unit


class TestBigQueryTable:
    def setup_method(self) -> None:
        self.bq_table_def_builder = BQTableDefinitionBuilder("myproject")

    @patch("uuid.uuid1")
    def test_load_to_bq_returns_table_with_random_name(self, mock_uuid_call: Any) -> None:
        mock_uuid_call.return_value = 1234
        table_def = self.bq_table_def_builder.from_json("mytable", [])
        result = table_def.load_to_bq(bq_client=MagicMock())
        assert result.test_table_id == "myproject.bquest.mytable_1234"

    @patch("uuid.uuid1")
    def test_replaces_special_chars_with_underscores_in_table_name_uuid(self, mock_uuid_call: Any) -> None:
        mock_uuid_call.return_value = "123-456"
        table_def = self.bq_table_def_builder.from_json("abc_mytable$20191224", [])
        result = table_def.load_to_bq(bq_client=MagicMock())
        assert result.test_table_id == "myproject.bquest.abc_mytable_20191224_123_456"

    def test_load_to_bq_writes_single_row_to_bq(self) -> None:
        table_def = self.bq_table_def_builder.from_json("mytable", [{"foo": "bar"}])
        bq_client = MagicMock()
        table_def.load_to_bq(bq_client=bq_client)
        bq_json_sources = bq_client.load_table_from_file.call_args_list[0][0][0]
        assert bq_json_sources.getvalue() == b'{"foo": "bar"}'

    def test_load_to_bq_writes_multiple_rows_to_bq(self) -> None:
        table_def = self.bq_table_def_builder.from_json("mytable", [{"foo": "bar"}, {"foo": "my"}])
        bq_client = MagicMock()
        table_def.load_to_bq(bq_client=bq_client)
        bq_json_sources = bq_client.load_table_from_file.call_args_list[0][0][0]
        assert bq_json_sources.getvalue().splitlines()[0] == b'{"foo": "bar"}'
        assert bq_json_sources.getvalue().splitlines()[1] == b'{"foo": "my"}'

    def test_get_table_as_dataframe(self) -> None:
        bq_client = MagicMock()
        bq_client.query().to_dataframe.return_value = pd.DataFrame.from_dict(
            {"row0": ["bar"]}, orient="index", columns=["foo"]
        )
        bq_table = BQTable("original_table_id", "test_table_id", bq_client)
        df = bq_table.to_df()
        assert df["foo"][0] == "bar"
        bq_client.query.assert_called_with("SELECT * FROM `test_table_id`")

    def test_delete_table(self) -> None:
        bq_client = MagicMock()
        bq_table = BQTable("original_table_id", "project.dataset.test_table_id", bq_client=bq_client)
        bq_table.delete()
        table_reference = bq_client.delete_table.call_args_list[0][0][0]
        assert table_reference.table_id == "test_table_id"
        assert table_reference.dataset_id == "dataset"
        assert table_reference.project == "project"

    @patch("uuid.uuid1")
    def test_load_to_bq_writes_multiple_rows_from_df(self, mock_uuid_call: Any) -> None:
        mock_uuid_call.return_value = "1234"
        df = MagicMock()
        table_def = self.bq_table_def_builder.from_df("abc.mytable", df)
        table_def.load_to_bq(bq_client=MagicMock())
        df.to_gbq.assert_called_with(
            "bquest.abc_mytable_1234",
            location="EU",
            project_id="myproject",
            if_exists="replace",
        )

    def test_table_definition_name(self) -> None:
        table_def = BQTableDefinition("original_table_name", "abc-project", "dataset", "EU")
        assert table_def.fq_table_name == f"abc-project.dataset.{table_def.table_name}"
