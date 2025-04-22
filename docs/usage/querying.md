# Querying Data Sources

The Data Sources Manager provides multiple ways to query and access the data sources.

## Using the Search Index

The most efficient way to query data sources is through the SQLite-based search index. The index is built by the `index_sources.py` tool and provides fast access to sources based on various criteria.

### Basic Index Structure

The index contains several lookup tables:

- `category_index`: Sources organized by category
- `tag_index`: Sources organized by tag
- `format_index`: Sources organized by format
- `quality_index`: Sources organized by quality buckets
- `source_lookup`: Detailed information for each source by ID

### Opening the Index

```python
from sqlitedict import SqliteDict

# Open the index
with SqliteDict("index.db") as db:
    # Use the index...
    pass
```

### Query Examples

#### Finding Sources by Category

```python
with SqliteDict("index.db") as db:
    # Get all vulnerability sources
    vulnerability_sources = db["category_index"].get("vulnerability", [])
    
    # Print the IDs
    print(f"Found {len(vulnerability_sources)} vulnerability sources:")
    for source_id in vulnerability_sources:
        print(f"- {source_id}")
```

#### Finding Sources by Tag

```python
with SqliteDict("index.db") as db:
    # Get sources with a specific tag
    official_sources = db["tag_index"].get("official", [])
    
    # Print the IDs
    print(f"Found {len(official_sources)} official sources:")
    for source_id in official_sources:
        print(f"- {source_id}")
```

#### Finding High-Quality Sources

```python
with SqliteDict("index.db") as db:
    # Get excellent quality sources (90-100 score)
    excellent_sources = db["quality_index"].get("excellent", [])
    
    # Print the IDs
    print(f"Found {len(excellent_sources)} excellent sources:")
    for source_id in excellent_sources:
        print(f"- {source_id}")
```

#### Getting Source Details

```python
with SqliteDict("index.db") as db:
    # Get details for a specific source
    nvd = db["source_lookup"].get("nvd-cve")
    
    if nvd:
        print(f"National Vulnerability Database:")
        print(f"  URL: {nvd['url']}")
        print(f"  Quality: {nvd['quality_score']}")
        print(f"  Last Updated: {nvd['last_updated']}")
```

#### Finding Sources by Multiple Criteria

```python
with SqliteDict("index.db") as db:
    # Get all vulnerability sources
    vulnerability_sources = db["category_index"].get("vulnerability", [])
    
    # Get all JSON format sources
    json_sources = db["format_index"].get("json", [])
    
    # Find vulnerability sources in JSON format
    json_vulnerability_sources = set(vulnerability_sources).intersection(json_sources)
    
    print(f"Found {len(json_vulnerability_sources)} JSON vulnerability sources")
    
    # Get details for each source
    for source_id in json_vulnerability_sources:
        source = db["source_lookup"].get(source_id)
        print(f"- {source['name']} (Quality: {source['quality_score']})")
```

## Direct File Access

If you prefer to work directly with the source files, they are stored as JSON files in the `data-sources/` directory, organized by category and subcategory:

```
data-sources/
└── vulnerability/
    ├── cve/
    │   ├── nvd.json
    │   └── vendor-advisory.json
    ├── exploit-db.json
    └── ...
```

You can read these files directly using standard file I/O:

```python
import json
import glob
from pathlib import Path

# Find all source files
source_files = glob.glob("data-sources/**/*.json", recursive=True)

# Read each file
sources = []
for file_path in source_files:
    with open(file_path, "r") as f:
        source = json.load(f)
        sources.append(source)

# Filter sources based on criteria
high_quality_sources = [s for s in sources if s.get("quality_score", 0) >= 90]

print(f"Found {len(high_quality_sources)} high-quality sources")
for source in high_quality_sources:
    print(f"- {source['name']} (Quality: {source['quality_score']})")
```

## Python API

The Data Sources Manager includes Python tools that can be imported and used in your own code:

```python
from tools.index_sources import build_category_index, build_tag_index, build_source_lookup

# Load all sources
sources = load_sources()

# Build indices
category_index = build_category_index(sources)
tag_index = build_tag_index(sources)
source_lookup = build_source_lookup(sources)

# Use the indices
vulnerability_sources = category_index.get("vulnerability", [])
official_sources = tag_index.get("official", [])

# Find sources that match both criteria
for source_id in set(vulnerability_sources).intersection(official_sources):
    source = source_lookup.get(source_id)
    print(f"- {source['name']} (Quality: {source['quality_score']})")
```

## Best Practices

- **Use the index** for most queries, as it's optimized for fast lookups
- **Cache results** when making multiple queries to avoid reopening the index
- **Consider quality scores** when selecting sources to use
- **Check last_updated** to ensure data is recent enough for your needs