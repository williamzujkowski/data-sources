# Quality Schema

The `quality.schema.json` defines the structure for quality scoring attributes. This schema ensures consistency in how quality scores are calculated across all data sources.

## Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Quality Scoring Attributes",
  "type": "object",
  "properties": {
    "freshness":    { "type": "number", "description": "days since last update" },
    "authority":    { "type": "number", "description": "0–100 credibility" },
    "coverage":     { "type": "number", "description": "0–100 scope of data" },
    "availability": { "type": "number", "description": "0–100 uptime/reliability" },
    "user_preference_weight": {
      "type": "object",
      "properties": {
        "freshness":    { "type": "number" },
        "authority":    { "type": "number" },
        "coverage":     { "type": "number" },
        "availability": { "type": "number" }
      },
      "additionalProperties": false
    }
  },
  "required": ["freshness","authority","coverage","availability"]
}
```

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `freshness` | number | Yes | Measure of how recently the source was updated (days since last update) |
| `authority` | number (0-100) | Yes | Credibility rating of the source |
| `coverage` | number (0-100) | Yes | How comprehensive the source's data coverage is |
| `availability` | number (0-100) | Yes | Reliability and uptime of the source |
| `user_preference_weight` | object | No | User-specific weights for calculating custom scores |

### User Preference Weight Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `freshness` | number | No | User-defined weight for freshness |
| `authority` | number | No | User-defined weight for authority |
| `coverage` | number | No | User-defined weight for coverage |
| `availability` | number | No | User-defined weight for availability |

## Quality Score Calculation

The overall quality score is calculated using these attributes with the following formula:

```
quality_score = (freshness * 0.4) + (authority * 0.3) + (coverage * 0.2) + (availability * 0.1)
```

When user preference weights are available, the formula becomes:

```
user_weighted_score = (freshness * user_weight.freshness) + 
                      (authority * user_weight.authority) + 
                      (coverage * user_weight.coverage) + 
                      (availability * user_weight.availability)
```

Where the user weights are normalized to sum to 1.0.

## Example Quality Attributes

```json
{
  "freshness": 95,
  "authority": 90,
  "coverage": 85,
  "availability": 95,
  "user_preference_weight": {
    "freshness": 0.5,
    "authority": 0.3,
    "coverage": 0.1,
    "availability": 0.1
  }
}
```

## Usage

### Scoring Sources

The `score_sources.py` tool uses this schema to calculate quality scores:

```bash
python tools/score_sources.py
```

### Customizing User Weights

You can customize the user preference weights in your data source files to prioritize certain attributes:

```json
"user_preference_weight": {
  "freshness": 0.6,    // Prioritize freshness
  "authority": 0.2,
  "coverage": 0.1,
  "availability": 0.1
}
```

This will result in a custom `user_weighted_score` that emphasizes freshness more than the default weighting.

## Related Schemas

- [Source Schema](source-schema.md) - Defines the structure for data source metadata