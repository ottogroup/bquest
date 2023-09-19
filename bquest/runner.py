"""Module for Running BQuest Tests"""
import ast
import copy
import os
from typing import Any, Callable, Dict, List, Optional

import pandas
from google.cloud import bigquery as bq

from bquest.tables import BQTable, BQTableDefinition, BQTableDefinitionBuilder


class BQConfigSubstitutor:
    """Substitutes parameters inside a BQ configuration"""

    def __init__(self, config: Dict[str, Any], allow_partial: Optional[bool] = False):
        self._config = config
        self._allow_partial = allow_partial

    @property
    def original_feature_table_name(self) -> str:
        return str(self._config["feature_table_name"])

    def _map_source_table_ids_to_mock_table_ids(self, source_tables: List[BQTable]) -> Dict[str, str]:
        """Match source tables with their mocks."""
        result = {}
        table_id_mapping = {t.original_table_id: t.fq_test_table_id for t in source_tables}

        # e.g. { "feed": "bquest.example_id" }
        for table_key, table_id in self._config["source_tables"].items():
            if table_id in table_id_mapping:
                result[table_key] = table_id_mapping[table_id]
            else:
                if not self._allow_partial:
                    raise ValueError(f"Found no substitution for table {table_id}")
                result[table_key] = table_id
        return result

    def substitute(
        self,
        start_date: str,
        end_date: str,
        feature_table_name: BQTable,
        test_tables: List[BQTable],
    ) -> Dict[str, Any]:
        """Substitutes a wide array of parameters inside a BQ configuration.

        Args:
            start_date: the start date
            end_date: the end date
            feature_table_name: the test table where the results will be stored
            test_tables: test tables that replace the original source tables

        Returns:
            Dict: a new BQ configuration where parameters have been substituted.
        """
        config = copy.deepcopy(self._config)
        config["start_date"] = start_date
        config["end_date"] = end_date
        config["feature_table_name"] = feature_table_name.fq_test_table_id
        config["source_tables"] = self._map_source_table_ids_to_mock_table_ids(test_tables)
        return config


class BaseRunner:
    """Base class for runners"""

    def __init__(self, bq_client: bq.Client, dataset: str = "bquest"):
        self._bq_client = bq_client
        self._bq_table_def_builder = BQTableDefinitionBuilder(bq_client.project, dataset)

    def _create_source_tables(self, table_definitions: List[BQTableDefinition]) -> List[BQTable]:
        result = []
        for table_def in table_definitions:
            test_table = table_def.load_to_bq(self._bq_client)
            result.append(test_table)
        return result

    def _create_result_table_from_def(self, table_definition: BQTableDefinition) -> BQTable:
        return table_definition.load_to_bq(self._bq_client)

    def _create_empty_result_table(self, table_name: str) -> BQTable:
        result_table_def = self._bq_table_def_builder.create_empty(table_name)
        return result_table_def.load_to_bq(self._bq_client)


class BQConfigRunner(BaseRunner):
    """Runs BQ configurations on custom data for testing"""

    def __init__(
        self,
        bq_client: bq.Client,
        bq_executor_func: Callable[[Dict[str, Any], Optional[Dict[str, str]]], None],
        dataset: str = "bquest",
        clean_up: bool = True,
    ):
        super().__init__(bq_client, dataset)
        self._bq_executor_func = bq_executor_func
        self._clean_up = clean_up

    def run_config(
        self,
        start_date: str,
        end_date: str,
        source_table_definitions: List[BQTableDefinition],
        substitutor: BQConfigSubstitutor,
        result_table_definition: Optional[BQTableDefinition] = None,
        templating_vars: Optional[Dict[str, str]] = None,
    ) -> pandas.DataFrame:
        """Runs a BQ configuration with custom table definitions.

        Args:
            start_date: the start date (e.g. 20190301)
            end_date: the end date (e.g. 20190308)
            source_table_definitions: custom table definitions that replace the source tables of the BQ configuration
            substitutor:  a substitutor for BQ configurations
            result_table_definition: optional result table definition used for creating an empty result table
            templating_vars: variables that are inserted into the given bq configuration
        Returns:
            the contents of the results table
        """
        source_tables = self._create_source_tables(source_table_definitions)
        result_table = (
            self._create_result_table_from_def(result_table_definition)
            if result_table_definition
            else self._create_empty_result_table(substitutor.original_feature_table_name)
        )

        test_bq_config = substitutor.substitute(start_date, end_date, result_table, source_tables)

        # run config with substituted table identifiers
        self._bq_executor_func(test_bq_config, templating_vars)

        return result_table.to_df()


