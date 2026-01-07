"""Tests for searchgoat._utils.dataframe module."""

import pytest
import pandas as pd

from searchgoat._utils.dataframe import records_to_dataframe


class TestRecordsToDataframe:
    """Tests for records_to_dataframe function."""
    
    def test_converts_list_of_dicts(self):
        """List of dicts becomes DataFrame."""
        records = [
            {"a": 1, "b": "x"},
            {"a": 2, "b": "y"},
        ]
        
        df = records_to_dataframe(records)
        
        assert len(df) == 2
        assert list(df.columns) == ["a", "b"]
        assert df["a"].tolist() == [1, 2]
    
    def test_empty_list_returns_empty_dataframe(self):
        """Empty list returns empty DataFrame."""
        df = records_to_dataframe([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_parses_time_column(self):
        """_time column is parsed to datetime."""
        records = [
            {"_time": 1704067200, "msg": "test"},  # 2024-01-01 00:00:00 UTC
        ]
        
        df = records_to_dataframe(records)
        
        assert pd.api.types.is_datetime64_any_dtype(df["_time"])
        assert df["_time"].dt.year.iloc[0] == 2024
    
    def test_handles_missing_time_column(self):
        """Records without _time are handled."""
        records = [{"a": 1}, {"a": 2}]
        
        df = records_to_dataframe(records)
        
        assert "_time" not in df.columns
        assert len(df) == 2
    
    def test_handles_generator_input(self):
        """Generator input is materialized."""
        def gen():
            yield {"a": 1}
            yield {"a": 2}
        
        df = records_to_dataframe(gen())
        
        assert len(df) == 2
