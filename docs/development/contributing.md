# Contributing

Thank you for your interest in contributing to the Data Sources Manager! This document provides guidelines for adding new data sources, updating existing ones, and contributing to the codebase.

## Deprecated Sources Rule

> If a data source is no longer useful, **do not delete** its metadata file.
> Instead, set `"quality_score": 0` and update `"last_updated"` to mark it retired.

This ensures that previously used sources remain in the history and helps avoid re-adding deprecated sources.

## Adding New Data Sources

1. Identify the appropriate category for your data source in the `data-sources/` directory.
2. Create a new JSON file following the naming convention `source-name.json`.
3. Use the following template for your source metadata:

```json
{
  "id": "unique-source-id",
  "name": "Human-Readable Source Name",
  "url": "https://example.com/data-feed",
  "description": "Concise description of what this source provides",
  "category": "vulnerability",
  "sub_category": "cve",
  "format": "json",
  "tags": ["tag1", "tag2", "tag3"],
  "quality_score": 80,
  "last_updated": "2025-04-22T00:00:00Z",
  "freshness": 0,
  "authority": 85,
  "coverage": 75,
  "availability": 90
}
```

4. Validate your JSON file against the schema using the commands:
   ```bash
   python tools/validate_sources.py
   ```

## Updating Existing Sources

1. Locate the source file you want to update.
2. Make your changes, ensuring they follow the schema.
3. Update the `last_updated` field with the current date-time.
4. Adjust quality metrics if necessary.
5. Validate your changes against the schema.

## Scoring Guide

Source quality is measured using these metrics:

- **Freshness**: How frequently the source is updated (0-100)
- **Authority**: Credibility of the source (0-100)
- **Coverage**: Comprehensiveness of the data (0-100)
- **Availability**: Reliability and uptime (0-100)

The overall `quality_score` is calculated as:
```
quality_score = (freshness * 0.4) + (authority * 0.3) + (coverage * 0.2) + (availability * 0.1)
```

## Contribution Process

1. Fork the repository.
2. Create a feature branch for your contribution.
3. Make your changes following the guidelines above.
4. Run tests to ensure everything works:
   ```bash
   # Validate sources
   python tools/validate_sources.py
   ```
5. Submit a pull request with a clear description of your changes.

## PR Checklist

- [ ] Source metadata follows the schema
- [ ] JSON files are valid and properly formatted
- [ ] `last_updated` field reflects the current date
- [ ] Quality scores are justified with appropriate metrics
- [ ] Documentation updated if applicable

## Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r tools/requirements.txt

# Optional: Install development tools
pip install black flake8 pytest
```

## Documentation

If you're adding a new feature or making significant changes, please update the documentation:

1. Update the relevant Markdown files in the `docs/` directory
2. Preview the changes locally:
   ```bash
   mkdocs serve
   ```
3. Include documentation changes in your pull request

Thank you for contributing to the Data Sources Manager!
