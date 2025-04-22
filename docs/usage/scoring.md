# Quality Scoring

The Data Sources Manager uses a quality scoring system to help prioritize the most reliable and valuable sources.

## Scoring Mechanism

Quality scores range from 0 to 100, where:

- **0**: Deprecated or retired source
- **1-49**: Poor quality source
- **50-69**: Average quality source
- **70-89**: Good quality source
- **90-100**: Excellent quality source

## Scoring Components

The overall quality score is calculated based on four main factors:

### 1. Freshness (40%)

Measures how recently the source has been updated:

- Recent updates (within days): High freshness score
- Older updates (weeks or months): Lower freshness score
- No updates for extended periods: Very low freshness score

Freshness is calculated based on the `last_updated` field in the source metadata.

### 2. Authority (30%)

Measures the credibility and reliability of the source:

- Official government sources: High authority score
- Established security organizations: High authority score
- Community-driven sources: Medium authority score
- Individual contributors: Lower authority score

Authority scores are assigned based on expert assessment.

### 3. Coverage (20%)

Measures the comprehensiveness of the data:

- Broad coverage of vulnerabilities: High coverage score
- Specialized focus: Medium to high coverage score (depending on completeness)
- Limited scope: Lower coverage score

Coverage scores are assigned based on the breadth and depth of information provided.

### 4. Availability (10%)

Measures the reliability of accessing the source:

- Consistent availability: High availability score
- Occasional downtime: Medium availability score
- Frequent unavailability: Low availability score

Availability is monitored through regular health checks.

## Calculation Formula

The quality score is calculated using the following formula:

```
quality_score = (freshness * 0.4) + (authority * 0.3) + (coverage * 0.2) + (availability * 0.1)
```

This weighted formula ensures that more important factors (like freshness and authority) have a greater impact on the overall score.

## User-Weighted Scores

In addition to the standard quality score, the system also supports user-weighted scores:

```json
{
  "user_preference_weight": {
    "freshness": 0.5,
    "authority": 0.3,
    "coverage": 0.1,
    "availability": 0.1
  }
}
```

This allows users to prioritize sources based on their specific needs. For example, if freshness is more important to you than coverage, you can adjust the weights accordingly.

## Score Buckets

For convenience, sources are categorized into quality buckets:

- **Excellent**: 90-100
- **Good**: 70-89
- **Average**: 50-69
- **Poor**: 1-49
- **Deprecated**: 0

These buckets can be used to quickly filter sources by quality level:

```python
from sqlitedict import SqliteDict

with SqliteDict("index.db") as db:
    # Get all excellent sources
    excellent_sources = db["quality_index"].get("excellent", [])
    
    # Get source details
    for source_id in excellent_sources:
        source = db["source_lookup"].get(source_id)
        print(f"{source['name']}: {source['quality_score']}")
```

## Updating Scores

Quality scores are updated automatically by the `score_sources.py` tool, which calculates freshness based on the current date and combines it with the other quality factors.

You can manually run the scoring tool:

```bash
python tools/score_sources.py
```

This will update the quality scores for all sources based on the latest data.