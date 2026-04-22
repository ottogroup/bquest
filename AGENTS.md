# BQuest Agent Guide

## Project Overview

**BQuest** (v0.5.8, Beta) is a Python library for validating and testing Google BigQuery queries using pandas DataFrames. It creates temporary test tables in BigQuery from JSON/DataFrame data, executes queries against them, and validates results without touching production tables.

**Status**: Beta — breaking changes expected until 1.0; pin your version.

## Tech Stack

- **Python** 3.10–3.12
- **Package manager**: `uv` (>=0.6.0)
- **Build**: `hatchling`
- **Key deps**: `google-cloud-bigquery[bqstorage,pandas]>=3.8`, `pandas>=2.0`, `pandas-gbq>=0.19`, `sqlvalidator>=0.0.20`
- **Dev tools**: `ruff>=0.2.2` (line length 120), `mypy>=1.3.0` (strict), `pytest>=7.3.1`, `poethepoet` (task runner), `pip-audit`, `creosote`, `zizmor`
- **Docs**: MkDocs Material + mkdocstrings, versioned with `mike`

## Repository Structure

```
bquest/
├── bquest/
│   ├── tables.py      # BQTable, BQTableDefinition, BQTableDataframeDefinition, BQTableJsonDefinition, BQTableDefinitionBuilder
│   ├── runner.py      # BaseRunner, BQConfigRunner, BQConfigFileRunner, BQConfigSubstitutor, SQLRunner, SQLFileRunner
│   ├── dataframe.py   # standardize_frame_numerics(), assert_frame_equal() (order-independent)
│   └── util.py        # is_sql() — detect SQL in strings
├── tests/
│   ├── unit/          # No external deps (mocked BigQuery)
│   └── integration/   # Real BigQuery (requires auth + bquest dataset)
├── docs/              # MkDocs source
├── pyproject.toml
└── uv.lock
```

## Local Setup

```bash
uv sync
gcloud auth application-default login   # For integration tests
```

**BigQuery setup**: Create dataset `bquest` in EU, set table expiration ~1 hour.

## Commands (via `poe`)

```bash
uv run poe lint              # ruff check
uv run poe format            # ruff format --fix
uv run poe type              # mypy strict
uv run poe test_unit         # Unit tests (fast, no BQ needed)
uv run poe test_integration  # Integration tests (requires BQ auth)
uv run poe test              # Both
uv run poe check_vulnerable_dependencies
uv run poe check_unused_dependencies
uv run poe check_githubactions
```

## Architecture & Key Classes

### Tables (`tables.py`)
- **`BQTable`** — wraps a BQ table ref; `load_to_bq()`, `to_df()`, `delete()`
- **`BQTableDataframeDefinition`** — create table from pandas DataFrame (via `pandas_gbq.to_gbq`)
- **`BQTableJsonDefinition`** — create table from JSON rows
- **`BQTableDefinitionBuilder`** — factory; use this instead of direct instantiation

### Runners (`runner.py`)
- **`BQConfigRunner`** — execute BQ config dict
- **`BQConfigFileRunner`** — load config from `.py` file via `ast.literal_eval`
- **`BQConfigSubstitutor`** — maps original table IDs → test table IDs
- **`SQLRunner`** — direct SQL with string replacements and parameter substitution
- **`SQLFileRunner`** — file-based SQL runner

### DataFrame utils (`dataframe.py`)
- **`standardize_frame_numerics()`** — rounds floats to 2 decimals, converts Int64→float64
- **`assert_frame_equal()`** — order-independent comparison (sorts columns + rows); use for test assertions

## Conventions

### Test Table Naming
`{original_table_id}_{uuid}` — special chars (`.{}$-`) → `_`

### BQConfig Dict Format
```python
{
    "query": "SELECT ...",
    "source_tables": {"key": "schema.table"},
    "feature_table_name": "schema.result_table",
    "start_date": "date_column_name",
}
```

### Code Style
- Line length: 120 (ruff), strict mypy, Ruff rules: S, B, A, C4, ERA, YTT, I, T20, E, W, F, RET
- `@pytest.mark.unit` — no external deps; `@pytest.mark.integration` — requires BigQuery

## CI/CD

- **`tests.yml`**: Python 3.10–3.12 matrix; integration tests skip on fork PRs
- **`code-checks.yml`**: ruff, pip-audit, creosote, zizmor
- **`type.yml`**: mypy strict; **`coverage.yml`**: Codecov 75% target
- **`release.yml`**: `uv build` → docs versioned with `mike` → `uv publish` (OIDC trusted publishing)
- Auth: Workload Identity Federation (no static keys)

## Key Gotchas

1. **Float precision**: Always use `standardize_frame_numerics()` + `assert_frame_equal()` — raw floats cause flaky tests
2. **Curly braces in SQL**: Can't use `{substitutions}` if query contains `{}` (e.g., regex). Use `string_replacements` instead
3. **Dataset must pre-exist**: `bquest` dataset won't be auto-created
4. **Location mismatch**: Pass `location` to `BQTableDefinitionBuilder` if not EU
5. **`pandas-gbq` exempt from creosote**: Dynamically imported; false positive for "unused"
6. **`BQConfigFileRunner` uses `ast.literal_eval`**: Config files can only contain Python literals
7. **Partition filter**: `to_df()` temporarily disables `requirePartitionFilter` for test tables
