# BQuest

BQuest is a library for testing BigQuery queries in Python.

* Use BQuest in combination with your favorite testing framework (e.g. pytest).
* Create temporary test tables from [JSON](https://cloud.google.com/bigquery/docs/loading-data) or [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).
* Run BQ configurations and plain SQL queries on your test tables and check the result.

## Installation

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


## Example

We recommend to look at the BQuest integration tests.


## Notes and Best Practices

* It's good practice to define an [expiration time](https://www.terraform.io/docs/providers/google/r/bigquery_dataset.html#default_table_expiration_ms) for tables in BQuest datasets.