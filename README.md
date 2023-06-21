![BQuest Logo](https://raw.githubusercontent.com/ottogroup/bquest/main/docs/assets/logo.svg)

# BQuest

Effortlessly validate and test your Google BigQuery queries with the power of pandas DataFrames in Python.

We would like to thank [Mike Czech](https://github.com/mikeczech) who is the original inventor of bquest!

**Warning**

This library is a work in progress!

Breaking changes should be expected until a 1.0 release, so version pinning is recommended.

[![CI: Overall outcome](https://github.com/ottogroup/bquest/workflows/Tests/badge.svg)](https://github.com/ottogroup/bquest/actions?workflow=Tests)
[![CD: gh-pages documentation](https://github.com/ottogroup/bquest/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages)](https://github.com/ottogroup/bquest/actions/workflows/pages/pages-build-deployment)
[![PyPI version](https://img.shields.io/pypi/v/bquest.svg)](https://pypi.org/project/bquest/)
[![Project status (alpha, beta, stable)](https://img.shields.io/pypi/status/bquest.svg)](https://pypi.python.org/pypi/bquest/)
[![PyPI downloads](https://static.pepy.tech/personalized-badge/bquest?period=month&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20downloads/month)](https://pepy.tech/project/bquest)
[![Project license](https://img.shields.io/github/license/ottogroup/bquest)](https://github.com/ottogroup/bquest/blob/main/LICENSE)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/bquest.svg)](https://pypi.python.org/pypi/bquest/)
[![Documentation: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

* Use BQuest in combination with your favorite testing framework (e.g. pytest).
* Create temporary test tables from [JSON](https://cloud.google.com/bigquery/docs/loading-data) or
[pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).
* Run BQ configurations and plain SQL queries on your test tables and check the result.

## Installation

Via PyPi (standard):

```bash
    pip install bquest
```

Via Github (most recent):

```bash
    pip install git+https://github.com/ottogroup/bquest
```

BQuest also requires a dedicated BigQuery dataset for storing test tables, e.g.

```yaml
    resource "google_bigquery_dataset" "bquest" {
      dataset_id    = "bquest"
      friendly_name = "bquest"
      description   = "Source tables for bquest tests"
      location      = "EU"
      default_table_expiration_ms = 3600000
    }
```

We recommend setting an [expiration time](https://www.terraform.io/docs/providers/google/r/bigquery_dataset.html#default_table_expiration_ms) for tables in the bquest dataset to assure removal of those test tables upon
test execution.

## Example

Given a ``pandas.DataFrame``

| foo    | weight | prediction_date   |
|--------|--------|-------------------|
| bar    | 23     | 20190301          |
| my     | 42     | 20190301          |

and its table definition

```python
    from bquest.tables import BQTableDefinitionBuilder

    table_def_builder = BQTableDefinitionBuilder(GOOGLE_PROJECT_ID, dataset="bquest", location="EU")
    table_definition = table_def_builder.from_df("abc.feed_latest", df)
```

you can use the config file ``*./abc/config.py*``

```json-object
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
```

and the runner

```python
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
```

to assert the result table

```python
    assert result_df.shape == (1, 2)
    assert result_df.iloc[0]["foo"] == "my"
```

## Testing

For the actual testing bquest relies on an accessible BigQuery project which can be configured
with the [gcloud](https://cloud.google.com/sdk/docs/install?hl=de) client. The corresponding 
``GOOGLE_PROJECT_ID`` is extracted from this project
and used with [pandas-gbq](https://github.com/googleapis/python-bigquery-pandas) to write temporary tables to the bquest dataset that has to be pre-
configured before testing on that project.

For Github CI we have configured an identity provider in our testing project which allows
only core members of this repository to access the testing projects' resources.

## Important Links

- Full documentation: https://ottogroup.github.io/bquest/
