"""SearchClient - the main interface for querying Cribl Search."""

import asyncio
from typing import Optional

import httpx
import pandas as pd

from searchgoat.auth import TokenManager
from searchgoat.config import CriblSettings
from searchgoat.exceptions import (
    JobFailedError,
    JobTimeoutError,
    QuerySyntaxError,
    RateLimitError,
)
from searchgoat.job import JobStatus, SearchJob
from searchgoat.pagination import paginate_results
from searchgoat._utils.dataframe import records_to_dataframe


class SearchClient:
    """
    Client for querying Cribl Search.
    
    Provides both sync and async methods for executing searches
    and retrieving results as pandas DataFrames.
    
    Configuration is loaded from environment variables:
    - CRIBL_CLIENT_ID
    - CRIBL_CLIENT_SECRET
    - CRIBL_ORG_ID
    - CRIBL_WORKSPACE
    
    Example (simple query):
        from searchgoat import SearchClient
        
        client = SearchClient()
        df = client.query('cribl dataset="logs" | limit 1000', earliest="-24h")
        print(df.head())
    
    Example (job-based workflow):
        job = client.submit('cribl dataset="logs"', earliest="-7d")
        job.wait()
        df = job.to_dataframe()
        job.save("results.parquet")
    """
    
    # Job polling configuration
    _DEFAULT_POLL_INTERVAL = 2.0
    
    def __init__(self, settings: Optional[CriblSettings] = None):
        """
        Initialize SearchClient.
        
        Args:
            settings: Optional CriblSettings. If not provided,
                     loads from environment variables.
        """
        self._settings = settings or CriblSettings()
        self._token_manager = TokenManager(self._settings)
    
    # -------------------------------------------------------------------------
    # Public Sync API
    # -------------------------------------------------------------------------
    
    def query(
        self,
        query: str,
        earliest: str = "-1h",
        latest: str = "now",
        timeout: float = 300.0,
    ) -> pd.DataFrame:
        """
        Execute a query and return results as a DataFrame.
        
        This is the simplest way to run a search. For more control,
        use submit() and the job-based workflow.
        
        Args:
            query: Cribl Search query (must start with 'cribl dataset="..."')
            earliest: Start of time range (default: "-1h")
            latest: End of time range (default: "now")
            timeout: Maximum seconds to wait for results (default: 300)
            
        Returns:
            pandas DataFrame with query results
            
        Raises:
            AuthenticationError: If credentials are invalid
            QuerySyntaxError: If query syntax is invalid
            JobTimeoutError: If query exceeds timeout
            JobFailedError: If query execution fails
            
        Example:
            df = client.query(
                'cribl dataset="logs" | where level="ERROR" | limit 100',
                earliest="-24h"
            )
            print(df.head())
        """
        return asyncio.run(self.query_async(query, earliest, latest, timeout))
    
    def submit(
        self,
        query: str,
        earliest: str = "-1h",
        latest: str = "now",
    ) -> SearchJob:
        """
        Submit a search job without waiting for results.
        
        Use this for fine-grained control over job execution.
        Call job.wait() to wait for completion, then job.to_dataframe()
        to retrieve results.
        
        Args:
            query: Cribl Search query
            earliest: Start of time range
            latest: End of time range
            
        Returns:
            SearchJob instance for tracking and retrieving results
            
        Example:
            job = client.submit('cribl dataset="logs"', earliest="-7d")
            print(f"Job ID: {job.id}")
            job.wait(timeout=600)
            df = job.to_dataframe()
        """
        return asyncio.run(self.submit_async(query, earliest, latest))
    
    # -------------------------------------------------------------------------
    # Public Async API
    # -------------------------------------------------------------------------
    
    async def query_async(
        self,
        query: str,
        earliest: str = "-1h",
        latest: str = "now",
        timeout: float = 300.0,
    ) -> pd.DataFrame:
        """
        Async version of query().
        
        Args:
            query: Cribl Search query
            earliest: Start of time range
            latest: End of time range
            timeout: Maximum seconds to wait
            
        Returns:
            pandas DataFrame with query results
        """
        job = await self.submit_async(query, earliest, latest)
        await self._wait_for_job(job, poll_interval=2.0, timeout=timeout)
        return await self._get_results_as_dataframe(job)
    
    async def submit_async(
        self,
        query: str,
        earliest: str = "-1h",
        latest: str = "now",
    ) -> SearchJob:
        """
        Async version of submit().
        
        Args:
            query: Cribl Search query
            earliest: Start of time range
            latest: End of time range
            
        Returns:
            SearchJob instance
        """
        async with httpx.AsyncClient() as client:
            headers = await self._get_headers(client)
            
            payload = {
                "query": query,
                "earliest": earliest,
                "latest": latest,
                "sampleRate": 1,
            }
            
            url = f"{self._settings.api_base_url}/search/jobs"
            
            try:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 400:
                    raise QuerySyntaxError(f"Invalid query: {response.text}")
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
                
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise QuerySyntaxError(f"Query failed: {e}") from e
            
            data = response.json()
            job_id = data["items"][0]["id"]
            
            return SearchJob(
                id=job_id,
                query=query,
                status=JobStatus.NEW,
                _client=self,
            )
    
    # -------------------------------------------------------------------------
    # Internal Methods (used by SearchJob)
    # -------------------------------------------------------------------------
    
    async def _wait_for_job(
        self,
        job: SearchJob,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> None:
        """
        Poll job status until completion.
        
        Updates job.status and job.record_count in place.
        """
        import time
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            url = f"{self._settings.api_base_url}/search/jobs/{job.id}/status"
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise JobTimeoutError(
                        f"Job {job.id} did not complete within {timeout} seconds"
                    )
                
                headers = await self._get_headers(client)
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                status_str = data["items"][0]["status"]
                job.status = JobStatus(status_str)
                
                if job.status == JobStatus.COMPLETED:
                    job.record_count = data["items"][0].get("numEvents", 0)
                    return
                
                if job.status == JobStatus.FAILED:
                    error_msg = data["items"][0].get("error", "Unknown error")
                    raise JobFailedError(
                        f"Job {job.id} failed: {error_msg}",
                        job_id=job.id
                    )
                
                if job.status == JobStatus.CANCELED:
                    raise JobFailedError(
                        f"Job {job.id} was canceled",
                        job_id=job.id
                    )
                
                await asyncio.sleep(poll_interval)
    
    async def _get_results_as_dataframe(self, job: SearchJob) -> pd.DataFrame:
        """Retrieve job results and convert to DataFrame."""
        async with httpx.AsyncClient() as client:
            headers = await self._get_headers(client)
            url = f"{self._settings.api_base_url}/search/jobs/{job.id}/results"
            
            records = []
            async for record in paginate_results(client, url, headers):
                records.append(record)
            
            return records_to_dataframe(records)
    
    async def _get_headers(self, client: httpx.AsyncClient) -> dict:
        """Get request headers with valid auth token."""
        token = await self._token_manager.get_token(client)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
