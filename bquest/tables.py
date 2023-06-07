"""Module for dealing with BigQueryTables"""

# mypy: allow-untyped-calls

import json
import uuid
from io import BytesIO
from typing import Any, Dict, List, Optional

from google.api_core import exceptions
from google.cloud import bigquery as bq
from pandas import DataFrame


class BQTable:
    """
    Represents a BigQuery table.
    """

    def __init__(self, original_table_id: str, test_table_id: str, bq_client: bq.Client) -> None:
        assert original_table_id != test_table_id

        self._original_table_id = original_table_id
        self._test_table_id = test_table_id
        self._bq_client = bq_client

    @property
    def original_table_id(self) -> str:
        """Returns the original table identifier (e.g. bquest.example_id)"""
        return self._original_table_id

    @property
    def test_table_id(self) -> str:
        """
        Returns the table identifier used for testing (e.g. bquest.example_id)
        """
        return self._test_table_id

    def remove_require_partition_filter(self, table_id: str) -> None:
        table = self._bq_client.get_table(table_id)
        if "requirePartitionFilter" in table.to_api_repr():
            table.require_partition_filter = False
            self._bq_client.update_table(table, ["require_partition_filter"])

    def to_df(self) -> DataFrame:
        """Loads the table into a dataframe

        Returns:
            DataFrame -- A pandas dataframe
        """
        self.remove_require_partition_filter(self._test_table_id)

        sql = f"SELECT * FROM `{self._test_table_id}`"

        return self._bq_client.query(sql).to_dataframe()

    def delete(self) -> None:
        """Deletes the table"""
        self._bq_client.delete_table(bq.table.TableReference.from_string(self._test_table_id))


class BQTableDefinition:
    """
    Base class for BigQuery table definitions.
    """

    def __init__(self, original_table_name: str, project: str, dataset: str, location: str):
        self._original_table_name = original_table_name
        self._project = project
        self._dataset = dataset
        self._location = location
        self._table_name = (
            f"{original_table_name}_{str(uuid.uuid1())}".replace("-", "_")
            .replace(".", "_")
            .replace("{", "_")
            .replace("}", "_")
            .replace("$", "_")
        )

    @property
    def table_name(self) -> str:
        return self._table_name

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def project(self) -> str:
        return self.project

    @property
    def fq_table_name(self) -> str:
        """
        Returns the fully qualified table name in the form
        {project_name}.{dataset}.{table_name}
        """
        return f"{self._project}.{self._dataset}.{self.table_name}"

    def load_to_bq(self, bq_client: bq.Client) -> BQTable:
        return BQTable(self._original_table_name, self.fq_table_name, bq_client)


class BQTableDataframeDefinition(BQTableDefinition):
    """
    Defines BigQuery tables based on a pandas dataframe.
    """

    def __init__(self, name: str, df: DataFrame, project: str, dataset: str, location: str) -> None:
        BQTableDefinition.__init__(self, name, project, dataset, location)
        self._dataframe = df

    def load_to_bq(self, bq_client: bq.Client) -> BQTable:
        """Loads this definition to a BigQuery table.

        Arguments:
            bq_client -- A BigQuery client

        Returns:
            BQTable -- A representative of the BigQuery table which was created.
        """
        self._dataframe.to_gbq(
            f"{self._dataset}.{self.table_name}",
            location=self._location,
            project_id=self._project,
            if_exists="replace",
        )
        return BQTable(
            self._original_table_name,
            f"{self._project}.{self._dataset}.{self.table_name}",
            bq_client,
        )


class BQTableJsonDefinition(BQTableDefinition):
    """
    Defines BigQuery tables based on a JSON format.
    """

    def __init__(
        self,
        name: str,
        rows: List[Dict[str, Any]],
        schema: Optional[List[bq.SchemaField]],
        project: str,
        dataset: str,
        location: str,
    ) -> None:
        BQTableDefinition.__init__(self, name, project, dataset, location)
        self._rows_json_sources = self._convert_rows_to_bq_json_format(rows)
        self._schema = schema

    @staticmethod
    def _convert_rows_to_bq_json_format(rows: List[Dict[str, Any]]) -> BytesIO:
        rows_as_json = [json.dumps(row) for row in rows]
        return BytesIO(bytes("\n".join(rows_as_json), "ascii"))

    def _create_bq_load_config(self) -> bq.job.LoadJobConfig:
        load_config = bq.job.LoadJobConfig()
        load_config.source_format = bq.job.SourceFormat.NEWLINE_DELIMITED_JSON
        if self._schema:
            load_config.schema = self._schema
            load_config.autodetect = False
        else:
            load_config.autodetect = True
        return load_config

    def load_to_bq(self, bq_client: bq.Client) -> BQTable:
        """Loads this definition to a BigQuery table.

        Arguments:
            bq_client -- A BigQuery client

        Returns:
            BQTable -- A representative of the BigQuery table which was created.
        """
        test_table_id = f"{self._project}.{self._dataset}.{self.table_name}"
        job = bq_client.load_table_from_file(
            self._rows_json_sources,
            bq.table.TableReference.from_string(test_table_id),
            location=self._location,
            job_config=self._create_bq_load_config(),
        )
        try:
            job.result()
        except exceptions.BadRequest:
            # same error but with full error msg
            raise exceptions.BadRequest(job.errors)

        return BQTable(self._original_table_name, test_table_id, bq_client)


class BQTableDefinitionBuilder:
    """Helper class for building BQTableDefinitions"""

    def __init__(self, project: str, dataset: str = "bquest", location: str = "EU"):
        self._project = project
        self._dataset = dataset
        self._location = location

    def from_json(
        self,
        name: str,
        rows: List[Dict[str, Any]],
        schema: Optional[List[bq.SchemaField]] = None,
    ) -> BQTableJsonDefinition:
        return BQTableJsonDefinition(name, rows, schema, self._project, self._dataset, self._location)

    def from_df(self, name: str, df: DataFrame) -> BQTableDataframeDefinition:
        return BQTableDataframeDefinition(name, df, self._project, self._dataset, self._location)

    def create_empty(self, name: str) -> BQTableDefinition:
        return BQTableDefinition(name, self._project, self._dataset, self._location)
