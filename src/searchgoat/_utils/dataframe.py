"""DataFrame conversion utilities."""

from typing import Iterable

import pandas as pd


def records_to_dataframe(records: Iterable[dict]) -> pd.DataFrame:
    """
    Convert search result records to a pandas DataFrame.
    
    Handles:
    - Empty results (returns empty DataFrame)
    - _time column parsing (Unix epoch to datetime)
    - Mixed-type columns
    
    Args:
        records: Iterable of record dicts from search results
        
    Returns:
        pandas DataFrame with parsed timestamps
    """
    # Materialize generator if needed
    records_list = list(records)
    
    if not records_list:
        return pd.DataFrame()
    
    df = pd.DataFrame(records_list)
    
    # Parse _time column if present (Cribl uses Unix epoch seconds)
    if "_time" in df.columns and len(df) > 0:
        df["_time"] = pd.to_datetime(df["_time"], unit="s", utc=True)
    
    return df
