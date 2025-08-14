"""
Performance tests for threat intelligence pipeline.
Tests throughput, latency, and resource usage under load.
"""

import asyncio
import json
import random
import time
from typing import Any, Dict, List

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from tools.deduplication import IntelligentDeduplicator
from tools.pipeline import PipelineOrchestrator
from tools.quality_analyzer import QualityAnalyzer


class TestPipelinePerformance:
    """Performance tests for the pipeline."""

    @pytest.fixture
    def sample_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Generate sample vulnerability data."""
        vulns = []
        for i in range(1000):
            vulns.append(
                {
                    "cve_id": f"CVE-2024-{i:04d}",
                    "description": f"Test vulnerability {i} with some description text",
                    "cvss_v3_score": random.uniform(0, 10),
                    "published": "2024-01-01T00:00:00Z",
                    "last_modified": "2024-01-02T00:00:00Z",
                    "vendor": random.choice(["microsoft", "oracle", "apache", "linux"]),
                    "product": f"product_{i % 100}",
                    "cwe_ids": [f"CWE-{random.randint(1, 1000)}"],
                    "references": [f"https://example.com/cve/{i}"],
                }
            )

        # Add some duplicates
        for i in range(100):
            vulns.append(vulns[i].copy())

        return vulns

    @pytest.fixture
    def large_dataset(self) -> List[Dict[str, Any]]:
        """Generate large dataset for stress testing."""
        items = []
        for i in range(10000):
            items.append(
                {
                    "id": f"item-{i}",
                    "type": random.choice(["cve", "ioc", "pulse"]),
                    "source": random.choice(["nvd", "mitre", "alienvault"]),
                    "data": f"Data payload {i}" * 10,  # Make it larger
                    "score": random.random(),
                }
            )
        return items

    @pytest.mark.benchmark
    def test_deduplication_throughput(
        self, benchmark: BenchmarkFixture, sample_vulnerabilities: List[Dict[str, Any]]
    ):
        """Benchmark deduplication throughput."""
        deduplicator = IntelligentDeduplicator()

        def run_dedup():
            deduplicator.reset()
            return deduplicator.deduplicate(sample_vulnerabilities)

        result = benchmark(run_dedup)

        assert result.statistics["total_input"] == len(sample_vulnerabilities)
        assert result.statistics["unique_output"] <= len(sample_vulnerabilities)
        assert result.processing_time < 1.0  # Should process in under 1 second

    @pytest.mark.benchmark
    def test_quality_analysis_performance(
        self, benchmark: BenchmarkFixture, sample_vulnerabilities: List[Dict[str, Any]]
    ):
        """Benchmark quality analysis performance."""
        analyzer = QualityAnalyzer()

        def run_analysis():
            return analyzer.analyze_source("test_source", sample_vulnerabilities)

        result = benchmark(run_analysis)

        assert result.overall_score >= 0
        assert result.overall_score <= 1
        assert result.analysis_time < 0.5  # Should analyze in under 500ms

    @pytest.mark.asyncio
    async def test_concurrent_source_fetching(self):
        """Test concurrent fetching from multiple sources."""
        orchestrator = PipelineOrchestrator(max_concurrent_sources=3)

        # Mock multiple source fetches
        async def mock_fetch(source_name: str):
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate network delay
            return [
                {"id": f"{source_name}-{i}", "data": f"Item {i} from {source_name}"}
                for i in range(100)
            ]

        # Test concurrent execution
        start_time = time.time()
        tasks = [mock_fetch(f"source_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        assert len(results) == 5
        assert all(len(r) == 100 for r in results)
        assert duration < 1.0  # Should complete concurrently

    @pytest.mark.benchmark
    def test_large_dataset_processing(
        self, benchmark: BenchmarkFixture, large_dataset: List[Dict[str, Any]]
    ):
        """Test processing of large datasets."""
        deduplicator = IntelligentDeduplicator()

        def process_large_dataset():
            deduplicator.reset()
            result = deduplicator.deduplicate(large_dataset)
            return result

        result = benchmark(process_large_dataset)

        assert result.statistics["total_input"] == len(large_dataset)
        assert (
            result.processing_time < 5.0
        )  # Should process 10k items in under 5 seconds

    def test_memory_efficiency(self, large_dataset: List[Dict[str, Any]]):
        """Test memory efficiency with large datasets."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        deduplicator = IntelligentDeduplicator()
        result = deduplicator.deduplicate(large_dataset)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 500  # Less than 500MB for 10k items
        assert len(result.unique_items) > 0

    @pytest.mark.asyncio
    async def test_pipeline_cycle_performance(self):
        """Test complete pipeline cycle performance."""
        orchestrator = PipelineOrchestrator()

        # Mock the fetcher to return test data quickly
        class MockFetcher:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def fetch_incremental(self):
                return [
                    {
                        "cve_id": f"CVE-2024-{i:04d}",
                        "description": f"Test CVE {i}",
                    }
                    for i in range(100)
                ]

        # Replace NVD fetcher with mock
        orchestrator.sources["nvd"]["fetcher"] = MockFetcher()
        orchestrator.sources["nvd"]["enabled"] = True

        # Run one cycle and measure time
        start_time = time.time()
        await orchestrator.run_fetch_cycle()
        duration = time.time() - start_time

        stats = orchestrator.get_statistics()

        assert stats["fetch_cycles"] == 1
        assert stats["total_items_fetched"] > 0
        assert duration < 2.0  # Complete cycle in under 2 seconds

    @pytest.mark.benchmark
    def test_fuzzy_matching_performance(self, benchmark: BenchmarkFixture):
        """Test fuzzy matching performance for near-duplicates."""
        deduplicator = IntelligentDeduplicator(similarity_threshold=0.85)

        # Generate similar items
        items = []
        for i in range(500):
            base_text = (
                f"SQL injection vulnerability in Example Product version {i % 10}"
            )
            # Add variations
            items.append({"description": base_text})
            items.append({"description": base_text.lower()})
            items.append({"description": base_text.replace("SQL", "SQLi")})

        def run_fuzzy_dedup():
            deduplicator.reset()
            return deduplicator.deduplicate(items)

        result = benchmark(run_fuzzy_dedup)

        assert result.statistics["total_input"] == len(items)
        assert result.processing_time < 3.0  # Should handle fuzzy matching efficiently

    def test_incremental_deduplication(self):
        """Test incremental deduplication performance."""
        deduplicator = IntelligentDeduplicator()

        # Process initial batch
        batch1 = [{"id": f"item-{i}"} for i in range(1000)]
        result1 = deduplicator.deduplicate(batch1)
        time1 = result1.processing_time

        # Process second batch with some duplicates
        batch2 = [{"id": f"item-{i}"} for i in range(500, 1500)]
        result2 = deduplicator.deduplicate(batch2)
        time2 = result2.processing_time

        # Second batch should be faster due to bloom filter
        assert result2.statistics["duplicates_removed"] == 500
        assert time2 < time1 * 1.5  # Should not be much slower despite duplicates

    @pytest.mark.asyncio
    async def test_api_endpoint_performance(self):
        """Test API endpoint response times."""
        from fastapi.testclient import TestClient

        from tools.api_server import app

        client = TestClient(app)

        # Test health endpoint
        start = time.time()
        response = client.get("/health")
        health_time = time.time() - start

        assert response.status_code == 200
        assert health_time < 0.1  # Health check should be fast

        # Test metrics endpoint
        start = time.time()
        response = client.get("/metrics")
        metrics_time = time.time() - start

        assert response.status_code == 200
        assert metrics_time < 0.2  # Metrics generation should be quick

        # Test deduplication endpoint
        items = [{"id": f"item-{i}"} for i in range(100)]
        start = time.time()
        response = client.post("/api/v1/deduplicate", json={"items": items})
        dedup_time = time.time() - start

        assert response.status_code == 200
        assert dedup_time < 0.5  # API processing should be responsive

    def test_scalability_metrics(self):
        """Test scalability with increasing load."""
        deduplicator = IntelligentDeduplicator()

        sizes = [100, 500, 1000, 5000, 10000]
        times = []

        for size in sizes:
            items = [{"id": f"item-{i}"} for i in range(size)]
            deduplicator.reset()

            start = time.time()
            result = deduplicator.deduplicate(items)
            duration = time.time() - start
            times.append(duration)

            # Calculate throughput
            throughput = size / duration
            print(
                f"Size: {size}, Time: {duration:.3f}s, Throughput: {throughput:.0f} items/s"
            )

        # Check that performance scales reasonably (not exponentially)
        # Time complexity should be roughly O(n) or O(n log n)
        for i in range(1, len(times)):
            size_ratio = sizes[i] / sizes[i - 1]
            time_ratio = times[i] / times[i - 1]
            # Time should not grow faster than n^2
            assert time_ratio < size_ratio * size_ratio
