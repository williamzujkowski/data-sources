# Tools API Reference

This document provides comprehensive API documentation for the Python tools included in the data-sources project.

## Table of Contents

- [fetch_sources](#fetch_sources)
- [score_sources](#score_sources)
- [validate_sources](#validate_sources)
- [index_sources](#index_sources)
- [Common Data Structures](#common-data-structures)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)

## fetch_sources

Module for fetching and updating data source metadata with health checks.

### Classes

#### DataSourceError
```python
class DataSourceError(Exception):
    """Base exception for data source operations."""
```

#### SourceFileError
```python
class SourceFileError(DataSourceError):
    """Exception raised when source file operations fail."""
```

#### HealthCheckError
```python
class HealthCheckError(DataSourceError):
    """Exception raised when health check operations fail."""
```

#### MetadataUpdateError
```python
class MetadataUpdateError(DataSourceError):
    """Exception raised when metadata update operations fail."""
```

### Functions

#### load_source_files()
```python
def load_source_files() -> List[Dict[str, Any]]:
    """
    Load all source metadata files from the data sources directory.
    
    Returns:
        List of source metadata dictionaries with _file_path added.
        
    Raises:
        SourceFileError: If no source files are found or directory doesn't exist.
    """
```

**Example:**
```python
import fetch_sources

# Load all source files
sources = fetch_sources.load_source_files()
print(f"Loaded {len(sources)} sources")

for source in sources:
    print(f"- {source['id']}: {source['name']}")
```

#### fetch_source_health()
```python
def fetch_source_health(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if a source is available and return health metrics.
    
    Args:
        source: Source metadata dictionary containing URL and other details.
        
    Returns:
        Dictionary with health check results including:
        - available: bool indicating if source is reachable
        - status_code: HTTP status code or None if request failed
        - response_time: Response time in seconds or None if request failed
        - error_message: Error message if request failed (optional)
    
    Raises:
        HealthCheckError: If source data is invalid.
    """
```

**Example:**
```python
source = {
    "id": "example-source",
    "url": "https://api.example.com/data"
}

health = fetch_sources.fetch_source_health(source)
if health['available']:
    print(f"Source is available (HTTP {health['status_code']})")
    print(f"Response time: {health['response_time']:.2f}s")
else:
    print(f"Source unavailable: {health.get('error_message', 'Unknown error')}")
```

#### update_source_metadata()
```python
def update_source_metadata(
    source: Dict[str, Any], 
    health: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update the source metadata with health check results and current timestamp.
    
    Args:
        source: Original source metadata dictionary.
        health: Health check results dictionary.
        
    Returns:
        Updated source metadata dictionary.
        
    Raises:
        MetadataUpdateError: If source or health data is invalid.
    """
```

#### save_source_file()
```python
def save_source_file(source: Dict[str, Any]) -> None:
    """
    Save the updated source metadata back to disk.
    
    Args:
        source: Source metadata dictionary with _file_path field.
        
    Raises:
        SourceFileError: If file operations fail.
    """
```

#### main()
```python
def main() -> int:
    """
    Main entry point for fetching and updating sources.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
```

**Command Line Usage:**
```bash
# Fetch and update all sources
python tools/fetch_sources.py

# Check exit code
echo $?  # 0 for success, 1 for failure
```

## score_sources

Module for calculating quality scores for data sources based on various metrics.

### Functions

#### load_scoring_config()
```python
def load_scoring_config() -> Dict[str, Any]:
    """
    Load scoring configuration from config file.
    
    Returns:
        Configuration dictionary with weights and other settings.
    """
```

#### calculate_freshness_score()
```python
def calculate_freshness_score(last_updated_str: Optional[str]) -> float:
    """
    Calculate freshness score (0-100) based on last update date.
    
    Args:
        last_updated_str: ISO 8601 timestamp string or None
        
    Returns:
        Freshness score between 0 and 100.
        - 0 days old = 100 points
        - 30 days old = 50 points  
        - 60+ days old = 0 points
    """
```

**Example:**
```python
import score_sources
from datetime import datetime, timezone

# Recent timestamp (high score)
recent = datetime.now(timezone.utc).isoformat() + "Z"
score = score_sources.calculate_freshness_score(recent)
print(f"Recent data score: {score}")  # Close to 100

# Old timestamp (low score)
old_timestamp = "2024-01-01T00:00:00Z"
score = score_sources.calculate_freshness_score(old_timestamp)
print(f"Old data score: {score}")  # Lower score
```

#### calculate_quality_score()
```python
def calculate_quality_score(
    source: Dict[str, Any], 
    weights: Dict[str, float]
) -> float:
    """
    Calculate overall quality score based on component metrics and weights.
    
    Args:
        source: Source metadata dictionary
        weights: Scoring weights dictionary
        
    Returns:
        Overall quality score (0-100)
    """
```

**Example:**
```python
source = {
    "last_updated": "2025-08-14T12:00:00Z",
    "authority": 90.0,
    "coverage": 85.0,
    "availability": 95.0
}

weights = {
    "freshness": 0.4,
    "authority": 0.3,
    "coverage": 0.2,
    "availability": 0.1
}

score = score_sources.calculate_quality_score(source, weights)
print(f"Quality score: {score}")
```

#### calculate_user_weighted_score()
```python
def calculate_user_weighted_score(
    source: Dict[str, Any],
    weights: Dict[str, float],
    user_weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate user-weighted score based on user preference weights.
    
    Args:
        source: Source metadata dictionary
        weights: Default scoring weights
        user_weights: User-specific weights (optional)
        
    Returns:
        User-weighted score (0-100)
    """
```

#### main()
```python
def main() -> None:
    """Main entry point for scoring sources."""
```

**Command Line Usage:**
```bash
# Score all sources using default configuration
python tools/score_sources.py

# The script updates quality_score and user_weighted_score fields
```

## validate_sources

Module for validating data source files against JSON schemas.

### Functions

#### load_schema()
```python
def load_schema(schema_path: Path) -> Dict[Any, Any]:
    """
    Load JSON schema from file.
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Schema dictionary
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is invalid JSON
    """
```

#### main()
```python
def main() -> int:
    """
    Main validation function.
    
    Returns:
        Exit code: 0 if all files valid, 1 if validation errors found
    """
```

**Command Line Usage:**
```bash
# Validate all data source files
python tools/validate_sources.py

# Check validation results
if [ $? -eq 0 ]; then
    echo "All files are valid"
else
    echo "Validation errors found"
fi
```

**Validation Process:**
1. Load schema from `schemas/source.schema.json`
2. Find all JSON files in `data-sources/` directory
3. Validate each file against the schema
4. Report validation errors with file paths and error details
5. Return exit code indicating overall validation status

## index_sources

Module for building and maintaining search indexes for fast data source lookups.

### Functions

#### build_category_index()
```python
def build_category_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build index mapping categories to source IDs.
    
    Args:
        sources: List of source metadata dictionaries
        
    Returns:
        Dictionary mapping category names to lists of source IDs
    """
```

#### build_tag_index()
```python
def build_tag_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build index mapping tags to source IDs.
    
    Args:
        sources: List of source metadata dictionaries
        
    Returns:
        Dictionary mapping tag names to lists of source IDs
    """
```

#### main()
```python
def main() -> None:
    """Main entry point for building search indexes."""
```

**Command Line Usage:**
```bash
# Build search indexes
python tools/index_sources.py

# Creates/updates indexes.db SQLite database
```

## Common Data Structures

### Source Metadata Dictionary

```python
{
    "id": str,                    # Unique identifier
    "name": str,                  # Human-readable name
    "url": str,                   # Data source URL
    "description": str,           # Detailed description
    "category": str,              # Category classification
    "tags": List[str],           # Classification tags
    "format": str,               # Data format (json, xml, etc.)
    "last_updated": str,         # ISO 8601 timestamp
    "quality_score": float,      # Overall quality score (0-100)
    "authority": float,          # Authority score (0-100)
    "coverage": float,           # Coverage score (0-100)
    "availability": float,       # Availability score (0-100)
    "user_weighted_score": float # User-specific weighted score
}
```

### Health Check Results

```python
{
    "available": bool,           # Whether source is reachable
    "status_code": int | None,   # HTTP status code
    "response_time": float | None, # Response time in seconds
    "error_message": str | None  # Error description if failed
}
```

### Scoring Configuration

```python
{
    "weights": {
        "freshness": float,      # Weight for freshness score (0-1)
        "authority": float,      # Weight for authority score (0-1)
        "coverage": float,       # Weight for coverage score (0-1)
        "availability": float    # Weight for availability score (0-1)
    }
}
```

## Error Handling

### Exception Hierarchy

```
Exception
└── DataSourceError (base class)
    ├── SourceFileError (file operations)
    ├── HealthCheckError (health checks)
    └── MetadataUpdateError (metadata updates)
```

### Error Handling Best Practices

```python
import fetch_sources

try:
    sources = fetch_sources.load_source_files()
except fetch_sources.SourceFileError as e:
    print(f"Failed to load sources: {e}")
    # Handle file-related errors
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

## Usage Examples

### Complete Workflow Example

```python
#!/usr/bin/env python3
"""
Example script demonstrating complete data source management workflow.
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

import fetch_sources
import score_sources
import validate_sources


def main():
    """Run complete data source management workflow."""
    
    # 1. Validate all sources
    print("Validating data sources...")
    validation_result = validate_sources.main()
    if validation_result != 0:
        print("Validation failed! Exiting.")
        return 1
    
    # 2. Load sources
    print("Loading source files...")
    try:
        sources = fetch_sources.load_source_files()
        print(f"Loaded {len(sources)} sources")
    except fetch_sources.SourceFileError as e:
        print(f"Failed to load sources: {e}")
        return 1
    
    # 3. Check health and update metadata
    print("Checking source health...")
    healthy_count = 0
    for source in sources:
        try:
            health = fetch_sources.fetch_source_health(source)
            updated_source = fetch_sources.update_source_metadata(source, health)
            fetch_sources.save_source_file(updated_source)
            
            if health['available']:
                healthy_count += 1
                
        except Exception as e:
            print(f"Error processing {source['id']}: {e}")
    
    print(f"Health check complete: {healthy_count}/{len(sources)} sources available")
    
    # 4. Calculate quality scores
    print("Calculating quality scores...")
    config = score_sources.load_scoring_config()
    weights = config.get('weights', {})
    
    for source in sources:
        quality_score = score_sources.calculate_quality_score(source, weights)
        source['quality_score'] = quality_score
        fetch_sources.save_source_file(source)
    
    # 5. Summary report
    avg_score = sum(s.get('quality_score', 0) for s in sources) / len(sources)
    print(f"Average quality score: {avg_score:.1f}")
    
    # Top 5 sources by quality
    top_sources = sorted(sources, key=lambda s: s.get('quality_score', 0), reverse=True)[:5]
    print("\nTop 5 sources by quality:")
    for i, source in enumerate(top_sources, 1):
        score = source.get('quality_score', 0)
        print(f"  {i}. {source['name']} ({score:.1f})")
    
    return 0


if __name__ == "__main__":
    exit(main())
```

### Filtering and Searching

```python
"""Example of filtering and searching data sources."""

import fetch_sources

# Load all sources
sources = fetch_sources.load_source_files()

# Filter by category
vuln_sources = [s for s in sources if s.get('category') == 'vulnerability']
print(f"Vulnerability sources: {len(vuln_sources)}")

# Filter by quality score
high_quality = [s for s in sources if s.get('quality_score', 0) >= 90]
print(f"High quality sources (≥90): {len(high_quality)}")

# Filter by tags
tagged_sources = [s for s in sources if 'threat-intelligence' in s.get('tags', [])]
print(f"Threat intelligence sources: {len(tagged_sources)}")

# Filter by availability
available_sources = [s for s in sources if s.get('availability', 0) >= 95]
print(f"Highly available sources (≥95%): {len(available_sources)}")

# Search by name/description
def search_sources(sources, query):
    """Search sources by name or description."""
    query_lower = query.lower()
    return [
        s for s in sources 
        if query_lower in s.get('name', '').lower() 
        or query_lower in s.get('description', '').lower()
    ]

cve_sources = search_sources(sources, 'cve')
print(f"CVE-related sources: {len(cve_sources)}")
```

### Custom Scoring Example

```python
"""Example of custom scoring with user weights."""

import score_sources

# Load sources and default configuration
sources = fetch_sources.load_source_files()
config = score_sources.load_scoring_config()
default_weights = config.get('weights', {})

# Define custom user weights (prioritize freshness and availability)
user_weights = {
    "freshness": 0.6,      # Higher weight for recent data
    "authority": 0.1,      # Lower weight for authority
    "coverage": 0.1,       # Lower weight for coverage  
    "availability": 0.2    # Higher weight for availability
}

# Calculate scores with custom weights
for source in sources:
    # Default score
    default_score = score_sources.calculate_quality_score(source, default_weights)
    
    # Custom weighted score
    custom_score = score_sources.calculate_user_weighted_score(
        source, default_weights, user_weights
    )
    
    print(f"{source['name']}:")
    print(f"  Default score: {default_score:.1f}")
    print(f"  Custom score:  {custom_score:.1f}")
    print(f"  Difference:    {custom_score - default_score:+.1f}")
    print()
```

---

For more examples and detailed usage instructions, see the [DEVELOPMENT.md](../DEVELOPMENT.md) file and the individual tool source code in the `tools/` directory.
