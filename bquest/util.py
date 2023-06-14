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
    try:
        return sqlvalidator.parse(string).is_valid()
    except Exception:
        # assume that if parsing fails at some point the string doesn't follow exact SQL syntax
        return False
