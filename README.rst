.. image:: https://raw.githubusercontent.com/ottogroup/bquest/main/docs/assets/logo.svg
    :alt: BQuest Logo

BQuest
######

Effortlessly validate and test your Google BigQuery queries with the power of pandas DataFrames in Python.

**Warning**

This library is a work in progress!

Breaking changes should be expected until a 1.0 release, so version pinning is recommended.

Overview
********

* Use BQuest in combination with your favorite testing framework (e.g. pytest).
* Create temporary test tables from [JSON](https://cloud.google.com/bigquery/docs/loading-data) or [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).
* Run BQ configurations and plain SQL queries on your test tables and check the result.

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

TBD