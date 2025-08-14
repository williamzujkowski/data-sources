# Data Sources

This page provides details about the available data sources in the repository.

## Vulnerability Data Sources

### National Vulnerability Database (NVD)

- **ID**: `nvd-cve`
- **URL**: [https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz](https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz)
- **Description**: NIST National Vulnerability Database CVE feed
- **Category**: vulnerability
- **Sub-category**: cve
- **Format**: json
- **Quality Score**: 95

The National Vulnerability Database (NVD) is the U.S. government repository of standards-based vulnerability management data. It includes databases of security checklist references, security-related software flaws, misconfigurations, product names, and impact metrics.

### MITRE Common Vulnerabilities and Exposures (CVE)

- **ID**: `mitre-cve`
- **URL**: [https://cve.mitre.org/data/downloads/](https://cve.mitre.org/data/downloads/)
- **Description**: Official CVE dictionary and standard identification method for publicly known cybersecurity vulnerabilities
- **Category**: vulnerability
- **Sub-category**: cve
- **Format**: xml
- **Quality Score**: 95

The MITRE CVE database is the authoritative source for CVE identifiers, providing a standardized identifier for known cybersecurity vulnerabilities.

### AlienVault Open Threat Exchange (OTX)

- **ID**: `alienvault-otx`
- **URL**: [https://otx.alienvault.com/api](https://otx.alienvault.com/api)
- **Description**: Crowd-sourced threat intelligence sharing platform with real-time threat data
- **Category**: vulnerability
- **Sub-category**: threat-intelligence
- **Format**: json
- **Quality Score**: 85

AlienVault OTX provides a community platform for sharing threat intelligence data, including indicators of compromise (IOCs) related to vulnerabilities.

### Zero Day Initiative (ZDI)

- **ID**: `zero-day-initiative`
- **URL**: [https://www.zerodayinitiative.com/advisories/published/](https://www.zerodayinitiative.com/advisories/published/)
- **Description**: Vulnerability acquisition program that procures zero-day vulnerabilities from security researchers
- **Category**: vulnerability
- **Sub-category**: advisory
- **Format**: rss
- **Quality Score**: 90

The Zero Day Initiative is a program for rewarding security researchers for responsibly disclosing vulnerabilities, providing early warning of zero-day vulnerabilities.

### CERT Coordination Center Vulnerability Notes

- **ID**: `cert-vn`
- **URL**: [https://www.kb.cert.org/vuls/](https://www.kb.cert.org/vuls/)
- **Description**: Technical documents describing vulnerabilities, their impact, and mitigations from Carnegie Mellon University's CERT/CC
- **Category**: vulnerability
- **Sub-category**: advisory
- **Format**: json
- **Quality Score**: 85

The CERT Coordination Center produces vulnerability notes for selected vulnerabilities to provide accurate, neutral technical information.

### Exploit Database

- **ID**: `exploit-db`
- **URL**: [https://www.exploit-db.com/search?type=json](https://www.exploit-db.com/search?type=json)
- **Description**: Archive of publicly disclosed security vulnerabilities and exploits
- **Category**: vulnerability
- **Sub-category**: exploit
- **Format**: json
- **Quality Score**: 90

The Exploit Database is a repository of public exploits and vulnerable software, maintained by Offensive Security.

### VulDB Vulnerability Database

- **ID**: `vuldb`
- **URL**: [https://vuldb.com/](https://vuldb.com/)
- **Description**: Independent and comprehensive vulnerability database documenting, explaining and rating vulnerabilities
- **Category**: vulnerability
- **Sub-category**: database
- **Format**: json
- **Quality Score**: 80

VulDB is a commercial vulnerability database with detailed information about vulnerabilities and affected products.

### SANS Internet Storm Center

- **ID**: `sans-isc`
- **URL**: [https://isc.sans.edu/api/](https://isc.sans.edu/api/)
- **Description**: Cooperative cybersecurity monitoring system with daily reports on emerging threats and vulnerabilities
- **Category**: vulnerability
- **Sub-category**: threat-intelligence
- **Format**: json
- **Quality Score**: 85

The SANS Internet Storm Center provides early warning of emerging threats and vulnerabilities.

### CISA Known Exploited Vulnerabilities Catalog

- **ID**: `cisa-kev`
- **URL**: [https://www.cisa.gov/known-exploited-vulnerabilities-catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **Description**: CISA's authoritative source of vulnerabilities that have been actively exploited in the wild
- **Category**: vulnerability
- **Sub-category**: exploited
- **Format**: json
- **Quality Score**: 95

The CISA Known Exploited Vulnerabilities (KEV) Catalog lists vulnerabilities that are being actively exploited by threat actors.

## Adding New Sources

To add new data sources, see the [Contributing Guide](../development/contributing.md).
