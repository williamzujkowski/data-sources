# Data Sources Documentation

## Overview
This document provides comprehensive information about each integrated data source, including their purpose, data structure, integration details, and usage guidelines.

## Table of Contents
- [Government Sources](#government-sources)
  - [CISA Known Exploited Vulnerabilities (KEV)](#cisa-known-exploited-vulnerabilities-kev)
  - [MITRE ATT&CK](#mitre-attck)
  - [MITRE D3FEND](#mitre-d3fend)
  - [EPSS (Exploit Prediction Scoring System)](#epss-exploit-prediction-scoring-system)
- [Community Sources](#community-sources)
  - [AlienVault OTX (Coming Soon)](#alienvault-otx-coming-soon)
  - [abuse.ch Suite (Coming Soon)](#abusech-suite-coming-soon)
  - [NVD (Coming Soon)](#nvd-coming-soon)

---

## Government Sources

### CISA Known Exploited Vulnerabilities (KEV)

**Purpose**: Track actively exploited vulnerabilities that pose immediate risk to organizations.

**Authority Score**: 10/10 - Highest authority as official US government confirmation of active exploitation

**Update Frequency**: Real-time (published as vulnerabilities are confirmed exploited)

**API Details**:
- **Base URL**: `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
- **Authentication**: None required
- **Rate Limits**: None
- **Format**: JSON

**Data Structure**:
```json
{
  "cve_id": "CVE-2024-12345",
  "vendor_project": "Example Corp",
  "product": "Example Product",
  "vulnerability_name": "Example Product Remote Code Execution Vulnerability",
  "date_added": "2024-01-15",
  "short_description": "Example Product contains an unspecified vulnerability that allows for remote code execution.",
  "required_action": "Apply updates per vendor instructions.",
  "due_date": "2024-02-05",
  "notes": "Additional context about the vulnerability"
}
```

**Key Fields**:
- `cve_id`: CVE identifier for the vulnerability
- `date_added`: When added to KEV catalog (indicates when exploitation was confirmed)
- `required_action`: Mandatory remediation action for federal agencies
- `due_date`: Compliance deadline for federal agencies

**Integration Notes**:
- This source has the highest weight in our scoring algorithm (10/10)
- Any CVE in this list should be treated as critical priority
- Used as the primary indicator for `exploitation_status.kev_listed` field

**Usage Example**:
```python
# Check if a CVE is actively exploited
def is_actively_exploited(cve_id):
    kev_data = load_kev_data()
    return any(entry['cve_id'] == cve_id for entry in kev_data)
```

**License**: Public Domain

---

### MITRE ATT&CK

**Purpose**: Comprehensive framework of adversary tactics, techniques, and procedures (TTPs) based on real-world observations.

**Authority Score**: 10/10 - Industry standard for threat intelligence and detection engineering

**Update Frequency**: Quarterly (major releases) with periodic minor updates

**API Details**:
- **STIX/TAXII API**: `https://cti-taxii.mitre.org/taxii/`
- **GitHub**: `https://github.com/mitre/cti`
- **Authentication**: None required
- **Rate Limits**: Reasonable use expected
- **Formats**: STIX 2.1, JSON

**Data Structure**:
```json
{
  "technique_id": "T1055",
  "name": "Process Injection",
  "description": "Process injection is a method of executing arbitrary code...",
  "platforms": ["Windows", "Linux", "macOS"],
  "tactics": ["Defense Evasion", "Privilege Escalation"],
  "detection": "Monitoring Windows API calls...",
  "mitigations": ["M1040", "M1026"],
  "data_sources": ["Process monitoring", "API monitoring"],
  "examples": [
    {
      "threat_actor": "APT28",
      "software": "CHOPSTICK",
      "description": "APT28 has used process injection..."
    }
  ]
}
```

**Key Concepts**:
- **Tactics**: High-level adversary objectives (e.g., Initial Access, Persistence)
- **Techniques**: How adversaries achieve tactical objectives
- **Sub-techniques**: More specific implementations of techniques
- **Procedures**: Specific implementations used by threat actors

**Integration Notes**:
- Maps to CVEs through technique references
- Used to enrich vulnerability data with attacker context
- Provides detection and mitigation guidance

**Usage Example**:
```python
# Find all techniques used by a specific threat actor
def get_actor_techniques(actor_name):
    attack_data = load_attack_data()
    return [
        tech for tech in attack_data['techniques']
        if any(ex['threat_actor'] == actor_name for ex in tech.get('examples', []))
    ]
```

**License**: Apache 2.0

---

### MITRE D3FEND

**Purpose**: Knowledge graph of defensive cybersecurity countermeasures and their relationships to offensive techniques.

**Authority Score**: 9/10 - Authoritative defensive framework complementing ATT&CK

**Update Frequency**: Periodic updates aligned with research publications

**API Details**:
- **SPARQL Endpoint**: `https://d3fend.mitre.org/sparql`
- **JSON-LD API**: `https://d3fend.mitre.org/api/`
- **Authentication**: None required
- **Rate Limits**: Standard web service limits
- **Formats**: RDF, JSON-LD, SPARQL results

**Data Structure**:
```json
{
  "technique_id": "D3-PSA",
  "name": "Process Spawn Analysis",
  "description": "Analyzing the spawn of a process...",
  "defeats": ["T1055", "T1055.001", "T1055.002"],
  "parent_technique": "D3-PA",
  "artifacts": ["Process", "File", "Network Traffic"],
  "effectiveness": {
    "high": ["T1055.001"],
    "medium": ["T1055.002"],
    "low": ["T1055.003"]
  },
  "implementation_examples": [
    {
      "product": "Windows Defender",
      "capability": "Behavior monitoring"
    }
  ]
}
```

**Key Concepts**:
- **Defensive Techniques**: Specific methods to detect or prevent attacks
- **Digital Artifacts**: Observable evidence of system activity
- **Defeats Relationships**: Mappings between defenses and ATT&CK techniques
- **Effectiveness Scores**: Relative effectiveness of defenses

**Integration Notes**:
- Provides defensive context for vulnerabilities
- Maps to ATT&CK techniques for comprehensive coverage
- Useful for prioritizing security controls

**Usage Example**:
```python
# Find defenses for a specific ATT&CK technique
def get_defenses_for_technique(attack_technique):
    d3fend_data = load_d3fend_data()
    return [
        defense for defense in d3fend_data['techniques']
        if attack_technique in defense.get('defeats', [])
    ]
```

**License**: MIT

---

### EPSS (Exploit Prediction Scoring System)

**Purpose**: Machine learning model that predicts the probability of a vulnerability being exploited in the wild within 30 days.

**Authority Score**: 9/10 - Data-driven predictions based on extensive threat intelligence

**Update Frequency**: Daily updates with new predictions

**API Details**:
- **Base URL**: `https://api.first.org/data/v1/epss`
- **Authentication**: Optional (higher rate limits with API key)
- **Rate Limits**: 100 requests/minute (authenticated: 1000/minute)
- **Format**: JSON, CSV

**Data Structure**:
```json
{
  "cve": "CVE-2024-12345",
  "epss": 0.89234,
  "percentile": 0.98765,
  "date": "2024-01-15",
  "model_version": "2023.03.01",
  "features": {
    "cvss_score": 9.8,
    "days_since_published": 15,
    "exploit_code_maturity": "functional",
    "references_count": 45,
    "twitter_mentions": 234
  }
}
```

**Key Metrics**:
- `epss`: Probability score (0-1) of exploitation within 30 days
- `percentile`: Relative ranking compared to all CVEs (0-100)
- `model_version`: Version of the ML model used for prediction

**Model Features** (used in predictions):
- CVSS scores and metrics
- Time since publication
- Exploit availability indicators
- Social media activity
- Threat intelligence references

**Integration Notes**:
- Updated daily with rolling 30-day predictions
- Complements KEV with predictive capabilities
- Useful for prioritizing patching when combined with CVSS

**Interpretation Guidelines**:
- **EPSS > 0.9**: Very high probability of exploitation
- **EPSS 0.5-0.9**: High probability, prioritize patching
- **EPSS 0.1-0.5**: Moderate probability, monitor closely
- **EPSS < 0.1**: Low probability, standard patching cycle

**Usage Example**:
```python
# Prioritize vulnerabilities by exploitation probability
def prioritize_by_epss(cves, threshold=0.5):
    epss_data = load_epss_scores()
    return sorted(
        [cve for cve in cves if epss_data.get(cve, {}).get('epss', 0) > threshold],
        key=lambda x: epss_data[x]['epss'],
        reverse=True
    )
```

**License**: Creative Commons

---

## Community Sources

### AlienVault OTX (Coming Soon)

**Purpose**: Open threat intelligence community for sharing indicators of compromise (IOCs) and threat data.

**Planned Features**:
- Pulse subscriptions for real-time threat feeds
- IOC extraction and categorization
- Threat actor attribution
- Geographic and industry targeting information

---

### abuse.ch Suite (Coming Soon)

**Purpose**: Collection of malware and botnet tracking projects providing real-time threat feeds.

**Planned Feeds**:
- **URLhaus**: Malicious URL feed
- **Malware Bazaar**: Malware sample sharing
- **Feodo Tracker**: Banking trojan C2 tracking
- **ThreatFox**: IOC sharing platform

---

### NVD (Coming Soon)

**Purpose**: Comprehensive vulnerability database maintained by NIST with detailed vulnerability information.

**Planned Features**:
- CVE details with CVSS scoring
- CPE (product) mappings
- CWE classifications
- Reference links and patches

---

## Integration Guidelines

### Adding a New Source

1. **Create source metadata file** in appropriate category directory
2. **Implement fetcher** if API integration needed
3. **Map to schema** ensuring all required fields are populated
4. **Add tests** for source validation and fetching
5. **Document** in this file with complete details
6. **Set authority score** based on source credibility (1-10)

### Source Quality Criteria

Sources are evaluated on:
- **Authority**: Credibility and official status
- **Freshness**: Update frequency and timeliness
- **Coverage**: Breadth and depth of data
- **Availability**: API reliability and rate limits
- **Accuracy**: False positive rate and data quality

### Data Normalization

All sources must:
- Use consistent date formats (ISO 8601)
- Map to standard identifiers (CVE, CWE, CPE)
- Provide English descriptions
- Include source attribution
- Maintain data lineage

---

## API Rate Limiting Guidelines

To maintain good relationships with data providers:
- Respect published rate limits
- Implement exponential backoff on errors
- Cache responses appropriately
- Use conditional requests (If-Modified-Since)
- Register for API keys where available

## License Compliance

Each source's license must be:
- Documented in metadata
- Compatible with project usage
- Properly attributed in outputs
- Reviewed for commercial use restrictions

## Contact Information

For questions about specific sources or integration issues:
- GitHub Issues: [data-sources/issues](https://github.com/williamzujkowski/data-sources/issues)
- Documentation: This file and source metadata files
- Schema: `/schemas/source.schema.json`
