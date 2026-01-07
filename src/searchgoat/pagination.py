"""Pagination helpers for streaming search results."""

import json
from typing import AsyncIterator

import httpx


async def paginate_results(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    page_size: int = 1000,
) -> AsyncIterator[dict]:
    """
    Stream paginated NDJSON results from Cribl Search.
    
    Handles offset-based pagination, yielding individual records
    as they're received. The first line of each response is metadata
    (skipped), subsequent lines are event records.
    
    Args:
        client: HTTP client with auth headers
        url: Results endpoint URL
        headers: Request headers (must include auth)
        page_size: Records per request (default: 1000)
        
    Yields:
        Individual event records as dicts
    """
    offset = 0
    total_count = None
    
    # Ensure we're requesting NDJSON format
    request_headers = {**headers, "Accept": "application/x-ndjson"}
    
    while True:
        params = {"limit": page_size, "offset": offset}
        response = await client.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        
        lines = response.text.strip().split("\n")
        if not lines:
            break
        
        # First line is metadata with total count
        metadata = json.loads(lines[0])
        total_count = metadata.get("totalEventCount", 0)
        
        # Remaining lines are events
        for line in lines[1:]:
            if line.strip():
                yield json.loads(line)
        
        offset += page_size
        
        # Stop when we've fetched all records
        if total_count is None or offset >= total_count:
            break
