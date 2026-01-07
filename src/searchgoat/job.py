"""Search job representation and status tracking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

import pandas as pd

if TYPE_CHECKING:
    from searchgoat.client import SearchClient


class JobStatus(str, Enum):
    """
    Possible states of a search job.
    
    Attributes:
        NEW: Job accepted, not yet running
        QUEUED: Job is queued waiting for resources
        RUNNING: Search in progress
        COMPLETED: Results ready for retrieval
        FAILED: Search encountered an error
        CANCELED: Search was stopped before completion
    """
    NEW = "new"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class SearchJob:
    """
    Represents a Cribl Search job.
    
    Use this for fine-grained control over job execution.
    For simple queries, use SearchClient.query() instead.
    
    Attributes:
        id: Unique job identifier
        query: The search query string
        status: Current job status
        record_count: Number of records (populated after completion)
    
    Example:
        job = client.submit('cribl dataset="logs"', earliest="-1h")
        job.wait()
        df = job.to_dataframe()
        job.save("results.parquet")
    """
    
    id: str
    query: str
    status: JobStatus = JobStatus.NEW
    record_count: Optional[int] = None
    _client: Optional["SearchClient"] = field(default=None, repr=False)
    
    def wait(self, timeout: float = 300.0) -> "SearchJob":
        """
        Wait for job completion (sync).
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            Self for method chaining
            
        Raises:
            JobTimeoutError: If timeout exceeded
            JobFailedError: If job failed
        """
        import asyncio
        asyncio.run(self.wait_async(timeout))
        return self
    
    async def wait_async(self, timeout: float = 300.0) -> "SearchJob":
        """
        Wait for job completion (async).
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            Self for method chaining
        """
        if self._client is None:
            raise RuntimeError("Job not associated with a client")
        await self._client._wait_for_job(self, timeout=timeout)
        return self
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Retrieve results as a DataFrame (sync).
        
        Returns:
            pandas DataFrame with query results
        """
        import asyncio
        return asyncio.run(self.to_dataframe_async())
    
    async def to_dataframe_async(self) -> pd.DataFrame:
        """
        Retrieve results as a DataFrame (async).
        
        Returns:
            pandas DataFrame with query results
        """
        if self._client is None:
            raise RuntimeError("Job not associated with a client")
        return await self._client._get_results_as_dataframe(self)
    
    def save(self, path: str) -> str:
        """
        Save results to file (sync).
        
        Args:
            path: Output path (.parquet or .csv)
            
        Returns:
            The path where file was saved
        """
        import asyncio
        return asyncio.run(self.save_async(path))
    
    async def save_async(self, path: str) -> str:
        """
        Save results to file (async).
        
        Supports:
        - .parquet (recommended for large datasets)
        - .csv (for universal compatibility)
        
        Args:
            path: Output path with extension
            
        Returns:
            The path where file was saved
            
        Raises:
            ValueError: If file extension not supported
        """
        df = await self.to_dataframe_async()
        
        if path.endswith(".parquet"):
            df.to_parquet(path, index=False)
        elif path.endswith(".csv"):
            df.to_csv(path, index=False)
        else:
            raise ValueError(f"Unsupported format. Use .parquet or .csv, got: {path}")
        
        return path
