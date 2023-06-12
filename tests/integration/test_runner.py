import json
from typing import Any, Callable, Dict, Optional
from unittest.mock import mock_open, patch

import pytest
from google.cloud import bigquery as bq

from bquest.runner import BQConfigFileRunner, BQConfigRunner, SQLFileRunner, SQLRunner
from bquest.tables import BQTableDefinition, BQTableJsonDefinition
from tests.integration import GOOGLE_PROJECT_ID

pytestmark = pytest.mark.integration

if not GOOGLE_PROJECT_ID:
    pytest.skip(
        "authentication with Google Cloud required (current active project will be used for tests)",
        allow_module_level=True,
    )


@pytest.fixture
def simple_table_schema():
    return [
        bq.SchemaField("foo", "STRING", mode="NULLABLE"),
        bq.SchemaField("weight", "INTEGER", mode="NULLABLE"),
        bq.SchemaField("prediction_date", "STRING", mode="NULLABLE"),
    ]


@pytest.fixture
def simple_table_definition(table_def_builder, simple_table_schema) -> BQTableJsonDefinition:
    return table_def_builder.from_json(
        "abc.feed_latest",
        [
            {"foo": "bar", "weight": 23, "prediction_date": "20190301"},
            {"foo": "my", "weight": 42, "prediction_date": "20190301"},
        ],
        schema=simple_table_schema,
    )


class TestBQConfigFileRunner:
    @pytest.fixture
    def simple_bq_config(self) -> object:
        return {
            "class": "abc.loader.BQExecutor",
            "query": """
                SELECT
                    foo,
                    PARSE_DATE('%Y%m%d', prediction_date)
                FROM
                    `{source_table}`
                WHERE
                    weight > {THRESHOLD}
            """,
            "start_date": "prediction_date",
            "end_date": "prediction_date",
            "source_tables": {"source_table": "abc.feed_latest"},
            "feature_table_name": "abc.myid",
            "export_to": {
                "target": "BQ",
                "mode": "upsert",
                "primary_key": ("prediction_date_id", "random_number"),
            },
        }

    @pytest.fixture
    def bq_executor_func(self, bq_client, bq_location) -> Callable[[Dict[str, Any], Dict[str, Any]], None]:
        def f(config: Dict[str, Any], templating_vars: Dict[str, Any]) -> None:
            job_config = bq.QueryJobConfig()
            job_config.destination = bq.table.TableReference.from_string(config["feature_table_name"])
            query_job = bq_client.query(
                config["query"].format(
                    **{
                        **{"source_table": config["source_tables"]["source_table"]},
                        **templating_vars,
                    }
                ),
                location=bq_location,
                job_config=job_config,
            )
            query_job.result()

        return f

    def test_run_config_from_file(
        self,
        simple_table_definition: BQTableDefinition,
        simple_bq_config: Any,
        bq_executor_func: Callable[[Dict[str, Any], Optional[Dict[str, str]]], None],
        bq_client,
    ) -> None:
        runner = BQConfigFileRunner(
            BQConfigRunner(bq_client, bq_executor_func, GOOGLE_PROJECT_ID),
            "config/bq_config",
        )

        with patch("builtins.open", mock_open(read_data=json.dumps(simple_bq_config))) as mock_file:
            result_df = runner.run_config(
                "20190301",
                "20190308",
                [simple_table_definition],
                "abc/config.py",
                templating_vars={"THRESHOLD": "30"},
            )

            assert result_df.shape == (1, 2)
            assert result_df.iloc[0]["foo"] == "my"
            file_opened = mock_file.call_args_list[0][0][0]
            assert file_opened.replace("\\", "/") == "config/bq_config/abc/config.py"


class TestSQLFileRunner:
    @pytest.fixture
    def simple_sql(self) -> str:
        return """
            SELECT
                replace_this,
                PARSE_DATE('%Y%m%d', prediction_date)
            FROM
                `{source_table}`
            WHERE
                weight > 30
        """

    def test_run_sql_from_file(self, simple_table_definition: BQTableDefinition, simple_sql: Any, bq_client) -> None:
        runner = SQLFileRunner(SQLRunner(bq_client, GOOGLE_PROJECT_ID), "sql")
        with patch("builtins.open", mock_open(read_data=simple_sql)) as mock_file:
            result_df = runner.run(
                "foo.sql",
                [simple_table_definition],
                {"source_table": f"{simple_table_definition.dataset}.{simple_table_definition.table_name}"},
                {"replace_this": "foo"},
            )
        assert result_df.shape == (1, 2)
        assert result_df.iloc[0]["foo"] == "my"
        file_opened = mock_file.call_args_list[0][0][0]
        assert file_opened.replace("\\", "/") == "sql/foo.sql"
