"""Tests for searchgoat.exceptions module."""

import pytest

from searchgoat.exceptions import (
    SearchGoatError,
    AuthenticationError,
    QuerySyntaxError,
    JobTimeoutError,
    JobFailedError,
    RateLimitError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""
    
    def test_all_exceptions_inherit_from_searchgoat_error(self):
        """All custom exceptions inherit from SearchGoatError."""
        exceptions = [
            AuthenticationError,
            QuerySyntaxError,
            JobTimeoutError,
            JobFailedError,
            RateLimitError,
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, SearchGoatError)
    
    def test_searchgoat_error_inherits_from_exception(self):
        """SearchGoatError inherits from Exception."""
        assert issubclass(SearchGoatError, Exception)
    
    def test_catching_base_catches_all(self):
        """Catching SearchGoatError catches all custom exceptions."""
        for exc_class in [AuthenticationError, QuerySyntaxError, JobTimeoutError]:
            try:
                raise exc_class("test")
            except SearchGoatError:
                pass  # Expected


class TestJobFailedError:
    """Tests for JobFailedError."""
    
    def test_stores_job_id(self):
        """JobFailedError stores job_id."""
        error = JobFailedError("Job failed", job_id="job-123")
        assert error.job_id == "job-123"
    
    def test_job_id_defaults_to_none(self):
        """job_id defaults to None."""
        error = JobFailedError("Job failed")
        assert error.job_id is None


class TestRateLimitError:
    """Tests for RateLimitError."""
    
    def test_stores_retry_after(self):
        """RateLimitError stores retry_after."""
        error = RateLimitError("Rate limited", retry_after=120)
        assert error.retry_after == 120
    
    def test_retry_after_defaults_to_60(self):
        """retry_after defaults to 60 seconds."""
        error = RateLimitError("Rate limited")
        assert error.retry_after == 60
