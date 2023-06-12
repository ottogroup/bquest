""" Helpers for dealing with pandas.DataFrames """
from typing import Any

import numpy as np
import pandas
import pandas as pd
from pandas import testing as pd_test

POSSIBLE_INTEGER_DTYPES = (int, pd.Int8Dtype, pd.Int16Dtype, pd.Int32Dtype, pd.Int64Dtype)


def standardize_frame_numerics(df: pandas.DataFrame, float_precision: int = 2) -> pandas.DataFrame:
    """Standardizes numerics inside a dataframe to facilitate comparison between
     dataframes with respect to meaningful differences.

    Args:
        df: Pandas dataframe to be standardized
        float_precision: level of precision for rounding floats

    Returns:
        Standardized dataframe
    """
    df = df.round(float_precision)

    integer_columns = df.select_dtypes(POSSIBLE_INTEGER_DTYPES).columns

    for col in integer_columns:
        df[col] = df[col].astype(float)

    return df.fillna(value=np.nan).reset_index(drop=True)


def _fix_integer_dtypes(df: pandas.DataFrame) -> None:
    """Since some version, pandas can not infer in assert_frame_equals Int64 as int64

    Args:
        df: A dataframe, that will behave all int types as int64
    """
    df[df.select_dtypes("Int64").columns] = df[df.select_dtypes("Int64").columns].astype("Int64")


def assert_frame_equal(left: pandas.DataFrame, right: pandas.DataFrame, **kwargs: Any) -> None:
    """Asserts that two dataframes are equal regardless of their order of rows

    Args:
        left: A dataframe, usually the result of a function under test
        right: Another dataframe, usually what we expect in a test
        **kwargs: Keyword arguments of pandas.testing.assert_frame_equal <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.testing.assert_frame_equal.html>
    """

    _fix_integer_dtypes(left)
    _fix_integer_dtypes(right)

    left_sorted = left[sorted(left.columns)].sort_values(sorted(left.columns)).reset_index(drop=True)
    right_sorted = right[sorted(right.columns)].sort_values(sorted(right.columns)).reset_index(drop=True)

    pd_test.assert_frame_equal(left_sorted, right_sorted, **kwargs)
