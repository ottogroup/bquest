import pytest

from bquest.util import is_sql

pytestmark = pytest.mark.unit


def test_is_sql_negatives():
    """Test is_sql negatives"""
    assert not is_sql("table")
    assert not is_sql("project.dataset.table")
    assert not is_sql("* FROM project.dataset.table")
    assert not is_sql("SELECT * FROM")
    assert not is_sql("SELECT FROM project.dataset.table")


def test_is_sql_positives():
    """Test is_sql positives"""
    query = "SELECT * FROM project.dataset.table"
    assert is_sql(query)
    super_complex_query = """
        SELECT
          t1.customer_id,
          t1.order_id,
          t1.product_id,
          t1.quantity,
          t1.unit_price,
          t1.order_date,
          t1.order_status,
          t2.product_name,
          t2.category_id,
          t3.category_name
        FROM
          orders AS t1
          JOIN products AS t2 ON t1.product_id = t2.product_id
          JOIN categories AS t3 ON t2.category_id = t3.category_id
        WHERE
          t1.order_status = 'Shipped'
          AND t2.category_id IN (1, 2, 3)
          AND t1.order_date BETWEEN '2022-01-01' AND '2022-12-31'
        ORDER BY
          t1.customer_id,
          t1.order_id,
          t1.order_date
    """
    assert is_sql(super_complex_query)
