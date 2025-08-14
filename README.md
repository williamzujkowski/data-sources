# Data Sources Manager

A centralized, version‑controlled catalog of high‑quality data feeds for LLM‑based projects, with an initial focus on vulnerability research.

## Overview

The data-sources-manager streamlines source discovery, scoring, and consumption, enabling consistent, automated integration of reliable information into downstream workflows.

## 📊 Data Sources

### Government & Standards Sources (Implemented)
- **CISA KEV** (10/10): Real-time exploited vulnerabilities catalog - highest authority for active exploitation
- **MITRE ATT&CK** (9/10): Adversary tactics and techniques framework - comprehensive TTP coverage
- **MITRE D3FEND** (8/10): Defensive countermeasures framework - structured defensive techniques
- **EPSS** (9/10): ML-based exploit prediction scoring - probabilistic exploitation forecasting

### Community Sources (Coming Soon)
- AlienVault OTX - Crowd-sourced threat intelligence
- abuse.ch suite - Malware and botnet tracking
- NVD - Comprehensive vulnerability database
- More sources being added weekly!

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/williamzujkowski/data-sources.git
cd data-sources

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Using the Data
```python
from tools.fetch_sources import load_source_files
from tools.score_sources import calculate_quality_score

# Load all data sources
sources = load_source_files()

# Filter high-priority vulnerabilities
critical_vulns = [
    s for s in sources 
    if s.get('exploitation_status', {}).get('kev_listed', False) or 
       s.get('exploitation_status', {}).get('epss_score', 0) > 0.7
]

# Calculate quality scores
for source in sources:
    score = calculate_quality_score(source, weights={
        "freshness": 0.4,
        "authority": 0.3,
        "coverage": 0.2,
        "availability": 0.1
    })
    print(f"{source['name']}: {score}/100")
```

### Command Line Tools
```bash
# Validate all sources against schema
python tools/validate_sources.py

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

## 📈 Source Quality Metrics

| Source | Authority | Update Frequency | Coverage | API Limits | Quality Score |
|--------|-----------|-----------------|----------|------------|---------------|
| CISA KEV | 10/10 | Real-time | Exploited CVEs | Unlimited | 100/100 |
| MITRE ATT&CK | 10/10 | Quarterly | TTPs | Unlimited | 95/100 |
| EPSS | 9/10 | Daily | All CVEs | Unlimited | 92/100 |
| D3FEND | 9/10 | Periodic | Defenses | Unlimited | 88/100 |

## 🔄 Data Update Schedule

Sources are automatically updated according to their configured frequency:
- **Real-time**: CISA KEV (on publication)
- **Daily**: EPSS scores (2 AM UTC)
- **Weekly**: Community feeds (Sundays)
- **Quarterly**: MITRE frameworks

## Features

- **Structured Metadata**: Consistent JSON schema for tracking diverse source types
- **Quality Scoring**: Numeric scoring (0-100) based on freshness, authority, coverage, and availability
- **User Preference Weights**: Customize source priorities based on your needs
- **Automated Updates**: Daily fetching, scoring, and indexing via GitHub Actions
- **Fast Lookups**: Minimal-token lookups via lightweight SQLite index
- **Threat Intelligence**: Extended schema supporting IOCs, TTPs, and threat actors
- **Exploitation Tracking**: KEV status, EPSS scores, and weaponization indicators

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to add or update data sources.

## License

This project is available under the MIT License.
