
You are a repository scaffolding assistant.
Create a new GitHub repository named **data-sources-manager** to track, version‑control and prioritize high‑quality data feeds for LLM projects (initial focus: vulnerability research). Follow best practices in folder layout, JSON metadata schema, minimal‑token lookups, and CI‑driven automation.

## 1. Top‑Level Files
- `README.md`  
  - Purpose overview, quick start, how to query index.  
- `CONTRIBUTING.md`  
  - Guidelines for adding/updating sources, scoring guide, PR checklist.  
  - **Deprecated Sources Rule:**  
    > If a data source is no longer useful, **do not delete** its metadata file.  
    > Instead, set `"quality_score": 0` and update `"last_updated"` to mark it retired.  
- `.gitignore`  
  - Standard patterns (e.g., `*.log`, `__pycache__/`, secrets).  
- `LICENSE` (MIT by default; downstream projects choose).

## 2. Folder Structure
```
data-sources-manager/
├── data-sources/
│   └── vulnerability/            
│       ├── cve/                  
│       │   ├── nvd.json          
│       │   ├── vendor-advisory.json
│       │   └── …  
│       ├── exploit-db.json       
│       └── …  
├── schemas/
│   ├── source.schema.json        
│   └── quality.schema.json       
├── config/
│   ├── categories.json           
│   └── scoring-config.json       
├── tools/
│   ├── fetch_sources.py          
│   ├── score_sources.py          
│   └── index_sources.py          
└── .github/
    └── workflows/
        ├── update-sources.yml    
        └── lint-schemas.yml      
```

## 3. JSON Schemas

### `schemas/source.schema.json`
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

### `schemas/quality.schema.json`
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

## 4. Configuration

### `config/categories.json`
```json
{
  "vulnerability": ["cve","nvd","exploit-db","vendor-advisory"],
  "technology_tags": ["web","container","cloud","network","host"]
}
```

### `config/scoring-config.json`
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

## 5. CI Workflows

### `.github/workflows/update-sources.yml`
```yaml
name: "Update Data Sources"
on:
  schedule:
    - cron: "0 2 * * *"
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install requirements
        run: pip install -r tools/requirements.txt
      - name: Fetch sources
        run: python tools/fetch_sources.py
      - name: Score sources
        run: python tools/score_sources.py
      - name: Index sources
        run: python tools/index_sources.py
      - name: Commit & Push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data-sources/ index.db
          git commit -m "chore: daily update of data sources"
          git push
```

### `.github/workflows/lint-schemas.yml`
```yaml
name: "Validate JSON Schemas"
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate schemas
        run: |
          pip install jsonschema
          python - <<EOF
import json, jsonschema
for file in ["schemas/source.schema.json","schemas/quality.schema.json"]:
    schema = json.load(open(file))
    jsonschema.Draft7Validator.check_schema(schema)
print("All schemas are valid")
EOF
```