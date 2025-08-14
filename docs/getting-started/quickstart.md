# Quick Start

This guide will help you get started with the Data Sources Manager quickly.

## Basic Usage

Once you've [installed](installation.md) the Data Sources Manager, you can start using it right away.

### Browsing Available Sources

All data sources are stored as JSON files in the `data-sources/` directory, organized by category and subcategory. You can browse these files directly or use the provided tools to query them.

### Using the Search Index

The repository maintains a lightweight SQLite index for efficient lookups. Here's a simple example of how to use it:

```python
from sqlitedict import SqliteDict

# Open the index
with SqliteDict("index.db") as db:
    # List all sources in a specific category
    vulnerability_sources = db["category_index"].get("vulnerability", [])
    
    # Look up sources by tag
    cloud_sources = db["tag_index"].get("cloud", [])
    
    # Get high-quality sources
    excellent_sources = db["quality_index"].get("excellent", [])
    
    # Get details for a specific source
    nvd_details = db["source_lookup"].get("nvd-cve")
```

## Common Tasks

### Updating Data Sources

To fetch the latest data from all sources:

```bash
python tools/fetch_sources.py
```

### Recalculating Quality Scores

To update quality scores based on freshness, authority, and other metrics:

```bash
python tools/score_sources.py
```

### Rebuilding the Search Index

To rebuild the search index after adding or modifying sources:

```bash
python tools/index_sources.py
```

### Validating Source Files

To validate all source files against the JSON schema:

```bash
python tools/validate_sources.py
```

## Working with Specific Categories

### Vulnerability Data

The repository includes various vulnerability data sources:

```python
from sqlitedict import SqliteDict

with SqliteDict("index.db") as db:
    # Get all vulnerability sources
    vuln_sources = db["category_index"].get("vulnerability", [])
    
    # Get NVD details
    nvd = db["source_lookup"].get("nvd-cve")
    
    # Print NVD URL
    print(f"NVD Feed URL: {nvd['url']}")
```

## Next Steps

- [Configuration](configuration.md) - Learn how to configure the Data Sources Manager
- [Data Sources](../usage/data-sources.md) - See the complete list of available data sources
- [Scoring](../usage/scoring.md) - Understand how quality scoring works
