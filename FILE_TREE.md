# Repository File Structure

This document provides a hierarchical representation of the project's file structure. It serves as a map of the codebase for both developers and AI tools.

## Root Level Files

- **README.md** - Project overview, introduction, and quick start guide
- **CONTRIBUTING.md** - Guidelines for contributing to the project
- **SECURITY.md** - Security policies and vulnerability reporting procedure
- **LICENSE** - Project license information
- **USAGE_GUIDE.md** - Detailed instructions on how to use the project
- **PROJECT_PLAN.md** - Overall project vision, objectives, and roadmap
- **CLAUDE.md** - Comprehensive guidance for Claude AI when working with this codebase
- **FILE_TREE.md** - This file, providing a map of the codebase structure
- **CODEOWNERS** - Defines individuals or teams responsible for code in the repository
- **SCAFFOLDING_PROMPT.md** - Provides guidance for initial project setup
- **mkdocs.yml** - Configuration for the MkDocs documentation system

## Core Directories

### `/config`
Contains configuration files for the project.
- **categories.json** - Defines data source categories and classifications
- **scoring-config.json** - Configuration for the scoring system

### `/data-sources`
Houses the actual data source definitions and examples.
- `/vulnerability` - Vulnerability data sources
  - **cert-vn.json** - CERT Vulnerability Notes data source
  - **cisa-kev.json** - CISA Known Exploited Vulnerabilities data source
  - **exploit-db.json** - Exploit Database data source
  - **mitre-cve.json** - MITRE CVE data source
  - **otx.json** - AlienVault OTX data source
  - **sans-isc.json** - SANS Internet Storm Center data source
  - **vuldb.json** - VulDB data source
  - **zdi.json** - Zero Day Initiative data source
  - `/cve` - Common Vulnerabilities and Exposures sources
    - **nvd.json** - National Vulnerability Database source
    - **vendor-advisory.json** - Vendor security advisories

### `/docs`
Project documentation organized by topic.
- **index.md** - Documentation home page
- **API_KEYS.md** - Information about API keys used in the project
- **SECRETS_MANAGEMENT.md** - Guidelines for managing secrets
- **github-pages-setup.md** - Instructions for setting up GitHub Pages
- `/api` - API documentation
  - **python-tools.md** - Documentation for Python tools
  - **quality-schema.md** - Documentation for the quality schema
  - **source-schema.md** - Documentation for the source schema
- `/development` - Developer documentation
  - **api-keys.md** - Guidance on using API keys in development
  - **architecture.md** - Architectural overview of the project
  - **contributing.md** - Detailed contributing guidelines
  - **secrets-management.md** - Procedures for managing secrets in development
- `/getting-started` - Onboarding documentation
  - **configuration.md** - Configuration instructions
  - **installation.md** - Installation guide
  - **quickstart.md** - Quick start tutorial
- `/usage` - Usage documentation
  - **data-sources.md** - Information on working with data sources
  - **querying.md** - Guide to querying the data
  - **scoring.md** - Explanation of the scoring system

### `/schemas`
JSON schemas for validation.
- **quality.schema.json** - Schema for data quality assessment
- **source.schema.json** - Schema for data source definitions

### `/tools`
Utility scripts and tools for working with the project.
- **fetch_sources.py** - Script to fetch data from sources
- **index_sources.py** - Script to index sources for searching
- **score_sources.py** - Script to score sources based on various metrics
- **serve_docs.py** - Script to serve documentation locally
- **validate_api_keys.py** - Script to validate API keys
- **validate_sources.py** - Script to validate data source configurations
- **requirements.txt** - Python dependencies for the tools

### `/ISSUE_TEMPLATE`
Templates for GitHub issues.
- **bug_report.md** - Template for bug reports
- **feature_request.md** - Template for feature requests
- **config.yml** - Configuration for issue templates

### `/workflows`
GitHub Actions workflows for CI/CD.
- **ci.yml** - Continuous integration workflow
- **codeql-analysis.yml** - CodeQL security analysis workflow
- **dependency-review.yml** - Dependency review workflow

## Special Files

- **pull_request_template.md** - Template for pull requests
- **dependabot.yml** - Configuration for Dependabot dependency updates

---

**Note:** This file should be kept updated whenever the repository structure changes to ensure an accurate representation of the codebase.