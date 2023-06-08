"""Utility functions for bquest"""
import sqlvalidator


def is_sql(string: str) -> bool:
    """
    Small function to test if string contains SQL syntax
    Args:
        string: string with potential SQL syntax

    Returns:
        bool if string contains SQL syntax
    """
    return sqlvalidator.parse(string).is_valid()
