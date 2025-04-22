# Data Sources Manager

A centralized, version‑controlled catalog of high‑quality data feeds for LLM‑based projects, with an initial focus on vulnerability research.

## Overview

The Data Sources Manager streamlines source discovery, scoring, and consumption, enabling consistent, automated integration of reliable information into downstream workflows.

## Features

- **Structured Metadata**: Consistent JSON schema for tracking diverse source types
- **Quality Scoring**: Numeric scoring (0-100) based on freshness, authority, coverage, and availability
- **User Preference Weights**: Customize source priorities based on your needs
- **Automated Updates**: Daily fetching, scoring, and indexing via GitHub Actions
- **Fast Lookups**: Minimal-token lookups via lightweight SQLite index

## Quick Links

- [Installation](getting-started/installation.md) - Set up the Data Sources Manager
- [Quick Start](getting-started/quickstart.md) - Get started in minutes
- [Data Sources](usage/data-sources.md) - Browse available data sources
- [Contributing](development/contributing.md) - Add new data sources

## Project Structure

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

## License

This project is available under the MIT License.