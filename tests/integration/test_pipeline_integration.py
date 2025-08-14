"""
Integration tests for the complete threat intelligence pipeline.
Tests end-to-end functionality and component interactions.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tools.api_server import app
from tools.deduplication import IntelligentDeduplicator
from tools.metrics import metrics_collector
from tools.pipeline import PipelineOrchestrator
from tools.quality_analyzer import QualityAnalyzer
from tools.sources.nvd_fetcher import CVEData, NVDFetcher


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary data directory."""
        return tmp_path / "test_data"

    @pytest.fixture
    def mock_cve_data(self) -> List[CVEData]:
        """Generate mock CVE data."""
        return [
            CVEData(
                cve_id=f"CVE-2024-{i:04d}",
                published="2024-01-01T00:00:00Z",
                last_modified="2024-01-02T00:00:00Z",
                description=f"Test vulnerability {i}",
                cvss_v3_score=7.5 if i % 2 == 0 else None,
                cvss_v3_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                cwe_ids=[f"CWE-{i % 100}"],
                vendor="test_vendor",
                product=f"product_{i % 10}",
            )
            for i in range(50)
        ]

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self, temp_data_dir, mock_cve_data):
        """Test complete pipeline flow from fetch to storage."""
        # Setup orchestrator with temp directory
        orchestrator = PipelineOrchestrator(data_dir=str(temp_data_dir))

        # Mock NVD fetcher
        with patch.object(NVDFetcher, "fetch_incremental", return_value=mock_cve_data):
            # Run one fetch cycle
            await orchestrator.run_fetch_cycle()

        # Verify data was processed and saved
        processed_dir = temp_data_dir / "processed" / "nvd"
        assert processed_dir.exists()

        # Check that files were created
        json_files = list(processed_dir.glob("*.json"))
        assert len(json_files) > 0

        # Load and verify saved data
        with open(json_files[0]) as f:
            saved_data = json.load(f)

        assert "metadata" in saved_data
        assert "items" in saved_data
        assert saved_data["metadata"]["source"] == "nvd"
        assert len(saved_data["items"]) > 0

        # Verify quality reports were generated
        quality_dir = temp_data_dir / "quality_reports"
        assert quality_dir.exists()
        quality_files = list(quality_dir.glob("*.json"))
        assert len(quality_files) > 0

        # Check statistics
        stats = orchestrator.get_statistics()
        assert stats["fetch_cycles"] == 1
        assert stats["total_items_fetched"] > 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    async def test_deduplication_across_sources(self):
        """Test deduplication works across multiple sources."""
        deduplicator = IntelligentDeduplicator()

        # Source 1 data
        source1_items = [
            {"cve_id": "CVE-2024-0001", "source": "nvd", "score": 7.5},
            {"cve_id": "CVE-2024-0002", "source": "nvd", "score": 8.0},
        ]

        # Source 2 data with overlap
        source2_items = [
            {"cve_id": "CVE-2024-0001", "source": "mitre", "score": 7.8},
            {"cve_id": "CVE-2024-0003", "source": "mitre", "score": 6.5},
        ]

        # Process both sources
        result1 = deduplicator.deduplicate(source1_items)
        result2 = deduplicator.deduplicate(source2_items)

        # CVE-2024-0001 should be detected as duplicate in source2
        assert len(result1.unique_items) == 2
        assert len(result2.unique_items) == 1  # Only CVE-2024-0003 is new
        assert result2.unique_items[0]["cve_id"] == "CVE-2024-0003"

    @pytest.mark.asyncio
    async def test_quality_tracking_over_time(self):
        """Test quality tracking across multiple fetch cycles."""
        analyzer = QualityAnalyzer()

        # Simulate multiple analysis cycles
        for day in range(3):
            items = [
                {
                    "cve_id": f"CVE-2024-{day:02d}{i:02d}",
                    "published": f"2024-01-{day+1:02d}T00:00:00Z",
                    "cvss_v3_score": 7.5 if i < 5 else None,  # Varying completeness
                }
                for i in range(10)
            ]

            result = analyzer.analyze_source("test_source", items)

            # Quality should be tracked
            assert result.overall_score >= 0
            assert result.overall_score <= 1

        # Check history
        assert len(analyzer.history) == 3

        # Get trend analysis
        trend = analyzer.get_quality_trend("test_source", days=7)
        assert "scores" in trend
        assert len(trend["scores"]) == 3

    def test_metrics_collection_integration(self):
        """Test metrics are properly collected throughout pipeline."""
        # Reset metrics
        metrics_collector.update_counts(0, 0)

        # Simulate pipeline operations
        metrics_collector.record_fetch("nvd", 1.5, 100, "success")
        metrics_collector.record_deduplication("nvd", 100, 85, 0.2)
        metrics_collector.record_quality("nvd", {"completeness": 0.9}, 0.1)

        # Get metrics
        from tools.metrics import get_metrics

        metrics_data = get_metrics()

        # Verify metrics are present
        assert b"threatintel_source_fetch_duration_seconds" in metrics_data
        assert b"threatintel_deduplication_ratio" in metrics_data
        assert b"threatintel_source_quality_score" in metrics_data

    def test_api_pipeline_integration(self):
        """Test API server integration with pipeline components."""
        client = TestClient(app)

        # Test deduplication endpoint
        items = [
            {"id": "item-1", "data": "test1"},
            {"id": "item-1", "data": "test1"},  # Duplicate
            {"id": "item-2", "data": "test2"},
        ]

        response = client.post("/api/v1/deduplicate", json={"items": items})
        assert response.status_code == 200

        result = response.json()
        assert len(result["unique_items"]) == 2
        assert result["statistics"]["duplicates_removed"] == 1

        # Test quality analysis endpoint
        quality_items = [
            {"cve_id": f"CVE-2024-{i:04d}", "cvss_v3_score": 7.5} for i in range(10)
        ]

        response = client.post(
            "/api/v1/analyze/quality",
            json={
                "source_name": "test",
                "items": quality_items,
            },
        )
        assert response.status_code == 200

        quality_result = response.json()
        assert "quality_score" in quality_result
        assert "dimensions" in quality_result
        assert quality_result["quality_score"] > 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_data_dir):
        """Test pipeline handles errors gracefully."""
        orchestrator = PipelineOrchestrator(data_dir=str(temp_data_dir))

        # Mock fetcher that raises an error
        async def failing_fetch(*args, **kwargs):
            raise ConnectionError("Network error")

        with patch.object(NVDFetcher, "fetch_incremental", side_effect=failing_fetch):
            # Should handle error without crashing
            await orchestrator.run_fetch_cycle()

        # Check error was recorded
        stats = orchestrator.get_statistics()
        assert stats["errors"] > 0

        # Pipeline should still be functional
        assert orchestrator.running == False  # Not in continuous mode

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """Test API handles concurrent requests properly."""
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send multiple concurrent requests
            tasks = []
            for i in range(10):
                items = [{"id": f"item-{i}-{j}"} for j in range(10)]
                task = client.post("/api/v1/deduplicate", json={"items": items})
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)

            # Each should have correct results
            for r in responses:
                data = r.json()
                assert len(data["unique_items"]) == 10

    @pytest.mark.asyncio
    async def test_incremental_updates(self, temp_data_dir):
        """Test incremental update functionality."""
        orchestrator = PipelineOrchestrator(data_dir=str(temp_data_dir))

        # First fetch
        batch1 = [
            CVEData(
                cve_id=f"CVE-2024-{i:04d}",
                published="2024-01-01T00:00:00Z",
                last_modified="2024-01-01T00:00:00Z",
                description=f"Initial batch {i}",
            )
            for i in range(10)
        ]

        with patch.object(NVDFetcher, "fetch_incremental", return_value=batch1):
            await orchestrator.run_fetch_cycle()

        initial_stats = orchestrator.get_statistics()

        # Second fetch with some new items
        batch2 = [
            CVEData(
                cve_id=f"CVE-2024-{i:04d}",
                published="2024-01-02T00:00:00Z",
                last_modified="2024-01-02T00:00:00Z",
                description=f"Updated batch {i}",
            )
            for i in range(5, 15)  # Overlap with first batch
        ]

        with patch.object(NVDFetcher, "fetch_incremental", return_value=batch2):
            await orchestrator.run_fetch_cycle()

        final_stats = orchestrator.get_statistics()

        # Should detect duplicates from previous fetch
        assert final_stats["total_duplicates"] > 0
        assert final_stats["fetch_cycles"] == 2

    def test_data_persistence_format(self, temp_data_dir):
        """Test data is persisted in correct format."""
        import json
        from datetime import datetime

        # Create test data
        test_data = {
            "metadata": {
                "source": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "total_items": 10,
                "quality_score": 0.85,
            },
            "items": [{"id": f"item-{i}", "data": f"test-{i}"} for i in range(10)],
        }

        # Save data
        output_dir = temp_data_dir / "processed" / "test"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "test_data.json"

        with open(output_file, "w") as f:
            json.dump(test_data, f, indent=2)

        # Verify it can be loaded back
        with open(output_file) as f:
            loaded_data = json.load(f)

        assert loaded_data["metadata"]["source"] == "test"
        assert len(loaded_data["items"]) == 10
        assert loaded_data["metadata"]["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_monitoring_integration(self):
        """Test monitoring components work together."""
        # Run some pipeline operations
        orchestrator = PipelineOrchestrator()

        # Generate some metrics
        metrics_collector.record_fetch("test", 1.0, 100, "success")
        metrics_collector.update_system_metrics()

        # Check Prometheus metrics are generated
        from tools.metrics import get_metrics

        metrics_data = get_metrics()

        # Should contain system metrics
        assert b"threatintel_memory_usage_bytes" in metrics_data
        assert b"threatintel_cpu_usage_percent" in metrics_data

        # API metrics endpoint should work
        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert len(response.text) > 0
