import pytest
from google.cloud import bigquery as bq

from bquest.tables import BQTableDefinitionBuilder
from tests.integration import GOOGLE_PROJECT_ID


@pytest.fixture
def bq_location():
    return "europe-west1"


@pytest.fixture
def bq_client(bq_location):
    return bq.Client(project=GOOGLE_PROJECT_ID, location=bq_location)


@pytest.fixture
def table_def_builder(bq_location):
    return BQTableDefinitionBuilder(GOOGLE_PROJECT_ID, dataset="bquest", location=bq_location)
