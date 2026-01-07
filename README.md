# searchgoat

**Query Cribl Search, get DataFrames.**

searchgoat is a Python library for querying Cribl Search and returning results as pandas DataFrames. It's the standalone core module—no notebook-specific dependencies.

## Installation

```bash
pip install searchgoat
```

Or from source:

```bash
git clone https://github.com/hackish-pub/searchgoat.git
cd searchgoat
pip install -e .
```

## Quick Start

```python
from searchgoat import SearchClient

client = SearchClient()
df = client.query('cribl dataset="logs" | limit 1000', earliest="-24h")
print(df.head())
```

## Configuration

Set environment variables or create a `.env` file:

```bash
CRIBL_CLIENT_ID=your-client-id
CRIBL_CLIENT_SECRET=your-client-secret
CRIBL_ORG_ID=your-org-id
CRIBL_WORKSPACE=your-workspace
```

### Finding Your Credentials

1. **Client ID & Secret**: Cribl Cloud → ⚙️ → Organization Settings → API Credentials
2. **Org ID & Workspace**: From your URL `https://{workspace}-{org_id}.cribl.cloud`

## Usage

### Simple Query

```python
from searchgoat import SearchClient

client = SearchClient()

# Basic query
df = client.query('cribl dataset="logs" | limit 100', earliest="-1h")

# With time range
df = client.query(
    'cribl dataset="logs" | where level="ERROR"',
    earliest="-24h",
    latest="now"
)

# With longer timeout
df = client.query(
    'cribl dataset="logs" | limit 50000',
    earliest="-7d",
    timeout=600  # 10 minutes
)
```

### Job-Based Workflow

For more control over long-running queries:

```python
# Submit without waiting
job = client.submit('cribl dataset="logs"', earliest="-7d")
print(f"Job ID: {job.id}")

# Wait for completion
job.wait(timeout=600)
print(f"Status: {job.status}")
print(f"Records: {job.record_count}")

# Get results
df = job.to_dataframe()

# Save to file
job.save("results.parquet")  # or .csv
```

### Async Support

```python
import asyncio
from searchgoat import SearchClient

async def main():
    client = SearchClient()
    df = await client.query_async('cribl dataset="logs" | limit 100', earliest="-1h")
    print(df.head())

asyncio.run(main())
```

## Query Syntax

Queries must start with `cribl dataset="..."`:

```python
# Filter
df = client.query('cribl dataset="logs" | where host="web01"', earliest="-1h")

# Aggregate
df = client.query('cribl dataset="logs" | stats count() by level', earliest="-24h")

# Multiple pipes
df = client.query('''
    cribl dataset="logs" 
    | where level="ERROR" 
    | stats count() by host 
    | sort -count
''', earliest="-24h")
```

## Exceptions

```python
from searchgoat import (
    SearchGoatError,      # Base exception
    AuthenticationError,  # Invalid credentials
    QuerySyntaxError,     # Bad query
    JobTimeoutError,      # Query took too long
    JobFailedError,       # Server-side failure
    RateLimitError,       # Too many requests
)

try:
    df = client.query('cribl dataset="logs"', earliest="-1h")
except AuthenticationError:
    print("Check your credentials")
except QuerySyntaxError as e:
    print(f"Bad query: {e}")
except JobTimeoutError:
    print("Try a shorter time range or add | limit N")
```

## Related Packages

| Package | Use Case |
|---------|----------|
| **searchgoat** | Standalone Python scripts and applications |
| **searchgoat-jupyter** | Local Jupyter notebooks (includes setup automation) |
| **searchgoat-hex** | Hex.tech notebooks (explicit credential passing) |

## License

Apache 2.0

---

*Part of the hackish.pub project family. 🐐*
