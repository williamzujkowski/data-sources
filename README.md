# Threat Intelligence Data Sources Catalog

A comprehensive metadata catalog for threat intelligence and cybersecurity data sources. This repository provides structured documentation on how to access and integrate various security data feeds, APIs, and services.

## 🎯 Purpose

This repository answers one key question: **"How do I access this data source?"**

We provide:
- 📚 Comprehensive API documentation
- 🔐 Authentication setup instructions  
- 💻 Working code examples in multiple languages
- 🚀 Integration patterns and best practices
- ⚡ Rate limiting and optimization guidance

## 📂 Repository Structure

```
data-sources/
├── sources/                    # Data source metadata files
│   ├── vulnerability/          # Vulnerability databases
│   │   ├── cve/               # CVE sources (NVD, MITRE)
│   │   ├── advisory/          # Security advisories (CISA KEV)
│   │   └── scoring/           # Risk scoring (EPSS, CVSS)
│   ├── threat-intelligence/    # Threat intel feeds
│   │   ├── ttps/              # Tactics, Techniques, Procedures
│   │   ├── iocs/              # Indicators of Compromise
│   │   └── actors/            # Threat actor intelligence
│   └── osint/                  # Open Source Intelligence
├── schemas/                    # JSON schemas for validation
└── templates/                  # Templates for new sources
```

## 🚀 Quick Start

### Finding a Data Source

Browse the `sources/` directory by category or use git to search:

```bash
# Find all CVE-related sources
find sources -name "*.json" | xargs grep -l "cve"

# Search for sources with API access
grep -r "api_key" sources/
```

### Using a Data Source

Each source file contains:

1. **Basic Information** - Name, description, category
2. **API Documentation** - Endpoints, parameters, authentication
3. **Integration Examples** - Working code in Python, JavaScript, Go, and curl
4. **Operational Guidance** - Best practices, rate limits, common pitfalls

Example: Accessing the National Vulnerability Database (NVD)

```python
import requests
import os

# Simple CVE lookup
url = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
headers = {'apiKey': os.environ.get('NVD_API_KEY')}  # Optional but recommended

params = {'cveId': 'CVE-2021-44228'}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    cve = data['vulnerabilities'][0]['cve']
    print(f"{cve['id']}: {cve['descriptions'][0]['value']}")
```

## 📊 Featured Data Sources

### Vulnerability Databases
- **[NVD](sources/vulnerability/cve/nvd.json)** - NIST National Vulnerability Database
  - Comprehensive CVE data with CVSS scores
  - Free API with optional key for higher rate limits
  - Real-time updates

- **[CISA KEV](sources/vulnerability/advisory/cisa-kev.json)** - Known Exploited Vulnerabilities
  - Actively exploited vulnerabilities
  - Remediation deadlines
  - Ransomware associations

- **[EPSS](sources/vulnerability/scoring/epss.json)** - Exploit Prediction Scoring System
  - Probabilistic exploitation scoring
  - Daily updates
  - Risk prioritization data

### Threat Intelligence
- **[MITRE ATT&CK](sources/threat-intelligence/ttps/mitre-attack.json)** - Adversary tactics and techniques
  - STIX 2.1 format
  - Technique detection rules
  - Actor mappings

## 💡 Common Integration Patterns

### 1. Caching Strategy
Most APIs have rate limits. Implement caching:

```python
import json
import time
from pathlib import Path

def fetch_with_cache(url, cache_file, max_age=3600):
    cache_path = Path(cache_file)
    
    # Check cache age
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < max_age:
            return json.loads(cache_path.read_text())
    
    # Fetch fresh data
    response = requests.get(url)
    data = response.json()
    
    # Update cache
    cache_path.write_text(json.dumps(data))
    return data
```

### 2. Rate Limit Handling
Respect API rate limits with exponential backoff:

```python
def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt * 60
                time.sleep(wait_time)
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

### 3. Batch Processing
For large datasets, use pagination:

```python
def fetch_all_pages(base_url, params=None):
    all_results = []
    params = params or {}
    params['resultsPerPage'] = 100
    params['startIndex'] = 0
    
    while True:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        all_results.extend(data.get('results', []))
        
        if params['startIndex'] + params['resultsPerPage'] >= data['totalResults']:
            break
            
        params['startIndex'] += params['resultsPerPage']
        time.sleep(1)  # Be nice to the API
    
    return all_results
```

## 🔑 Authentication Methods

### API Keys
Most sources offer free API keys for higher rate limits:

| Source | Free Tier | With API Key | Registration |
|--------|-----------|--------------|--------------|
| NVD | 50 requests/30 days | 50,000 requests/30 days | [Register](https://nvd.nist.gov/developers/request-an-api-key) |
| VirusTotal | 4 requests/minute | 500 requests/day | [Register](https://www.virustotal.com/gui/join-us) |

### No Authentication Required
These sources provide public access:
- CISA KEV Catalog
- MITRE ATT&CK Framework
- EPSS Scores

## 📝 Data Source Schema

Each source follows our [standard schema](schemas/source.schema.json):

```json
{
  "id": "unique-source-id",
  "name": "Human Readable Name",
  "category": "vulnerability|threat-intelligence|osint",
  "authority": "official|community|commercial",
  "api": {
    "base_url": "https://api.example.com",
    "endpoints": [...],
    "rate_limit": {...}
  },
  "authentication": {...},
  "integration_examples": {...},
  "operational_guidance": {...}
}
```

## 🤝 Contributing

We welcome contributions! To add a new data source:

1. **Use the template**: Copy `templates/source-metadata-template.json`
2. **Follow the schema**: Validate against `schemas/source.schema.json`
3. **Include examples**: Provide working code in at least Python and curl
4. **Document thoroughly**: Include authentication setup and common pitfalls
5. **Test your examples**: Ensure all code examples actually work

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📊 Quality Standards

All data sources are evaluated on:
- **Completeness** - API documentation, examples, error handling
- **Accuracy** - Verified endpoints, correct parameters
- **Timeliness** - Recently tested and validated
- **Usability** - Clear instructions, working examples

## 🔍 Use Cases

This catalog supports:
- **Security Operations Centers (SOCs)** - Vulnerability prioritization
- **Threat Intelligence Teams** - Feed aggregation and enrichment
- **DevSecOps** - Automated vulnerability scanning
- **Incident Response** - Threat actor attribution
- **Risk Management** - Exploitation probability assessment

## 📚 Additional Resources

- [FIRST CVE Services](https://www.first.org/cvss/)
- [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
- [CISA Cybersecurity Resources](https://www.cisa.gov/resources-tools/resources)
- [EPSS Model Documentation](https://www.first.org/epss/model)

## 📄 License

This metadata catalog is provided under the MIT License. Individual data sources maintain their own licensing terms.

## 🙏 Acknowledgments

This catalog aggregates metadata about publicly available data sources. We acknowledge and respect the work of all organizations providing these valuable security resources to the community.

---

**Note**: This repository contains metadata and documentation only. For actual threat data, please access the sources directly using the provided integration examples.