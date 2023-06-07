""" Helpers for dealing with pandas.DataFrames """
from typing import Any

import numpy as np
from pandas import DataFrame
from pandas import testing as pd_test


def standardize_frame_numerics(df: DataFrame, float_precision: int = 2) -> DataFrame:
    """Standardizes numerics inside a dataframe to facilitate comparison between
     dataframes with respect to meaningful differences.

    Arguments:
        df -- Pandas dataframe to be standardized
        float_precision -- level of precision for rounding floats
    """
    df = df.round(float_precision)
    for col in df.columns:
        if df[col].dtype != int:
            continue
        df[col] = df[col].astype(float)

    return df.fillna(value=np.nan).reset_index(drop=True)


def _fix_integer_dtypes(df: DataFrame) -> None:
    """Since some version, pandas can not infer in assert_frame_equals Int64 as int64

    Arguments:
        df -- A dataframe, that will be have all int types as int64
    """
    df[df.select_dtypes("Int64").columns] = df[
        df.select_dtypes("Int64").columns
    ].astype("Int64")


def assert_frame_equal(left: DataFrame, right: DataFrame, **kwargs: Any) -> None:
    """Asserts that two dataframes are equal regardless of their order of rows

    Arguments:
        left -- A dataframe, usually the result of a function under test.
        right -- Another dataframe, usually what we expect in a test.

    Keyword Arguments:
        Keyword arguments of pandas.testing.assert_frame_equal
    <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.testing.assert_frame_equal.html>
    """

    _fix_integer_dtypes(left)
    _fix_integer_dtypes(right)

    left_sorted = (
        left[sorted(left.columns)]
        .sort_values(sorted(left.columns))
        .reset_index(drop=True)
    )
    right_sorted = (
        right[sorted(right.columns)]
        .sort_values(sorted(right.columns))
        .reset_index(drop=True)
    )

    pd_test.assert_frame_equal(left_sorted, right_sorted, **kwargs)
