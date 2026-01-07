"""Exception hierarchy for searchgoat."""


class SearchGoatError(Exception):
    """
    Base exception for all searchgoat errors.
    
    Catch this to handle any searchgoat-related error.
    """
    pass


class AuthenticationError(SearchGoatError):
    """
    OAuth2 authentication failed.
    
    Common causes:
    - Invalid client_id or client_secret
    - Expired or revoked credentials
    - Network connectivity to login.cribl.cloud
    """
    pass


class QuerySyntaxError(SearchGoatError):
    """
    Invalid query syntax.
    
    Queries must start with 'cribl dataset="..."'.
    Check Cribl Search documentation for valid operators.
    """
    pass


class JobTimeoutError(SearchGoatError):
    """
    Search job did not complete within timeout.
    
    Consider:
    - Narrowing the time range (earliest/latest)
    - Adding filters to reduce data volume
    - Adding '| limit N' to the query
    - Increasing the timeout parameter
    """
    pass


class JobFailedError(SearchGoatError):
    """
    Search job failed on the server.
    
    Attributes:
        job_id: The ID of the failed job (for debugging)
    """
    
    def __init__(self, message: str, job_id: str | None = None):
        super().__init__(message)
        self.job_id = job_id


class RateLimitError(SearchGoatError):
    """
    Too many requests to Cribl API.
    
    Attributes:
        retry_after: Seconds to wait before retrying (default: 60)
    """
    
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after
