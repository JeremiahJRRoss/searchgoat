"""Tests for searchgoat.pagination module."""

import json
import pytest
import respx
from httpx import Response

from searchgoat.pagination import paginate_results


class TestPaginateResults:
    """Tests for paginate_results function."""
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_yields_records_from_single_page(self):
        """Single page of results yields all records."""
        ndjson = (
            '{"totalEventCount": 2}\n'
            '{"_time": 1, "message": "log1"}\n'
            '{"_time": 2, "message": "log2"}\n'
        )
        
        respx.get("https://api.test/results").mock(
            return_value=Response(200, text=ndjson)
        )
        
        import httpx
        async with httpx.AsyncClient() as client:
            records = []
            async for record in paginate_results(
                client, "https://api.test/results", {}
            ):
                records.append(record)
        
        assert len(records) == 2
        assert records[0]["message"] == "log1"
        assert records[1]["message"] == "log2"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_paginates_across_multiple_pages(self):
        """Multiple pages are fetched when total exceeds page size."""
        page1 = '{"totalEventCount": 3}\n{"id": 1}\n{"id": 2}\n'
        page2 = '{"totalEventCount": 3}\n{"id": 3}\n'
        
        route = respx.get("https://api.test/results")
        route.side_effect = [
            Response(200, text=page1),
            Response(200, text=page2),
        ]
        
        import httpx
        async with httpx.AsyncClient() as client:
            records = []
            async for record in paginate_results(
                client, "https://api.test/results", {}, page_size=2
            ):
                records.append(record)
        
        assert len(records) == 3
        assert [r["id"] for r in records] == [1, 2, 3]
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_handles_empty_results(self):
        """Empty results yield nothing."""
        ndjson = '{"totalEventCount": 0}\n'
        
        respx.get("https://api.test/results").mock(
            return_value=Response(200, text=ndjson)
        )
        
        import httpx
        async with httpx.AsyncClient() as client:
            records = []
            async for record in paginate_results(
                client, "https://api.test/results", {}
            ):
                records.append(record)
        
        assert len(records) == 0
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_skips_blank_lines(self):
        """Blank lines in NDJSON are skipped."""
        ndjson = '{"totalEventCount": 1}\n\n{"id": 1}\n\n'
        
        respx.get("https://api.test/results").mock(
            return_value=Response(200, text=ndjson)
        )
        
        import httpx
        async with httpx.AsyncClient() as client:
            records = []
            async for record in paginate_results(
                client, "https://api.test/results", {}
            ):
                records.append(record)
        
        assert len(records) == 1
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_includes_ndjson_accept_header(self):
        """Request includes NDJSON Accept header."""
        ndjson = '{"totalEventCount": 0}\n'
        
        route = respx.get("https://api.test/results").mock(
            return_value=Response(200, text=ndjson)
        )
        
        import httpx
        async with httpx.AsyncClient() as client:
            async for _ in paginate_results(
                client, "https://api.test/results", {"Authorization": "Bearer token"}
            ):
                pass
        
        assert route.calls[0].request.headers["Accept"] == "application/x-ndjson"
