"""
Unit tests for Phase 1 data sources: Core Government & Standards Sources.

Tests the CISA KEV, MITRE ATT&CK, MITRE D3FEND, and EPSS data sources
to ensure they meet Phase 1 requirements and quality standards.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add tools directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

import fetch_sources
import score_sources


class TestPhase1Sources:
    """Test suite for Phase 1 Core Government & Standards Sources."""

    @pytest.fixture
    def phase1_sources(self) -> Dict[str, Dict[str, Any]]:
        """Load Phase 1 source files for testing."""
        sources = {}

        # Phase 1 source file paths
        phase1_files = {
            "cisa-kev": "data-sources/vulnerability/exploited/cisa-kev.json",
            "mitre-attack": "data-sources/threat-intelligence/ttps/mitre-attack.json",
            "mitre-defend": "data-sources/threat-intelligence/defensive/mitre-defend.json",
            "epss": "data-sources/vulnerability/scoring/epss.json",
        }

        base_path = Path(__file__).parent.parent.parent
        for source_id, file_path in phase1_files.items():
            full_path = base_path / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    sources[source_id] = json.load(f)

        return sources

    def test_phase1_sources_exist(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test that all Phase 1 sources exist and are loadable."""
        expected_sources = ["cisa-kev", "mitre-attack", "mitre-defend", "epss"]

        for source_id in expected_sources:
            assert source_id in phase1_sources, f"Phase 1 source {source_id} not found"
            assert isinstance(
                phase1_sources[source_id], dict
            ), f"Source {source_id} is not a valid dict"

    def test_cisa_kev_properties(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test CISA KEV source meets requirements."""
        kev = phase1_sources["cisa-kev"]

        # Basic properties
        assert kev["id"] == "cisa-kev"
        assert kev["name"] == "CISA Known Exploited Vulnerabilities (KEV)"
        assert kev["category"] == "vulnerability"
        assert kev["sub_category"] == "exploited"

        # High priority requirements
        assert kev["source_weight"] == 10, "CISA KEV should have highest weight"
        assert kev["authority"] == 100, "CISA KEV should have maximum authority"

        # Government source tags
        assert "government" in kev["tags"]
        assert "authoritative" in kev["tags"]
        assert "exploited-vulnerabilities" in kev["tags"]

        # API details
        assert "api_details" in kev
        assert kev["api_details"]["requires_auth"] is False
        assert "data_feed" in kev["api_details"]

        # Exploitation status
        assert "exploitation_status" in kev
        assert kev["exploitation_status"]["kev_listed"] is True
        assert kev["exploitation_status"]["active_exploitation"] is True

        # Data quality
        assert "data_quality" in kev
        assert kev["data_quality"]["confidence_score"] == 100
        assert kev["data_quality"]["source_authority"] == 100

    def test_mitre_attack_properties(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test MITRE ATT&CK source meets requirements."""
        attack = phase1_sources["mitre-attack"]

        # Basic properties
        assert attack["id"] == "mitre-attack"
        assert attack["name"] == "MITRE ATT&CK Framework"
        assert attack["category"] == "threat-intelligence"
        assert attack["sub_category"] == "ttps"

        # High weight for authoritative TTP source
        assert attack["source_weight"] == 9
        assert attack["authority"] == 100

        # STIX/CTI integration
        assert "mitre" in attack["tags"]
        assert "attack-framework" in attack["tags"]
        assert "stix" in attack["tags"]

        # Threat intelligence fields
        assert "threat_intelligence" in attack
        ti = attack["threat_intelligence"]
        assert "attack_techniques" in ti
        assert "iocs" in ti
        assert "threat_actors" in ti
        assert "cve_mappings" in ti

        # Coverage details
        assert "coverage_details" in attack
        coverage = attack["coverage_details"]
        assert "platforms" in coverage
        assert "attack_lifecycle" in coverage
        assert "technique_count" in coverage

    def test_mitre_defend_properties(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test MITRE D3FEND source meets requirements."""
        defend = phase1_sources["mitre-defend"]

        # Basic properties
        assert defend["id"] == "mitre-defend"
        assert (
            defend["name"]
            == "MITRE D3FEND - A Knowledge Graph of Cybersecurity Countermeasures"
        )
        assert defend["category"] == "threat-intelligence"
        assert defend["sub_category"] == "defensive"

        # Defensive framework weight
        assert defend["source_weight"] == 8
        assert defend["authority"] == 98

        # D3FEND specific tags
        assert "d3fend" in defend["tags"]
        assert "defensive-techniques" in defend["tags"]
        assert "countermeasures" in defend["tags"]

        # Threat intelligence with defensive measures
        assert "threat_intelligence" in defend
        ti = defend["threat_intelligence"]
        assert "defensive_measures" in ti
        assert "attack_techniques" in ti

        # Verify defensive measures structure
        if ti["defensive_measures"]:
            measure = ti["defensive_measures"][0]
            assert "technique_id" in measure
            assert "technique_name" in measure
            assert "effectiveness_score" in measure

        # API details for SPARQL and knowledge graph
        assert "api_details" in defend
        api = defend["api_details"]
        assert "sparql_endpoint" in api
        assert "ontology_api" in api

    def test_epss_properties(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test EPSS source meets requirements."""
        epss = phase1_sources["epss"]

        # Basic properties
        assert epss["id"] == "epss"
        assert epss["name"] == "EPSS - Exploit Prediction Scoring System"
        assert epss["category"] == "vulnerability"
        assert epss["sub_category"] == "scoring"

        # Scoring system weight
        assert epss["source_weight"] == 8
        assert epss["authority"] == 95

        # EPSS specific tags
        assert "epss" in epss["tags"]
        assert "exploit-prediction" in epss["tags"]
        assert "probabilistic-scoring" in epss["tags"]

        # Exploitation status with EPSS specifics
        assert "exploitation_status" in epss
        exp_status = epss["exploitation_status"]
        assert "epss_score" in exp_status
        assert "epss_percentile" in exp_status

        # Scoring methodology
        assert "scoring_methodology" in epss
        methodology = epss["scoring_methodology"]
        assert "model_type" in methodology
        assert "training_data" in methodology
        assert "features" in methodology
        assert "output" in methodology

        # Performance metrics
        assert "performance_metrics" in epss
        metrics = epss["performance_metrics"]
        assert "model_accuracy" in metrics
        assert "update_frequency" in metrics

    def test_threat_intelligence_schema_compliance(
        self, phase1_sources: Dict[str, Dict[str, Any]]
    ):
        """Test that threat intelligence fields follow the schema."""
        ti_sources = ["mitre-attack", "mitre-defend"]

        for source_id in ti_sources:
            source = phase1_sources[source_id]
            assert "threat_intelligence" in source

            ti = source["threat_intelligence"]

            # Check IOCs structure if present
            if "iocs" in ti and ti["iocs"]:
                for ioc in ti["iocs"]:
                    assert "type" in ioc
                    assert "format" in ioc
                    assert "confidence" in ioc
                    assert isinstance(ioc["confidence"], (int, float))
                    assert 0 <= ioc["confidence"] <= 100

    def test_exploitation_status_compliance(
        self, phase1_sources: Dict[str, Dict[str, Any]]
    ):
        """Test exploitation status fields follow the schema."""
        sources_with_exp_status = ["cisa-kev", "epss"]

        for source_id in sources_with_exp_status:
            source = phase1_sources[source_id]
            assert "exploitation_status" in source

            exp_status = source["exploitation_status"]

            # Validate EPSS score range if present
            if "epss_score" in exp_status and exp_status["epss_score"] is not None:
                assert 0 <= exp_status["epss_score"] <= 1

            # Validate EPSS percentile range if present
            if (
                "epss_percentile" in exp_status
                and exp_status["epss_percentile"] is not None
            ):
                assert 0 <= exp_status["epss_percentile"] <= 100

    def test_data_quality_scores(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test data quality scores meet Phase 1 standards."""
        for source_id, source in phase1_sources.items():
            assert "data_quality" in source

            dq = source["data_quality"]

            # All Phase 1 sources should have high confidence
            assert "confidence_score" in dq
            assert (
                dq["confidence_score"] >= 90
            ), f"{source_id} confidence too low: {dq['confidence_score']}"

            # Source authority should be high for government/standards sources
            assert "source_authority" in dq
            if source_id in ["cisa-kev", "mitre-attack"]:
                assert dq["source_authority"] >= 98, f"{source_id} authority too low"
            else:
                assert dq["source_authority"] >= 90, f"{source_id} authority too low"

            # Validation methods should be documented
            assert "validation_methods" in dq
            assert isinstance(dq["validation_methods"], list)
            assert len(dq["validation_methods"]) > 0

    def test_source_weights_hierarchy(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test that source weights follow expected hierarchy."""
        weights = {
            source_id: source["source_weight"]
            for source_id, source in phase1_sources.items()
        }

        # CISA KEV should have highest weight (government authority)
        assert weights["cisa-kev"] == 10

        # MITRE ATT&CK should be second highest (comprehensive TTP framework)
        assert weights["mitre-attack"] == 9

        # D3FEND and EPSS should be high but lower than KEV/ATT&CK
        assert weights["mitre-defend"] == 8
        assert weights["epss"] == 8

        # Verify all weights are in valid range
        for source_id, weight in weights.items():
            assert 0 <= weight <= 10, f"{source_id} weight {weight} out of range"

    def test_api_integration_readiness(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test that sources are ready for API integration."""
        for source_id, source in phase1_sources.items():
            assert "api_details" in source

            api = source["api_details"]

            # All sources should have documented API access
            assert "requires_auth" in api
            assert isinstance(api["requires_auth"], bool)

            # Should have clear data feed URL
            assert "data_feed" in api or "api_endpoint" in api

            # Update frequency should be documented
            assert "update_frequency" in api or "update_frequency" in source

            # Data formats should be specified
            assert "data_formats" in api
            assert isinstance(api["data_formats"], list)
            assert len(api["data_formats"]) > 0

    def test_framework_mappings(self, phase1_sources: Dict[str, Dict[str, Any]]):
        """Test framework mappings are present for integration."""
        for source_id, source in phase1_sources.items():
            if "frameworks_supported" in source:
                frameworks = source["frameworks_supported"]
                assert isinstance(frameworks, list)

                for framework in frameworks:
                    assert "name" in framework
                    assert "version" in framework
                    assert "mapping" in framework

    def test_usage_guidance_completeness(
        self, phase1_sources: Dict[str, Dict[str, Any]]
    ):
        """Test that usage guidance is comprehensive."""
        for source_id, source in phase1_sources.items():
            assert "usage_guidance" in source

            guidance = source["usage_guidance"]

            # Primary use cases should be documented
            assert "primary_use_cases" in guidance
            assert isinstance(guidance["primary_use_cases"], list)
            assert len(guidance["primary_use_cases"]) >= 3

            # Integration recommendations should be provided
            assert "integration_recommendations" in guidance
            assert isinstance(guidance["integration_recommendations"], list)
            assert len(guidance["integration_recommendations"]) >= 3

            # Automation potential should be assessed
            assert "automation_potential" in guidance
            assert isinstance(guidance["automation_potential"], str)


class TestPhase1Integration:
    """Integration tests for Phase 1 sources."""

    def test_load_phase1_sources_with_tools(self):
        """Test that Phase 1 sources can be loaded by existing tools."""
        # This should not raise an exception
        sources = fetch_sources.load_source_files()

        # Verify we can find Phase 1 sources
        phase1_ids = ["cisa-kev", "mitre-attack", "mitre-defend", "epss"]
        found_sources = {source["id"]: source for source in sources}

        for source_id in phase1_ids:
            assert (
                source_id in found_sources
            ), f"Phase 1 source {source_id} not loaded by tools"

    def test_scoring_with_new_fields(self):
        """Test that scoring tools handle new threat intelligence fields."""
        config = score_sources.load_scoring_config()
        sources = fetch_sources.load_source_files()

        # Find a Phase 1 source with new fields
        phase1_sources = [
            s
            for s in sources
            if s["id"] in ["cisa-kev", "mitre-attack", "mitre-defend", "epss"]
        ]
        assert len(phase1_sources) > 0

        # Test scoring doesn't fail with new fields
        for source in phase1_sources:
            try:
                score = score_sources.calculate_quality_score(
                    source, config.get("weights", {})
                )
                assert isinstance(score, (int, float))
                assert 0 <= score <= 100
            except Exception as e:
                pytest.fail(f"Scoring failed for {source['id']}: {e}")
