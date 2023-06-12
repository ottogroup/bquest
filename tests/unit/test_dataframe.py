import pandas as pd
import pytest

from bquest.dataframe import assert_frame_equal, standardize_frame_numerics

pytestmark = pytest.mark.unit


class TestDataframeUtils:
    def test_standardize_frame_numerics(self) -> None:
        df_in = pd.DataFrame(
            {
                "hash": ["abc-999", "abc-888"],
                "date_id": ["20190402", "20190401"],
                "score": [0.8154768, 7.298],
                "value": [3, 5],
            }
        )

        df_out = pd.DataFrame(
            {
                "date_id": ["20190401", "20190402"],
                "hash": ["abc-888", "abc-999"],
                "score": [7.30, 0.82],
                "value": [5.0, 3.0],
            }
        )

        assert_frame_equal(standardize_frame_numerics(df_in), df_out)

    def test_order_of_columns_is_ignored(self) -> None:
        df_in = pd.DataFrame({"hash": ["abc-999"], "date_id": ["20190402"]})

        df_out = pd.DataFrame({"date_id": ["20190402"], "hash": ["abc-999"]})

        assert_frame_equal(df_in, df_out)

    def test_assert_frame_equal(self) -> None:
        left = pd.DataFrame(
            {
                "hash": ["abc-999", "abc-888"],
                "category_path": ["B", "A"],
            },
            index=[2, 3],
        )

        right = pd.DataFrame(
            {
                "hash": ["abc-888", "abc-999"],
                "category_path": ["A", "B"],
            },
            index=[1, 2],
        )

        assert_frame_equal(left, right)

    def test_assert_frame_equal_recognizes_dfs_that_are_different(self) -> None:
        left = pd.DataFrame(
            {
                "hash": ["abc-999", "abc-887"],
                "category_path": ["B", "A"],
            },
            index=[2, 3],
        )

        right = pd.DataFrame(
            {
                "hash": ["abc-888", "abc-999"],
                "category_path": ["A", "B"],
            },
            index=[1, 2],
        )

        with pytest.raises(AssertionError) as _:
            assert_frame_equal(left, right)

    def test_assert_frame_equal_less_precise(self) -> None:
        a, b = 1.0, 10.0
        left = pd.DataFrame(
            {
                "hash": ["abc-999", "abc-888"],
                "category_path": ["B", "A"],
                "target": [b, a],
            },
            index=[2, 3],
        )

        right = pd.DataFrame(
            {
                "hash": ["abc-888", "abc-999"],
                "category_path": ["A", "B"],
                "target": [a * 1.0005, b * 1.0005],
            },
            index=[1, 2],
        )

        assert_frame_equal(left, right, rtol=1e-3)
        with pytest.raises(AssertionError):
            assert_frame_equal(left, right)

    def test_assert_frame_equal_dtype(self) -> None:
        left = pd.DataFrame(
            {
                "hash": ["abc-999", "abc-888"],
                "category_path": ["B", "A"],
                "target": [2.0, 1.0],
            },
            index=[2, 3],
        )

        right = pd.DataFrame(
            {
                "hash": ["abc-888", "abc-999"],
                "category_path": ["A", "B"],
                "target": [1, 2],
            },
            index=[1, 2],
        )

        assert_frame_equal(left, right, check_dtype=False)
        with pytest.raises(AssertionError):
            assert_frame_equal(left, right, check_dtype=True)
