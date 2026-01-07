"""Tests for searchgoat.job module."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import pandas as pd

from searchgoat.job import JobStatus, SearchJob


class TestJobStatus:
    """Tests for JobStatus enum."""
    
    def test_status_values(self):
        """JobStatus has expected values."""
        assert JobStatus.NEW.value == "new"
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELED.value == "canceled"
    
    def test_status_from_string(self):
        """JobStatus can be created from string."""
        assert JobStatus("completed") == JobStatus.COMPLETED
        assert JobStatus("running") == JobStatus.RUNNING
        assert JobStatus("queued") == JobStatus.QUEUED


class TestSearchJob:
    """Tests for SearchJob dataclass."""
    
    def test_job_creation(self):
        """SearchJob can be created with required fields."""
        job = SearchJob(id="job-123", query="test query")
        
        assert job.id == "job-123"
        assert job.query == "test query"
        assert job.status == JobStatus.NEW
        assert job.record_count is None
    
    def test_job_repr_hides_client(self):
        """SearchJob repr doesn't expose client."""
        mock_client = MagicMock()
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        
        repr_str = repr(job)
        assert "job-123" in repr_str
        assert "_client" not in repr_str
    
    @pytest.mark.asyncio
    async def test_wait_async_delegates_to_client(self):
        """wait_async calls client's _wait_for_job."""
        mock_client = MagicMock()
        mock_client._wait_for_job = AsyncMock()
        
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        await job.wait_async(timeout=100)
        
        mock_client._wait_for_job.assert_called_once_with(job, timeout=100)
    
    @pytest.mark.asyncio
    async def test_to_dataframe_async_returns_dataframe(self):
        """to_dataframe_async returns DataFrame from client."""
        mock_client = MagicMock()
        expected_df = pd.DataFrame({"col": [1, 2, 3]})
        mock_client._get_results_as_dataframe = AsyncMock(return_value=expected_df)
        
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        result = await job.to_dataframe_async()
        
        assert result.equals(expected_df)
    
    @pytest.mark.asyncio
    async def test_save_async_parquet(self, tmp_path):
        """save_async writes parquet file."""
        mock_client = MagicMock()
        mock_client._get_results_as_dataframe = AsyncMock(
            return_value=pd.DataFrame({"col": [1, 2, 3]})
        )
        
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        path = str(tmp_path / "test.parquet")
        
        result = await job.save_async(path)
        
        assert result == path
        loaded = pd.read_parquet(path)
        assert len(loaded) == 3
    
    @pytest.mark.asyncio
    async def test_save_async_csv(self, tmp_path):
        """save_async writes CSV file."""
        mock_client = MagicMock()
        mock_client._get_results_as_dataframe = AsyncMock(
            return_value=pd.DataFrame({"col": [1, 2, 3]})
        )
        
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        path = str(tmp_path / "test.csv")
        
        result = await job.save_async(path)
        
        assert result == path
        loaded = pd.read_csv(path)
        assert len(loaded) == 3
    
    @pytest.mark.asyncio
    async def test_save_async_invalid_extension(self):
        """save_async raises ValueError for invalid extension."""
        mock_client = MagicMock()
        mock_client._get_results_as_dataframe = AsyncMock(
            return_value=pd.DataFrame({"col": [1, 2, 3]})
        )
        
        job = SearchJob(id="job-123", query="test", _client=mock_client)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            await job.save_async("test.json")
