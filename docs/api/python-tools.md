# Python Tools API

The Data Sources Manager includes several Python tools that can be used programmatically in your own code. This page documents the key functions and classes in these tools.

## fetch_sources.py

The `fetch_sources.py` module is responsible for fetching data from sources and updating metadata.

### Key Functions

#### `load_source_files()`

Loads all source metadata files from the `data-sources/` directory.

```python
from tools.fetch_sources import load_source_files

# Load all sources
sources = load_source_files()
print(f"Loaded {len(sources)} sources")
```

#### `fetch_source_health(source)`

Checks if a source is available and returns health metrics.

```python
from tools.fetch_sources import fetch_source_health

# Check health of a source
source = {"url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"}
health = fetch_source_health(source)
print(f"Source available: {health['available']}")
print(f"Status code: {health['status_code']}")
print(f"Response time: {health['response_time']}s")
```

#### `update_source_metadata(source, health)`

Updates the source metadata with health check results and current timestamp.

```python
from tools.fetch_sources import update_source_metadata

# Update source metadata
source = {"id": "nvd-cve", "availability": 90}
health = {"available": True, "status_code": 200, "response_time": 0.5}
updated_source = update_source_metadata(source, health)
print(f"Updated last_updated: {updated_source['last_updated']}")
```

## score_sources.py

The `score_sources.py` module is responsible for calculating quality scores for data sources.

### Key Functions

#### `load_scoring_config()`

Loads scoring configuration from the config file.

```python
from tools.score_sources import load_scoring_config

# Load scoring config
config = load_scoring_config()
weights = config.get("weights", {})
print(f"Freshness weight: {weights.get('freshness')}")
```

#### `calculate_freshness_score(last_updated_str)`

Calculates freshness score based on last update date.

```python
from tools.score_sources import calculate_freshness_score

# Calculate freshness score
freshness = calculate_freshness_score("2025-04-15T00:00:00Z")
print(f"Freshness score: {freshness}")
```

#### `calculate_quality_score(source, weights)`

Calculates overall quality score based on component metrics and weights.

```python
from tools.score_sources import calculate_quality_score

# Calculate quality score
source = {
    "last_updated": "2025-04-15T00:00:00Z",
    "authority": 90,
    "coverage": 85,
    "availability": 95
}
weights = {
    "freshness": 0.4,
    "authority": 0.3,
    "coverage": 0.2,
    "availability": 0.1
}
quality_score = calculate_quality_score(source, weights)
print(f"Quality score: {quality_score}")
```

## index_sources.py

The `index_sources.py` module is responsible for building the search index.

### Key Functions

#### `build_category_index(sources)`

Builds an index of sources by category.

```python
from tools.index_sources import build_category_index

# Build category index
sources = [
    {"id": "nvd-cve", "category": "vulnerability"},
    {"id": "exploit-db", "category": "vulnerability"}
]
category_index = build_category_index(sources)
print(f"Vulnerability sources: {category_index.get('vulnerability', [])}")
```

#### `build_tag_index(sources)`

Builds an index of sources by tag.

```python
from tools.index_sources import build_tag_index

# Build tag index
sources = [
    {"id": "nvd-cve", "tags": ["official", "government"]},
    {"id": "exploit-db", "tags": ["exploit", "security"]}
]
tag_index = build_tag_index(sources)
print(f"Official sources: {tag_index.get('official', [])}")
print(f"Security sources: {tag_index.get('security', [])}")
```

#### `build_source_lookup(sources)`

Builds a lookup dictionary for source details by ID.

```python
from tools.index_sources import build_source_lookup

# Build source lookup
sources = [
    {
        "id": "nvd-cve",
        "name": "National Vulnerability Database",
        "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz",
        "category": "vulnerability",
        "format": "json",
        "quality_score": 95,
        "last_updated": "2025-04-22T00:00:00Z"
    }
]
source_lookup = build_source_lookup(sources)
print(f"NVD details: {source_lookup.get('nvd-cve')}")
```

## validate_sources.py

The `validate_sources.py` module is responsible for validating source files against the schema.

### Usage Example

```python
import json
import jsonschema
from pathlib import Path

# Load schema
schema_path = Path("schemas/source.schema.json")
with open(schema_path, "r") as f:
    schema = json.load(f)

# Validate a source file
source_path = Path("data-sources/vulnerability/cve/nvd.json")
with open(source_path, "r") as f:
    source = json.load(f)

try:
    jsonschema.validate(source, schema)
    print(f"{source_path} is valid")
except jsonschema.exceptions.ValidationError as e:
    print(f"{source_path} is invalid: {e}")
```

## validate_api_keys.py

The `validate_api_keys.py` module is responsible for validating API keys against services.

### Key Functions

#### `validate_nvd_api_key()`

Validates the NVD API key.

```python
from tools.validate_api_keys import validate_nvd_api_key

# Validate NVD API key
valid = validate_nvd_api_key()
print(f"NVD API key is valid: {valid}")
```

#### `validate_otx_api_key()`

Validates the AlienVault OTX API key.

```python
from tools.validate_api_keys import validate_otx_api_key

# Validate OTX API key
valid = validate_otx_api_key()
print(f"OTX API key is valid: {valid}")
```

## Full Example

Here's a complete example that combines multiple tools:

```python
from tools.fetch_sources import load_source_files
from tools.score_sources import calculate_quality_score, load_scoring_config
from tools.index_sources import build_category_index, build_source_lookup

# Load sources and config
sources = load_source_files()
config = load_scoring_config()
weights = config.get("weights", {})

# Recalculate quality scores
for source in sources:
    source["quality_score"] = calculate_quality_score(source, weights)

# Build indices
category_index = build_category_index(sources)
source_lookup = build_source_lookup(sources)

# Find high-quality vulnerability sources
vulnerability_sources = category_index.get("vulnerability", [])
high_quality_sources = []

for source_id in vulnerability_sources:
    source = source_lookup.get(source_id)
    if source and source.get("quality_score", 0) >= 90:
        high_quality_sources.append(source)

# Print results
print(f"Found {len(high_quality_sources)} high-quality vulnerability sources:")
for source in high_quality_sources:
    print(f"- {source['name']} (Quality: {source['quality_score']})")
```
