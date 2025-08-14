# Architecture

This document describes the overall architecture of the Data Sources Manager, explaining how the different components work together.

## System Overview

The Data Sources Manager is designed as a simple yet efficient system for tracking, scoring, and querying data sources. It consists of the following main components:

1. **Data Source Metadata**: JSON files that describe each data source
2. **Schemas**: JSON Schema definitions that enforce consistency
3. **Configuration**: Settings for categories, scoring weights, etc.
4. **Tools**: Python scripts for fetching, scoring, and indexing
5. **Search Index**: SQLite-based index for efficient queries
6. **Documentation**: Comprehensive guides and references

## Component Architecture

### Data Flow Diagram

```
+----------------+     +----------------+     +----------------+
| Data Sources   |     | Fetch Sources  |     | Source Health  |
| JSON Files     | --> | Python Tool    | --> | Metrics        |
+----------------+     +----------------+     +----------------+
        |                      |                     |
        v                      v                     v
+----------------+     +----------------+     +----------------+
| Score Sources  |     | Index Sources  |     | Search Index   |
| Python Tool    | --> | Python Tool    | --> | (SQLite)       |
+----------------+     +----------------+     +----------------+
        ^                      ^                     |
        |                      |                     v
+----------------+     +----------------+     +----------------+
| Configuration  |     | Schemas        |     | Query API      |
| JSON Files     |     | JSON Schema    |     | (Python)       |
+----------------+     +----------------+     +----------------+
```

### Directory Structure

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
├── docs/                        # Documentation
│   ├── index.md                 # Home page
│   ├── getting-started/         # Getting started guides
│   ├── usage/                   # Usage guides
│   └── api/                     # API references
└── .github/workflows/           # CI/CD automation
    ├── update-sources.yml       # Daily source updates
    └── lint-schemas.yml         # Schema validation
```

## Key Components

### 1. Data Source Metadata

Each data source is represented by a JSON file that follows the `source.schema.json` schema. These files contain metadata about the source, including:

- Basic information (ID, name, URL, description)
- Categorization (category, sub-category, tags)
- Quality metrics (quality_score, last_updated)
- Format and other attributes

### 2. JSON Schemas

The system uses JSON Schema to enforce consistency across all data source files:

- `source.schema.json`: Defines the structure for data source metadata
- `quality.schema.json`: Defines the structure for quality scoring attributes

### 3. Configuration

Configuration files in the `config/` directory control various aspects of the system:

- `categories.json`: Defines categories and tags for organizing sources
- `scoring-config.json`: Sets weights for quality scoring and update schedules

### 4. Python Tools

The system includes several Python tools for managing data sources:

- `fetch_sources.py`: Fetches data from sources and updates metadata
- `score_sources.py`: Calculates quality scores based on freshness, authority, etc.
- `index_sources.py`: Builds a search index for efficient queries
- `validate_sources.py`: Validates source files against the schemas
- `validate_api_keys.py`: Validates API keys for external services

### 5. Search Index

The search index is a SQLite database (`index.db`) that provides fast access to sources based on various criteria:

- `category_index`: Sources organized by category
- `tag_index`: Sources organized by tag
- `format_index`: Sources organized by format
- `quality_index`: Sources organized by quality buckets
- `source_lookup`: Detailed information for each source by ID

### 6. CI/CD Automation

GitHub Actions workflows automate various tasks:

- `update-sources.yml`: Runs daily to fetch the latest data, update quality scores, and rebuild the index
- `lint-schemas.yml`: Validates the JSON schemas on every push and pull request

## Data Flow

The typical data flow in the system is as follows:

1. **Source Addition**: A contributor adds a new data source JSON file
2. **Validation**: The file is validated against the schema
3. **Fetching**: The `fetch_sources.py` tool checks the source's health and updates metadata
4. **Scoring**: The `score_sources.py` tool calculates quality scores based on freshness, authority, etc.
5. **Indexing**: The `index_sources.py` tool builds the search index
6. **Querying**: Users query the search index to find relevant sources

## Design Principles

The Data Sources Manager follows these design principles:

1. **Simplicity**: Simple file-based storage with minimal dependencies
2. **Consistency**: Strict schema validation to ensure data quality
3. **Modularity**: Separate tools for different functions
4. **Efficiency**: Optimized search index for fast queries
5. **Extensibility**: Easy to add new sources and categories
6. **Automation**: Automated updates and validation

## Future Enhancements

Potential future enhancements to the architecture include:

1. **API Server**: A REST API for remote access to the data
2. **Web Interface**: A web-based UI for browsing and managing sources
3. **Analytics**: Advanced analytics on source quality and usage
4. **Notification System**: Alerts for source changes or problems
5. **Integration**: Direct integration with downstream systems

## Conclusion

The Data Sources Manager's architecture is designed to be simple, flexible, and efficient, making it easy to track, score, and query data sources for LLM-based projects.
