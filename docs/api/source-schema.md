# Source Schema

The `source.schema.json` defines the structure for data source metadata files. This schema ensures consistency across all data sources in the repository.

## Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Data Source Metadata",
  "type": "object",
  "properties": {
    "id":              { "type": "string" },
    "name":            { "type": "string" },
    "url":             { "type": "string", "format": "uri" },
    "description":     { "type": "string" },
    "category":        { "type": "string" },
    "sub_category":    { "type": "string" },
    "format":          { "type": "string", "enum": ["json","csv","rss","xml","other"] },
    "tags":            { "type": "array", "items": { "type": "string" } },
    "quality_score":   { "type": "number", "minimum": 0, "maximum": 100 },
    "user_weighted_score": { "type": "number", "minimum": 0, "maximum": 100 },
    "last_updated":    { "type": "string", "format": "date-time" }
  },
  "required": ["id","name","url","category","format","quality_score","last_updated"]
}
```

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the data source |
| `name` | string | Yes | Human-readable name of the data source |
| `url` | string (URI) | Yes | URL to access the data source |
| `description` | string | No | Description of what the data source provides |
| `category` | string | Yes | Primary category (e.g., "vulnerability") |
| `sub_category` | string | No | Subcategory for more specific classification |
| `format` | string (enum) | Yes | Format of the data (json, csv, rss, xml, other) |
| `tags` | array of strings | No | List of tags for additional classification |
| `quality_score` | number (0-100) | Yes | Calculated quality score |
| `user_weighted_score` | number (0-100) | No | Quality score with user preference weights |
| `last_updated` | string (date-time) | Yes | Timestamp of the last update (ISO 8601 format) |

## Example Source File

```json
{
  "id": "nvd-cve",
  "name": "National Vulnerability Database",
  "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz",
  "description": "NIST National Vulnerability Database CVE feed",
  "category": "vulnerability",
  "sub_category": "cve",
  "format": "json",
  "tags": ["official", "government", "security"],
  "quality_score": 95,
  "user_weighted_score": 95,
  "last_updated": "2025-04-22T00:00:00Z"
}
```

## Usage

### Validating Against Schema

You can validate a source file against the schema using the `jsonschema` Python package:

```bash
jsonschema -i data-sources/vulnerability/cve/nvd.json schemas/source.schema.json
```

Or using the provided validation tool:

```bash
python tools/validate_sources.py
```

### Creating New Source Files

When creating a new source file, make sure it follows the schema:

1. Use a unique `id` that describes the source
2. Provide a clear `name` and `description`
3. Include the correct `url` to access the data
4. Specify the appropriate `category` and `format`
5. Set an initial `quality_score` based on your assessment
6. Set the `last_updated` timestamp to the current time

The `score_sources.py` tool will recalculate the quality score based on the current data.

## Related Schemas

- [Quality Schema](quality-schema.md) - Defines the structure for quality scoring attributes