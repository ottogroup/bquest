# Getting started

In the project where you want to run bquest tests install bquest via PyPi:

```bash
    pip install bquest
```

We advise you to create a bquest dataset in your Google Cloud projects BigQuery instance 
so that your regular datasets are not spammed with bquest tables:

```yaml
    resource "google_bigquery_dataset" "bquest" {
      dataset_id    = "bquest"
      friendly_name = "bquest"
      description   = "Source tables for bquest tests"
      location      = "EU"
      default_table_expiration_ms = 3600000
    }
```

***
<span style="color:red">WARNING: SET A DEFAULT EXPIRATION TIME SO THAT BQUEST GENERATED TABLES ARE AUTOMATICALLY REMOVED AFTER SOME TIME</span>
***