class BQConfigFileRunner:
    """Class for Running BQConfigs"""

    def __init__(self, bq_config_runner: BQConfigRunner, config_base_path: str) -> None:
        self._bq_config_runner = bq_config_runner
        self._config_base_path = config_base_path

    def run_config(
        self,
        start_date: str,
        end_date: str,
        source_table_definitions: List[BQTableDefinition],
        path_to_config: str,
        result_table_definition: Optional[BQTableDefinition] = None,
        allow_partial_table_substitutions: Optional[bool] = False,
        templating_vars: Optional[Dict[str, str]] = None,
    ) -> pandas.DataFrame:
        """Runs a BQ configuration file"""
        with open(os.path.join(self._config_base_path, path_to_config), "r", encoding="UTF-8") as f:
            try:
                config = ast.literal_eval(f.read())
            except ValueError as e:
                raise ValueError("Could not read the configuration.") from e
            return self._bq_config_runner.run_config(
                start_date,
                end_date,
                source_table_definitions,
                BQConfigSubstitutor(config, allow_partial=allow_partial_table_substitutions),
                result_table_definition=result_table_definition,
                templating_vars=templating_vars,
            )


class SQLRunner(BaseRunner):
    """Runs SQL queries on custom data for testing"""

    def __init__(
        self,
        bq_client: bq.Client,
        dataset: str = "bquest",
        clean_up: Optional[bool] = True,
    ):
        """

        Args:
            bq_client: BigQuery client used for interaction with BigQuery
            dataset: dataset which will be used for testing
            clean_up:  boolean if tables should be cleaned up
        """
        super(SQLRunner, self).__init__(bq_client, dataset)
        self._bq_client = bq_client
        self._clean_up = clean_up

    def run(
        self,
        sql: str,
        source_table_definitions: List[BQTableDefinition],
        substitutions: Optional[Dict[str, str]] = None,
        string_replacements: Optional[Dict[str, str]] = None,
        result_table_definition: Optional[BQTableDefinition] = None,
    ) -> pandas.DataFrame:
        """

        Args:
            sql: SQL query that is being executed in BigQuery
            source_table_definitions: source table definitions, list of BQTableDefinition
            substitutions: substitutions for the given query
            Can't use substitutions together with sql that contains curly brackets, for example sql with regexs.
            This leads to error when trying to substitute the regex which shouldn't be substituted.
            string_replacements: entire string replacements for the query, substitutions are placed before
            result_table_definition: result table definition

        Returns:
            pandas DataFrame of result table
        """
        if substitutions is None:
            substitutions = {}

        if string_replacements is None:
            string_replacements = {}

        _ = self._create_source_tables(source_table_definitions)
        _ = (
            self._create_result_table_from_def(result_table_definition)
            if result_table_definition
            else self._create_empty_result_table("result")
        )
        if substitutions:
            sql_with_substitutions = sql.format(**substitutions)
        for key, value in string_replacements.items():
            sql_with_substitutions = sql_with_substitutions.replace(key, value)

        job_config = bq.QueryJobConfig()
        query_job = self._bq_client.query(sql_with_substitutions, job_config=job_config)
        query_job.result()

        return query_job.result().to_dataframe()


class SQLFileRunner:
    """Class for running SQLFiles."""

    def __init__(self, sql_runner: SQLRunner, base_path: str) -> None:
        """

        Args:
            sql_runner: SQLRunner used to execute SQL config
            base_path: base path where SQL config is looked for
        """
        self._sql_runner = sql_runner
        self._base_path = base_path

    def run(
        self,
        path_to_sql: str,
        source_table_definitions: List[BQTableDefinition],
        substitutions: Optional[Dict[str, str]] = None,
        string_replacements: Optional[Dict[str, str]] = None,
    ) -> pandas.DataFrame:
        """

        Args:
            path_to_sql: relative path to SQL config file based on base path
            source_table_definitions: source table definitions
            substitutions: substitutions for SQL query
            string_replacements: entire string replacements for the query, substitutions are placed before

        Returns:

        """
        if substitutions is None:
            substitutions = {}

        if string_replacements is None:
            string_replacements = {}

        file = os.path.join(self._base_path, path_to_sql)
        try:
            with open(file, "r", encoding="UTF-8") as f:
                sql = f.read()
        except IOError as e:
            raise ValueError(f"Could not read the SQL file {file}.") from e
        return self._sql_runner.run(sql, source_table_definitions, substitutions, string_replacements)
