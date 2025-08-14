# Project Plan: Data Sources Manager

**Last Updated:** 2025-04-22

---

## 1. Project Overview

The **data-sources-manager** repository will serve as a centralized, version‑controlled catalog of high‑quality data feeds for LLM‑based projects, with an initial focus on vulnerability research. It will streamline source discovery, scoring, and consumption, enabling consistent, automated integration of reliable information into downstream workflows.

## 2. Objectives

1. Define a reusable folder structure and JSON metadata schema for tracking diverse source types.
2. Implement numeric quality scoring (0–100) plus user‑preference weights to prioritize sources.
3. Automate daily or weekly fetching, scoring, and indexing via CI workflows.
4. Provide clear contribution guidelines, including retirement (quality_score=0) of deprecated sources.
5. Enable fast, minimal‑token lookups via a lightweight index.

## 3. Scope

**In Scope:**
- JSON schema definitions for `source` and `quality` metadata.
- Configuration files for categories, tags, and scoring weights.
- Python tools: `fetch_sources.py`, `score_sources.py`, `index_sources.py`.
- CI/CD: GitHub Actions workflows for updating and validating artifacts.
- Documentation: `README.md`, `CONTRIBUTING.md`, and this `project_plan.md`.

**Out of Scope:**
- Language‑ or framework‑specific build pipelines.
- Production deployment scripts beyond GitHub Actions.

## 4. Deliverables

- **Scaffolding Prompt:** `SCAFFOLDING_PROMPT.md` (detailed instructions for LLM-based repo generation).
- **Folder Structure & Templates:** stub files and directories in `data-sources/`, `schemas/`, `config/`, and `tools/`.
- **JSON Schemas:** `source.schema.json`, `quality.schema.json`.
- **Config Files:** `categories.json`, `scoring-config.json`.
- **CI Workflows:** `update-sources.yml`, `lint-schemas.yml`.
- **Documentation:** `README.md`, `CONTRIBUTING.md`, `project_plan.md`.

## 5. Timeline

| Phase               | Tasks                                                      | Duration     |
|---------------------|------------------------------------------------------------|--------------|
| **Phase 1**         | Finalize schemas and folder structure; write scaffolding prompt | Week 1       |
| **Phase 2**         | Scaffold repository via LLM; review and commit templates    | Week 2       |
| **Phase 3**         | Implement and test Python tools; validate CI workflows      | Week 3       |
| **Phase 4**         | Write documentation; onboard contributors; finalize release  | Week 4       |

## 6. Roles & Responsibilities

- **Project Owner (William):** Define requirements, review scaffolding, approve merges.
- **Repo Automation:** LLM-assisted code generation for stubs and CI.
- **Contributors (future):** Add new sources, validate schemas, write tests.

## 7. Risks & Mitigations

- **Risk:** Outdated or broken feeds.  
  **Mitigation:** Automated fetch retries and fallback logic; health monitoring.

- **Risk:** Schema drift causing CI failures.  
  **Mitigation:** Strict schema validation in `lint-schemas.yml`.

- **Risk:** Excessive token usage in lookups.  
  **Mitigation:** Lean metadata design and lightweight index format.

## 8. Communication Plan

- **Weekly Sync:** Status updates in Slack channel `#data-sources-manager`.
- **GitHub Issues:** Track feature requests, bugs, and schema changes.
- **Documentation Updates:** Pull requests for any doc changes.

## 9. Success Metrics

- 100% of sources conform to JSON schemas.
- Automated update workflow runs successfully at least 95% of scheduled times.
- Average index lookup latency below 100 ms.
- Positive feedback from downstream consumers on ease of use.

## 10. Next Steps

1. Merge this `project_plan.md` into the main branch.  
2. Execute the scaffolding prompt in `SCAFFOLDING_PROMPT.md` to generate the initial structure.  
3. Review and iterate on generated templates and tools.  
4. Publish first release tag (`v0.1.0`).

## 11. Scaffolding Reference

For detailed repository structure, file templates, and instructions, refer to **`SCAFFOLDING_PROMPT.md`** in this repository.
