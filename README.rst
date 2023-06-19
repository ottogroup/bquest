.. image:: https://raw.githubusercontent.com/ottogroup/bquest/main/docs/assets/logo.svg
    :alt: BQuest Logo

BQuest
######

Effortlessly validate and test your Google BigQuery queries with the power of pandas DataFrames in Python.

We would like to thank `Mike Czech <https://github.com/mikeczech>`_ who is the original inventor of bquest!

**Warning**

This library is a work in progress!

Breaking changes should be expected until a 1.0 release, so version pinning is recommended.

.. image:: https://github.com/ottogroup/bquest/workflows/Tests/badge.svg
   :target: https://github.com/ottogroup/bquest/actions?workflow=Tests
   :alt: CI: Overall outcome
.. image:: https://github.com/ottogroup/bquest/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages
   :target: https://github.com/ottogroup/bquest/actions/workflows/pages/pages-build-deployment
   :alt: CD: gh-pages documentation
.. image:: https://img.shields.io/pypi/v/bquest.svg
   :target: https://pypi.org/project/bquest/
   :alt: PyPI version
.. image:: https://img.shields.io/pypi/status/bquest.svg
   :target: https://pypi.python.org/pypi/bquest/
   :alt: Project status (alpha, beta, stable)
.. image:: https://static.pepy.tech/personalized-badge/bquest?period=month&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20downloads/month
   :target: https://pepy.tech/project/bquest
   :alt: PyPI downloads
.. image:: https://img.shields.io/github/license/ottogroup/bquest
   :target: https://github.com/ottogroup/bquest/blob/main/LICENSE
   :alt: Project license
.. image:: https://img.shields.io/pypi/pyversions/bquest.svg
   :target: https://pypi.python.org/pypi/bquest/
   :alt: Python version compatibility
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Documentation: Black

Overview
********

* Use BQuest in combination with your favorite testing framework (e.g. pytest).
* Create temporary test tables from JSON_ or `pandas DataFrame`_.
* Run BQ configurations and plain SQL queries on your test tables and check the result.

.. _JSON: https://cloud.google.com/bigquery/docs/loading-data
.. _pandas DataFrame: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html

Installation
************

Via PyPi (standard):

.. code-block:: bash

    pip install bquest


Via Github (most recent):

.. code-block:: bash

    pip install git+https://github.com/ottogroup/bquest


BQuest also requires a dedicated BigQuery dataset for storing test tables, e.g.

.. code-block:: yaml

    resource "google_bigquery_dataset" "bquest" {
      dataset_id    = "bquest"
      friendly_name = "bquest"
      description   = "Source tables for bquest tests"
      location      = "EU"
      default_table_expiration_ms = 3600000
    }

We recommend setting an `expiration time`_ for tables in the bquest dataset to assure removal of those test tables upon
test execution.

.. _`expiration time`: https://www.terraform.io/docs/providers/google/r/bigquery_dataset.html#default_table_expiration_ms

Example
*******

Given a pandas DataFrame

.. list-table::
   :widths: 30 30 30
   :header-rows: 1

   * - foo
     - weight
     - prediction_date
   * - bar
     - 23
     - 20190301
   * - my
     - 42
     - 20190301

and its table definition

.. code-block:: python

    from bquest.tables import BQTableDefinitionBuilder

    table_def_builder = BQTableDefinitionBuilder(GOOGLE_PROJECT_ID, dataset="bquest", location="EU")
    table_definition = table_def_builder.from_df("abc.feed_latest", df)

you can use the config file *./abc/config.py*

.. code-block:: json-object

    {
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
    }

and the runner

.. code-block:: python

    from bquest.runner import BQConfigFileRunner, BQConfigRunner

    runner = BQConfigFileRunner(
        BQConfigRunner(bq_client, bq_executor_func),
        "config/bq_config",
    )

    result_df = runner.run_config(
        "20190301",
        "20190308",
        [table_definition],
        "abc/config.py",
        templating_vars={"THRESHOLD": "30"},
    )

to assert the result table

.. code-block:: python

    assert result_df.shape == (1, 2)
    assert result_df.iloc[0]["foo"] == "my"

Testing
*******

For the actual testing bquest relies on an accessible BigQuery project which can be configured
with the gcloud_ client. The corresponding ``GOOGLE_PROJECT_ID`` is extracted from this project
and used with pandas-gbq_ to write temporary tables to the bquest dataset that has to be pre-
configured before testing on that project.

For Github CI we have configured an identity provider in our testing project which allows
only core members of this repository to access the testing projects' resources.

.. _gcloud: https://cloud.google.com/sdk/docs/install?hl=de
.. _pandas-gbq: https://github.com/googleapis/python-bigquery-pandas

Important Links
***************

- Full documentation: https://ottogroup.github.io/bquest/
