from typing import Any, Dict, List

import pytest
from mock import MagicMock

from bquest.runner import BQConfigRunner, BQConfigSubstitutor
from bquest.tables import BQTable, BQTableDefinition, BQTableDefinitionBuilder, BQTableJsonDefinition

pytestmark = pytest.mark.unit


@pytest.fixture()
def simple_bq_config() -> Dict[str, Any]:
    # TODO: check why query works
    return {
        "class": "biws_data.loader.BQExecutor",
        "query": """
            SELECT *
            FROM `{source_table}`
            WHERE
            BQ_PARTITIONTIME BETWEEN PARSE_TIMESTAMP('%Y%m%d', '{start_date}')
            AND PARSE_TIMESTAMP('%Y%m%d', '{end_date}')
        """,
        "start_date": "prediction_date",
        "end_date": "prediction_date",
        "source_tables": {
            "source_table": "abc.my_table",
            "view_table": "abc_views.myview",
        },
        "feature_table_name": "abc.feature_table",
        "export_to": {
            "target": "BQ",
            "mode": "upsert",
            "primary_key": ("prediction_date_id", "product_number"),
        },
    }


class TestBQConfigSubstitutor:
    def setup_method(self) -> None:
        pass

    def test_substitution(self, simple_bq_config: Dict[str, Any]) -> None:
        bq_client = MagicMock()
        source_tables = [
            BQTable("abc.my_table", "my_table", bq_client),
            BQTable("abc_views.myview", "my_view_table", bq_client),
        ]

        result = BQConfigSubstitutor(simple_bq_config).substitute(
            "20190301",
            "20190301",
            BQTable("featuretable", "myfeaturetable", bq_client),
            source_tables,
        )

        assert result["source_tables"]["source_table"] == "my_table"
        assert result["source_tables"]["view_table"] == "my_view_table"
        assert result["start_date"] == "20190301"
        assert result["end_date"] == "20190301"
        assert result["feature_table_name"] == "myfeaturetable"

    def test_substitution_accepts_partial_table_replacements_when_enabled(
        self, simple_bq_config: Dict[str, Any]
    ) -> None:
        bq_client = MagicMock()
        source_tables = [BQTable("abc.my_table", "my_table", bq_client)]

        result = BQConfigSubstitutor(simple_bq_config, allow_partial=True).substitute(
            "20190301",
            "20190301",
            BQTable("featuretable", "myfeaturetable", bq_client),
            source_tables,
        )

        assert result["source_tables"]["source_table"] == "my_table"
        assert result["source_tables"]["view_table"] == "abc_views.myview"

    def test_substitution_rejects_partial_table_replacements(self, simple_bq_config: Dict[str, Any]) -> None:
        bq_client = MagicMock()
        source_tables = [BQTable("abc.my_table", "my_table", bq_client)]

        with pytest.raises(ValueError) as _:
            BQConfigSubstitutor(simple_bq_config).substitute(
                "20190301",
                "20190301",
                BQTable("featuretable", "myfeaturetable", bq_client),
                source_tables,
            )


class TestBQConfigRunner:
    @pytest.fixture()
    def table_definitions(self) -> List[BQTableJsonDefinition]:
        table_def_builder = BQTableDefinitionBuilder("myproject")
        table_a = table_def_builder.from_json("abc.my_table", [{"foo": "bar"}, {"foo": "my"}])
        table_b = table_def_builder.from_json("abc_views.myview", [{"foo_id": "bar_id"}])
        return [table_a, table_b]

    def test_run_config_returns_result_table(
        self,
        table_definitions: List[BQTableDefinition],
        simple_bq_config: Dict[str, Any],
    ) -> None:
        substitutor = BQConfigSubstitutor(simple_bq_config)
        bq_client = MagicMock()
        df = MagicMock()
        bq_client.query().to_dataframe.return_value = df
        runner = BQConfigRunner(bq_client, MagicMock(), "myproject")

        result_df = runner.run_config("20190301", "20190308", table_definitions, substitutor)

        assert result_df == df

    def test_run_config_passes_args_to_bq_executor_func(
        self,
        table_definitions: List[BQTableDefinition],
        simple_bq_config: Dict[str, Any],
    ) -> None:
        bq_config = MagicMock()
        substitutor = MagicMock()
        substitutor.substitute.return_value = bq_config
        substitutor.original_feature_table_name = "abc.mytable"
        bq_executor_func = MagicMock()
        runner = BQConfigRunner(MagicMock(), bq_executor_func, "myproject")

        runner.run_config(
            "20190301",
            "20190308",
            table_definitions,
            substitutor,
            templating_vars={"foo": "bar"},
        )

        bq_executor_func.assert_called_with(bq_config, {"foo": "bar"})

    def test_run_config_does_not_delete_test_tables_if_clean_up_flag_is_false(
        self, simple_bq_config: Dict[str, Any]
    ) -> None:
        substitutor = BQConfigSubstitutor(simple_bq_config, allow_partial=True)
        runner = BQConfigRunner(MagicMock(), MagicMock(), "myproject", clean_up=False)
        table_def = MagicMock()
        table = MagicMock()
        table_def.load_to_bq.return_value = table

        runner.run_config("20190301", "20190308", [table_def], substitutor)

        table.delete.assert_not_called()

    def test_run_config_uses_custom_result_table(self) -> None:
        substitutor = MagicMock()
        runner = BQConfigRunner(MagicMock(), MagicMock(), "myproject")
        result_table_def = MagicMock()
        result_table = MagicMock()
        result_table_def.load_to_bq.return_value = result_table

        runner.run_config(
            "20190301",
            "20190308",
            [],
            substitutor,
            result_table_definition=result_table_def,
        )

        result_table_def.load_to_bq.assert_called()
        substitutor.substitute.assert_called_with("20190301", "20190308", result_table, [])
