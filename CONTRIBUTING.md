# Contributing to the Threat Intelligence Data Sources Catalog

Thank you for your interest in contributing to this catalog! This guide will help you add new data sources or improve existing ones.

## 📋 Table of Contents

- [Before You Start](#before-you-start)
- [Adding a New Data Source](#adding-a-new-data-source)
- [Updating Existing Sources](#updating-existing-sources)
- [Quality Standards](#quality-standards)
- [Testing Your Contribution](#testing-your-contribution)
- [Submission Process](#submission-process)

## Before You Start

### Prerequisites

- Basic understanding of JSON format
- Familiarity with REST APIs and authentication methods
- Ability to test API endpoints and code examples
- Git knowledge for submitting pull requests

### What We're Looking For

We prioritize data sources that are:
- **Publicly accessible** (free tier or open access)
- **Well-documented** with stable APIs
- **Actively maintained** by reputable organizations
- **Relevant** to cybersecurity and threat intelligence

## Adding a New Data Source

### Step 1: Choose the Right Category

Place your source file in the appropriate directory:

```
sources/
├── vulnerability/           # CVEs, security advisories, exploit DBs
│   ├── cve/                # CVE databases
│   ├── advisory/           # Security bulletins
│   └── scoring/            # Risk scoring systems
├── threat-intelligence/     # Threat intel feeds
│   ├── ttps/               # Tactics, techniques, procedures
│   ├── iocs/               # Indicators of compromise
│   └── actors/             # Threat actor intelligence
└── osint/                  # Open source intelligence
    ├── reputation/         # IP/domain reputation
    └── sandbox/            # Malware analysis sandboxes
```

### Step 2: Use the Template

Start with our template file:

```bash
cp templates/source-metadata-template.json sources/[category]/[subcategory]/[your-source].json
```

### Step 3: Fill in Required Fields

#### Basic Information
```json
{
  "id": "unique-source-id",
  "name": "Official Source Name",
  "description": "Clear, concise description of what this source provides",
  "category": "vulnerability|threat-intelligence|osint",
  "subcategory": "specific-subcategory",
  "authority": "official|community|commercial",
  "website": "https://source-homepage.com",
  "documentation": "https://source-docs.com/api"
}
```

#### API Documentation
```json
"api": {
  "type": "REST|GraphQL|WebSocket",
  "base_url": "https://api.example.com/v1",
  "endpoints": [
    {
      "path": "/endpoint",
      "method": "GET|POST|PUT|DELETE",
      "description": "What this endpoint does",
      "parameters": [
        {
          "name": "param_name",
          "type": "string|integer|boolean",
          "required": true|false,
          "description": "What this parameter does",
          "example": "example_value"
        }
      ],
      "response_format": {
        "type": "JSON|XML|CSV",
        "example": {}
      },
      "rate_limit": {
        "requests_per_minute": 60,
        "notes": "Additional rate limit information"
      }
    }
  ]
}
```

#### Authentication
```json
"authentication": {
  "type": "none|api_key|oauth2|basic",
  "required": true|false,
  "registration_url": "https://example.com/register",
  "setup_instructions": [
    "Step 1: Register at the URL above",
    "Step 2: Navigate to API settings",
    "Step 3: Generate an API key",
    "Step 4: Store key in environment variable"
  ]
}
```

### Step 4: Add Integration Examples

Provide working code examples in at least Python and curl:

```json
"integration_examples": {
  "python": {
    "basic_fetch": "# Minimal working example",
    "error_handling": "# Example with proper error handling",
    "full_example": "# Complete implementation with best practices"
  },
  "curl": {
    "basic_fetch": "curl -X GET 'https://api.example.com/data'",
    "with_auth": "curl -H 'API-Key: YOUR_KEY' 'https://api.example.com/data'"
  },
  "javascript": {
    "basic_fetch": "// Optional but recommended"
  },
  "go": {
    "basic_fetch": "// Optional but recommended"
  }
}
```

### Step 5: Include Operational Guidance

Help users avoid common pitfalls:

```json
"operational_guidance": {
  "recommended_update_frequency": "How often to fetch data",
  "best_practices": [
    "Use caching to respect rate limits",
    "Implement exponential backoff on errors",
    "Store API keys securely"
  ],
  "common_pitfalls": [
    "Rate limiting without API key",
    "Not handling pagination",
    "Ignoring update timestamps"
  ],
  "cost_considerations": {
    "pricing_model": "free|freemium|paid",
    "free_tier_limits": "What's included for free",
    "paid_tiers": "Pricing information if applicable"
  }
}
```

## Updating Existing Sources

When updating an existing source:

1. **Verify all endpoints** still work
2. **Update any deprecated parameters**
3. **Add new endpoints or features**
4. **Test all code examples**
5. **Update the `last_updated` field**
6. **Document what changed** in your PR

## Quality Standards

### Required Elements

✅ Every source MUST include:
- Unique ID and descriptive name
- Clear description of the data provided
- Correct categorization
- Working API documentation
- At least Python and curl examples
- Rate limiting information
- Authentication setup (if required)

### Code Examples Standards

All code examples must:
- **Actually work** when copy-pasted
- **Handle errors** appropriately
- **Include comments** explaining key steps
- **Follow language conventions** (PEP 8 for Python, etc.)
- **Use environment variables** for sensitive data

Example of a good Python implementation:

```python
#!/usr/bin/env python3
"""
Example client for [Source Name] API
Demonstrates authentication, error handling, and rate limiting
"""

import os
import time
import requests
from typing import Optional, Dict, Any

class SourceClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('SOURCE_API_KEY')
        self.base_url = 'https://api.example.com/v1'
        self.session = requests.Session()
        if self.api_key:
            self.session.headers['API-Key'] = self.api_key
    
    def get_data(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Fetch data with automatic retry on rate limiting"""
        url = f"{self.base_url}/resource/{resource_id}"
        
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    time.sleep(retry_after)
                else:
                    response.raise_for_status()
                    
            except requests.RequestException as e:
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

# Example usage
if __name__ == '__main__':
    client = SourceClient()
    data = client.get_data('example-123')
    if data:
        print(f"Retrieved: {data}")
```

### Documentation Standards

- Use clear, concise language
- Avoid jargon without explanation
- Include practical examples
- Document all parameters and options
- Specify data types and formats
- Include response examples

## Testing Your Contribution

Before submitting, test your source documentation:

### 1. Validate JSON Schema

```bash
# Install jsonschema if needed
pip install jsonschema

# Validate your source file
python -c "
import json
import jsonschema

# Load your source file
with open('sources/your-category/your-source.json') as f:
    source = json.load(f)

# Load the schema
with open('schemas/source.schema.json') as f:
    schema = json.load(f)

# Validate
jsonschema.validate(source, schema)
print('✓ Schema validation passed')
"
```

### 2. Test API Endpoints

Verify each endpoint returns expected data:

```bash
# Test basic endpoint
curl -X GET 'https://api.example.com/endpoint'

# Test with authentication if required
curl -H 'API-Key: YOUR_KEY' 'https://api.example.com/endpoint'
```

### 3. Test Code Examples

Run each code example to ensure it works:

```bash
# Test Python examples
python3 your_example.py

# Test JavaScript examples  
node your_example.js

# Test Go examples
go run your_example.go
```

### 4. Check for Sensitive Data

Ensure no API keys or sensitive data are included:

```bash
# Search for potential API keys
grep -r "api[_-]key.*=" sources/
grep -r "token.*=" sources/
grep -r "secret" sources/
```

## Submission Process

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/data-sources.git
cd data-sources
git checkout -b add-source-name
```

### 2. Make Your Changes

```bash
# Add your source file
cp templates/source-metadata-template.json sources/category/your-source.json
# Edit the file with your source information
```

### 3. Commit Your Changes

```bash
git add sources/category/your-source.json
git commit -m "Add [Source Name] to [category] sources

- Comprehensive API documentation
- Python, JavaScript, Go, and curl examples
- Authentication setup instructions
- Rate limiting and best practices"
```

### 4. Submit Pull Request

1. Push your branch: `git push origin add-source-name`
2. Open a pull request on GitHub
3. Fill out the PR template completely
4. Link to any relevant documentation

### PR Template

```markdown
## New Data Source: [Source Name]

### Checklist
- [ ] Source file validates against schema
- [ ] All API endpoints tested and working
- [ ] Code examples tested in all languages provided
- [ ] No API keys or sensitive data included
- [ ] Documentation is clear and complete
- [ ] Appropriate category and subcategory selected

### Source Details
- **Category:** vulnerability/threat-intelligence/osint
- **Authority:** official/community/commercial
- **API Type:** REST/GraphQL/WebSocket
- **Authentication:** none/api_key/oauth2
- **Rate Limits:** [Specify limits]

### Testing
Describe how you tested the endpoints and examples:
- [ ] Endpoint 1: [Test description]
- [ ] Endpoint 2: [Test description]
- [ ] Python example: [Test result]
- [ ] Curl example: [Test result]

### Additional Notes
[Any additional information about this source]
```

## Getting Help

If you need assistance:

1. **Check existing sources** for examples
2. **Open an issue** for questions
3. **Join discussions** in GitHub Discussions
4. **Review closed PRs** for similar contributions

## Code of Conduct

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## Recognition

Contributors will be recognized in:
- The source file's `metadata.contributors` field
- The project's CONTRIBUTORS.md file
- Release notes for significant contributions

Thank you for helping make this catalog more comprehensive and useful for the security community!