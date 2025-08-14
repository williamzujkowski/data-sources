"""Performance benchmark tests for the data sources tools.

These tests measure the performance of key operations to ensure
they meet acceptable performance standards.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

import fetch_sources
import score_sources


@pytest.fixture
def sample_data_sources():
    """Create sample data sources for benchmarking."""
    sources = []
    for i in range(100):
        source = {
            "id": f"test-source-{i}",
            "name": f"Test Source {i}",
            "url": f"https://example.com/api/v{i}",
            "description": f"Test data source number {i}",
            "category": "test",
            "tags": ["test", "benchmark"],
            "format": "json",
            "last_updated": "2025-08-14T12:00:00Z",
            "quality_score": 85.5,
            "authority": 90.0,
            "coverage": 80.0,
            "availability": 95.0,
        }
        sources.append(source)
    return sources


@pytest.fixture
def temp_source_files(sample_data_sources):
    """Create temporary source files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_files = []

        for i, source in enumerate(sample_data_sources):
            file_path = temp_path / f"source_{i}.json"
            with open(file_path, "w") as f:
                json.dump(source, f, indent=2)
            source_files.append(str(file_path))

        yield source_files


class TestFetchSourcesPerformance:
    """Benchmark tests for fetch_sources module."""

    def test_load_source_files_performance(self, benchmark, temp_source_files):
        """Benchmark loading multiple source files."""
        with patch("fetch_sources.DATA_SOURCES_DIR", Path(temp_source_files[0]).parent):
            result = benchmark(fetch_sources.load_source_files)
            assert len(result) == 100

    def test_health_check_performance(self, benchmark, sample_data_sources):
        """Benchmark health check for a single source."""
        source = sample_data_sources[0]

        with patch("fetch_sources.requests.head") as mock_head:
            mock_head.return_value.status_code = 200

            result = benchmark(fetch_sources.fetch_source_health, source)
            assert "available" in result


class TestScoreSourcesPerformance:
    """Benchmark tests for score_sources module."""

    def test_calculate_quality_score_performance(self, benchmark, sample_data_sources):
        """Benchmark quality score calculation."""
        source = sample_data_sources[0]
        weights = {
            "freshness": 0.4,
            "authority": 0.3,
            "coverage": 0.2,
            "availability": 0.1,
        }

        result = benchmark(score_sources.calculate_quality_score, source, weights)
        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_calculate_freshness_score_performance(self, benchmark):
        """Benchmark freshness score calculation."""
        timestamp = "2025-08-14T12:00:00Z"

        result = benchmark(score_sources.calculate_freshness_score, timestamp)
        assert isinstance(result, float)
        assert 0 <= result <= 100

    def test_bulk_scoring_performance(self, benchmark, sample_data_sources):
        """Benchmark scoring multiple sources."""
        weights = {
            "freshness": 0.4,
            "authority": 0.3,
            "coverage": 0.2,
            "availability": 0.1,
        }

        def score_all_sources():
            results = []
            for source in sample_data_sources:
                score = score_sources.calculate_quality_score(source, weights)
                results.append(score)
            return results

        results = benchmark(score_all_sources)
        assert len(results) == 100
        assert all(isinstance(score, float) for score in results)


class TestValidateSourcesPerformance:
    """Benchmark tests for validate_sources module."""

    def test_schema_validation_performance(self, benchmark):
        """Benchmark schema validation."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "url": {"type": "string"},
            },
            "required": ["id", "name"],
        }

        source_data = {
            "id": "test-source",
            "name": "Test Source",
            "url": "https://example.com",
        }

        def validate_source():
            import jsonschema

            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(source_data))
            return len(errors) == 0

        result = benchmark(validate_source)
        assert result is True


class TestIntegratedWorkflowPerformance:
    """Benchmark tests for integrated workflows."""

    def test_full_processing_workflow(self, benchmark, temp_source_files):
        """Benchmark the full source processing workflow."""

        def full_workflow():
            # Load sources
            with patch(
                "fetch_sources.DATA_SOURCES_DIR", Path(temp_source_files[0]).parent
            ):
                sources = fetch_sources.load_source_files()

            # Score sources
            weights = {
                "freshness": 0.4,
                "authority": 0.3,
                "coverage": 0.2,
                "availability": 0.1,
            }
            for source in sources:
                score_sources.calculate_quality_score(source, weights)

            return len(sources)

        result = benchmark(full_workflow)
        assert result == 100


# Performance thresholds (these can be adjusted based on requirements)
pytestmark = pytest.mark.benchmark(
    group="data_sources_tools",
    min_rounds=5,
    max_time=10.0,
    disable_gc=True,
    warmup=True,
)
