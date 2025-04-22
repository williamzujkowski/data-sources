# Data Sources Manager

A centralized, version‑controlled catalog of high‑quality data feeds for LLM‑based projects, with an initial focus on vulnerability research.

## Overview

The data-sources-manager streamlines source discovery, scoring, and consumption, enabling consistent, automated integration of reliable information into downstream workflows.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/data-sources-manager.git
   cd data-sources-manager
   ```

2. Set up a Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r tools/requirements.txt
   ```

3. Run the tools:
   ```bash
   # Fetch latest data from sources
   python tools/fetch_sources.py
   
   # Calculate quality scores
   python tools/score_sources.py
   
   # Build the search index
   python tools/index_sources.py
   ```

## Querying the Index

The repository maintains a lightweight SQLite index for efficient lookups. Here's how to use it:

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

## Directory Structure

```
data-sources-manager/
├── data-sources/                # Data source metadata files
│   └── vulnerability/           # Grouped by category
│       ├── cve/                 # Subcategories
│       │   ├── nvd.json
│       │   ├── vendor-advisory.json
│       │   └── …
│       ├── exploit-db.json
│       └── …
├── schemas/                     # JSON schema definitions
│   ├── source.schema.json       # Source metadata schema
│   └── quality.schema.json      # Quality scoring schema
├── config/                      # Configuration files
│   ├── categories.json          # Category definitions
│   └── scoring-config.json      # Quality scoring weights
├── tools/                       # Python utilities
│   ├── fetch_sources.py         # Update source data
│   ├── score_sources.py         # Calculate quality scores
│   └── index_sources.py         # Build search index
└── .github/workflows/           # CI/CD automation
    ├── update-sources.yml       # Daily source updates
    └── lint-schemas.yml         # Schema validation
```

## Features

- **Structured Metadata**: Consistent JSON schema for tracking diverse source types
- **Quality Scoring**: Numeric scoring (0-100) based on freshness, authority, coverage, and availability
- **User Preference Weights**: Customize source priorities based on your needs
- **Automated Updates**: Daily fetching, scoring, and indexing via GitHub Actions
- **Fast Lookups**: Minimal-token lookups via lightweight SQLite index

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to add or update data sources.

## License

This project is available under the MIT License.