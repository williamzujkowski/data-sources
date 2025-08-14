"""Tests for source quality analyzer."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from tools.quality_analyzer import (
    QualityMetrics,
    SourceQualityAnalyzer,
    SourceQualityReport,
)


class TestQualityAnalyzer:
    """Test quality analyzer functionality."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create quality analyzer instance."""
        history_file = tmp_path / "quality_history.json"
        return SourceQualityAnalyzer(str(history_file))

    @pytest.fixture
    def sample_vulnerability_data(self):
        """Sample vulnerability data for testing."""
        now = datetime.utcnow()
        return [
            {
                "cve_id": "CVE-2024-1234",
                "description": "Critical SQL injection vulnerability",
                "published": now.isoformat(),
                "cvss_score": 9.8,
                "source": "nvd",
                "cwe_ids": ["CWE-89"],
                "references": ["https://example.com/advisory"],
            },
            {
                "cve_id": "CVE-2024-5678",
                "description": "XSS vulnerability in web application",
                "published": (now - timedelta(hours=6)).isoformat(),
                "cvss_score": 6.1,
                "source": "nvd",
                "cwe_ids": ["CWE-79"],
            },
            {
                "cve_id": "CVE-2024-9999",
                "description": "Buffer overflow",
                "published": (now - timedelta(days=3)).isoformat(),
                "cvss_score": 7.5,
                "source": "nvd",
            },
        ]

    def test_analyze_source_with_good_data(self, analyzer, sample_vulnerability_data):
        """Test analysis with high-quality data."""
        report = analyzer.analyze_source(
            "nvd", sample_vulnerability_data, "vulnerability"
        )

        assert isinstance(report, SourceQualityReport)
        assert report.source_id == "nvd"
        assert report.data_samples == 3
        assert report.metrics.overall_score > 0.7
        assert len(report.issues) == 0 or all(
            "below" not in issue for issue in report.issues
        )

    def test_analyze_source_with_empty_data(self, analyzer):
        """Test analysis with empty data."""
        report = analyzer.analyze_source("test_source", [], "vulnerability")

        assert report.source_id == "test_source"
        assert report.data_samples == 0
        assert report.metrics.overall_score == 0
        assert "No data available" in report.issues[0]

    def test_freshness_calculation(self, analyzer):
        """Test freshness score calculation."""
        now = datetime.utcnow()
        data = [
            {"published": now.isoformat()},  # Fresh
            {"published": (now - timedelta(hours=24)).isoformat()},  # 1 day old
            {"published": (now - timedelta(hours=72)).isoformat()},  # 3 days old
        ]

        score = analyzer._calculate_freshness(data)

        # Fresh item should score 1.0
        # 1-day old should score ~0.5 (24/48)
        # 3-day old should score 0 (>48 hours)
        # Average should be around 0.5
        assert 0.4 <= score <= 0.6

    def test_completeness_calculation(self, analyzer):
        """Test completeness score calculation."""
        complete_data = [
            {
                "cve_id": "CVE-2024-1",
                "description": "Test",
                "published": "2024-01-01",
                "cvss_score": 5.0,
            }
        ]
        incomplete_data = [
            {"cve_id": "CVE-2024-2", "description": "Test"}  # Missing fields
        ]

        complete_score = analyzer._calculate_completeness(
            complete_data, "vulnerability"
        )
        incomplete_score = analyzer._calculate_completeness(
            incomplete_data, "vulnerability"
        )

        assert complete_score == 1.0
        assert incomplete_score < 1.0

    def test_uniqueness_calculation(self, analyzer):
        """Test uniqueness score calculation."""
        with patch("tools.deduplication.IntelligentDeduplicator") as mock_dedup:
            # Mock deduplication result
            mock_result = Mock()
            mock_result.unique_items = [{"id": 1}, {"id": 2}]
            mock_dedup.return_value.deduplicate.return_value = mock_result

            # Test with 3 items, 2 unique
            data = [{"id": 1}, {"id": 2}, {"id": 1}]  # One duplicate
            score = analyzer._calculate_uniqueness("nvd", data)

            # 2 unique out of 3 = 0.667
            assert 0.6 <= score <= 0.7

    def test_consistency_calculation(self, analyzer):
        """Test consistency score calculation."""
        # Consistent data - all items have same fields
        consistent_data = [
            {"id": 1, "name": "A", "value": 10},
            {"id": 2, "name": "B", "value": 20},
            {"id": 3, "name": "C", "value": 30},
        ]

        # Inconsistent data - different fields
        inconsistent_data = [
            {"id": 1, "name": "A"},
            {"id": 2, "value": 20},
            {"name": "C", "extra": True},
        ]

        consistent_score = analyzer._calculate_consistency(consistent_data)
        inconsistent_score = analyzer._calculate_consistency(inconsistent_data)

        assert consistent_score > 0.8
        assert inconsistent_score < 0.5

    def test_accuracy_estimation(self, analyzer):
        """Test accuracy estimation."""
        # Known high-accuracy source
        nvd_score = analyzer._estimate_accuracy("nvd", [{"id": 1}])
        assert nvd_score >= 0.95

        # Unknown source
        unknown_score = analyzer._estimate_accuracy("unknown", [{"id": 1}])
        assert unknown_score <= 0.85

        # Test data detection
        test_data = [
            {"description": "This is a test vulnerability"},
            {"description": "Example demo issue"},
        ]
        test_score = analyzer._estimate_accuracy("source", test_data)
        assert test_score < unknown_score  # Should be penalized

    def test_overall_score_calculation(self, analyzer):
        """Test weighted overall score calculation."""
        metrics = {
            "freshness": 1.0,
            "completeness": 0.8,
            "uniqueness": 0.6,
            "consistency": 0.9,
            "accuracy": 0.95,
        }

        overall = analyzer._calculate_overall_score(metrics)

        # Check weighted calculation
        expected = sum(metrics[k] * analyzer.WEIGHTS[k] for k in analyzer.WEIGHTS)
        assert abs(overall - expected) < 0.01

    def test_issue_identification(self, analyzer):
        """Test issue identification based on metrics."""
        # Poor metrics
        poor_metrics = QualityMetrics(
            freshness_score=0.3,
            completeness_score=0.5,
            uniqueness_score=0.05,
            consistency_score=0.6,
            accuracy_score=0.7,
            overall_score=0.4,
        )

        issues = analyzer._identify_issues(poor_metrics)

        assert any("freshness" in issue.lower() for issue in issues)
        assert any("completeness" in issue.lower() for issue in issues)
        assert any("duplicate" in issue.lower() for issue in issues)

    def test_recommendations_generation(self, analyzer):
        """Test recommendation generation."""
        poor_metrics = QualityMetrics(
            freshness_score=0.3,
            completeness_score=0.5,
            uniqueness_score=0.05,
            consistency_score=0.6,
            accuracy_score=0.7,
            overall_score=0.4,
        )

        recommendations = analyzer._generate_recommendations(
            "test_source", poor_metrics, ["Issue 1", "Issue 2"]
        )

        assert len(recommendations) > 0
        assert any("update frequency" in rec.lower() for rec in recommendations)
        assert any("deduplication" in rec.lower() for rec in recommendations)

    def test_trend_analysis(self, analyzer):
        """Test historical trend analysis."""
        # Simulate historical data
        source_id = "test_source"
        analyzer.history[source_id] = [
            {"metrics": {"overall": 0.5}, "timestamp": "2024-01-01"},
            {"metrics": {"overall": 0.6}, "timestamp": "2024-01-02"},
            {"metrics": {"overall": 0.7}, "timestamp": "2024-01-03"},
        ]

        # Improving trend
        trend = analyzer._analyze_trend(source_id, 0.8)
        assert trend == "improving"

        # Degrading trend
        trend = analyzer._analyze_trend(source_id, 0.4)
        assert trend == "degrading"

        # Stable trend
        trend = analyzer._analyze_trend(source_id, 0.7)
        assert trend == "stable"

    def test_history_persistence(self, analyzer, tmp_path):
        """Test saving and loading history."""
        report = SourceQualityReport(
            source_id="test",
            timestamp=datetime.utcnow().isoformat(),
            metrics=QualityMetrics(0.8, 0.9, 0.7, 0.85, 0.95, 0.85),
            issues=[],
            recommendations=["Keep up the good work"],
        )

        analyzer._store_in_history("test", report)

        # Create new analyzer with same history file
        new_analyzer = SourceQualityAnalyzer(analyzer.history_file)
        loaded_history = new_analyzer.history.get("test", [])

        assert len(loaded_history) == 1
        assert loaded_history[0]["source_id"] == "test"
        assert loaded_history[0]["metrics"]["overall"] == 0.85

    def test_quality_report_to_dict(self):
        """Test report serialization."""
        report = SourceQualityReport(
            source_id="test",
            timestamp="2024-01-01T00:00:00",
            metrics=QualityMetrics(0.8, 0.9, 0.7, 0.85, 0.95, 0.85),
            issues=["Issue 1"],
            recommendations=["Recommendation 1"],
            historical_trend="improving",
            data_samples=100,
        )

        report_dict = report.to_dict()

        assert report_dict["source_id"] == "test"
        assert report_dict["metrics"]["overall"] == 0.85
        assert len(report_dict["issues"]) == 1
        assert report_dict["historical_trend"] == "improving"

    def test_field_requirements(self, analyzer):
        """Test field requirements for different data types."""
        vuln_fields = analyzer.field_requirements["vulnerability"]
        assert "cve_id" in vuln_fields
        assert "cvss_score" in vuln_fields

        threat_fields = analyzer.field_requirements["threat_intelligence"]
        assert "indicator" in threat_fields
        assert "type" in threat_fields

    def test_type_consistency_check(self, analyzer):
        """Test type consistency checking."""
        # Consistent types
        consistent_data = [
            {"value": 1, "name": "A"},
            {"value": 2, "name": "B"},
            {"value": 3, "name": "C"},
        ]

        # Inconsistent types
        inconsistent_data = [
            {"value": 1, "name": "A"},
            {"value": "2", "name": "B"},  # String instead of int
            {"value": 3, "name": 100},  # Int instead of string
        ]

        consistent_score = analyzer._check_type_consistency(consistent_data)
        inconsistent_score = analyzer._check_type_consistency(inconsistent_data)

        assert consistent_score == 1.0
        assert inconsistent_score < 1.0

    def test_historical_summary(self, analyzer):
        """Test historical summary generation."""
        # Add some history
        source_id = "test_source"
        for i in range(5):
            report = SourceQualityReport(
                source_id=source_id,
                timestamp=datetime.utcnow().isoformat(),
                metrics=QualityMetrics(0.8, 0.9, 0.7, 0.85, 0.95, 0.7 + i * 0.05),
            )
            analyzer._store_in_history(source_id, report)

        summary = analyzer.get_historical_summary(source_id)

        assert summary["source_id"] == source_id
        assert summary["total_analyses"] == 5
        assert "average_score" in summary
        assert "min_score" in summary
        assert "max_score" in summary
        assert "recent_trend" in summary

    def test_multiple_date_fields(self, analyzer):
        """Test freshness with multiple date field options."""
        now = datetime.utcnow()
        data = [
            {
                "modified": (now - timedelta(days=5)).isoformat(),
                "created": (now - timedelta(days=10)).isoformat(),
            },
            {
                "updated": now.isoformat(),  # Should use most recent
                "published": (now - timedelta(days=2)).isoformat(),
            },
        ]

        score = analyzer._calculate_freshness(data)

        # Should use the most recent dates available
        assert score > 0  # At least one item is fresh

    def test_empty_history_summary(self, analyzer):
        """Test historical summary with no data."""
        summary = analyzer.get_historical_summary("nonexistent")
        assert "error" in summary

    @pytest.mark.parametrize(
        "data_type,expected_fields",
        [
            ("vulnerability", ["cve_id", "description", "cvss_score"]),
            ("threat_intelligence", ["indicator", "type", "source"]),
            ("malware", ["hash", "name", "type"]),
            ("default", ["id", "source", "timestamp"]),
        ],
    )
    def test_data_type_requirements(self, analyzer, data_type, expected_fields):
        """Test that different data types have appropriate field requirements."""
        fields = analyzer.field_requirements.get(
            data_type, analyzer.field_requirements["default"]
        )
        for field in expected_fields:
            assert field in fields

    def test_metrics_to_dict(self):
        """Test metrics serialization."""
        metrics = QualityMetrics(
            freshness_score=0.123456,
            completeness_score=0.987654,
            uniqueness_score=0.555555,
            consistency_score=0.777777,
            accuracy_score=0.999999,
            overall_score=0.666666,
        )

        metrics_dict = metrics.to_dict()

        # Check rounding to 3 decimal places
        assert metrics_dict["freshness"] == 0.123
        assert metrics_dict["completeness"] == 0.988
        assert metrics_dict["overall"] == 0.667

    @pytest.mark.benchmark
    def test_analysis_performance(self, benchmark, analyzer):
        """Benchmark analysis performance."""
        # Generate large dataset
        data = [
            {
                "cve_id": f"CVE-2024-{i:04d}",
                "description": f"Vulnerability {i}",
                "published": datetime.utcnow().isoformat(),
                "cvss_score": 5.0 + (i % 5),
            }
            for i in range(1000)
        ]

        result = benchmark(analyzer.analyze_source, "perf_test", data, "vulnerability")

        assert result.data_samples == 1000
        assert result.metrics.overall_score > 0
