# Configuration

The Data Sources Manager can be configured to suit your specific needs. This guide explains the available configuration options.

## Configuration Files

The main configuration files are located in the `config/` directory:

### categories.json

This file defines the categories and tags for organizing data sources:

```json
{
  "vulnerability": ["cve","nvd","exploit-db","vendor-advisory"],
  "technology_tags": ["web","container","cloud","network","host"]
}
```

You can modify this file to add new categories or tags as needed.

### scoring-config.json

This file defines the weights used for calculating quality scores:

```json
{
  "weights": {
    "freshness":    0.4,
    "authority":    0.3,
    "coverage":     0.2,
    "availability": 0.1
  },
  "update_schedule": {
    "daily":  true,
    "weekly": false
  }
}
```

- The `weights` section determines how much each factor contributes to the overall quality score.
- The `update_schedule` section controls how often sources are updated.

## Environment Variables

For features that require API access to external data sources, you can configure API keys in a `.env` file:

```
NVD_API_KEY=your_nvd_api_key_here
ALIENVAULT_OTX_API_KEY=your_otx_api_key_here
```

See the [API Keys](../development/api-keys.md) documentation for more details on obtaining and configuring these keys.

## User Preference Weights

Each data source can have user-specific preference weights that override the global weights:

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

This allows you to prioritize sources based on your specific needs.

## Update Automation

The repository includes GitHub Actions workflows for automating updates:

### update-sources.yml

This workflow runs daily to fetch the latest data, update quality scores, and rebuild the index:

```yaml
name: "Update Data Sources"
on:
  schedule:
    - cron: "0 2 * * *"
```

You can modify the schedule to run at a different time or frequency.

### lint-schemas.yml

This workflow validates the JSON schemas on every push and pull request:

```yaml
name: "Validate JSON Schemas"
on: [push, pull_request]
```

This helps ensure that all changes to the schemas are valid.

## Customization

To customize the Data Sources Manager:

1. Fork the repository
2. Modify the configuration files
3. Add your own data sources
4. Update the weights to match your priorities

The system is designed to be flexible and extensible, so you can adapt it to your specific use case.