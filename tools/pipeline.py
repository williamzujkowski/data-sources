#!/usr/bin/env python3
"""
Main pipeline orchestrator for threat intelligence data collection.
Coordinates fetching, deduplication, quality analysis, and metrics.
"""

import asyncio
import json
import logging
import signal
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tools.deduplication import DuplicateStrategy, IntelligentDeduplicator
from tools.metrics import metrics_collector
from tools.quality_analyzer import SourceQualityAnalyzer as QualityAnalyzer
from tools.sources.nvd_fetcher import NVDFetcher

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main orchestrator for the threat intelligence pipeline.

    Coordinates:
    - Source data fetching
    - Intelligent deduplication
    - Quality analysis
    - Metrics collection
    - Data persistence
    """

    def __init__(
        self,
        data_dir: str = "data",
        max_concurrent_sources: int = 3,
        fetch_interval_minutes: int = 60,
    ):
        """
        Initialize the pipeline orchestrator.

        Args:
            data_dir: Directory for data storage
            max_concurrent_sources: Maximum concurrent source fetches
            fetch_interval_minutes: Minutes between fetch cycles
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent_sources = max_concurrent_sources
        self.fetch_interval = timedelta(minutes=fetch_interval_minutes)
        self.running = False
        self.fetch_semaphore = asyncio.Semaphore(max_concurrent_sources)

        # Initialize components
        self.deduplicator = IntelligentDeduplicator()
        self.quality_analyzer = QualityAnalyzer()

        # Source configurations
        self.sources = self._configure_sources()

        # Statistics
        self.stats = {
            "total_items_fetched": 0,
            "total_unique_items": 0,
            "total_duplicates": 0,
            "fetch_cycles": 0,
            "errors": 0,
        }

    def _configure_sources(self) -> Dict[str, Any]:
        """Configure data sources."""
        return {
            "nvd": {
                "fetcher": NVDFetcher(),
                "strategy": DuplicateStrategy(
                    name="nvd",
                    keep_highest_authority=True,
                    merge_fields=True,
                    aggregate_scores=True,
                ),
                "enabled": True,
            },
            # Placeholder for future sources
            "cisa_kev": {
                "fetcher": None,  # To be implemented
                "strategy": DuplicateStrategy(
                    name="cisa_kev",
                    keep_highest_authority=True,
                    merge_fields=True,
                ),
                "enabled": False,
            },
            "alienvault_otx": {
                "fetcher": None,  # To be implemented
                "strategy": DuplicateStrategy(
                    name="alienvault_otx",
                    merge_fields=True,
                    preserve_all_sources=True,
                ),
                "enabled": False,
            },
        }

    async def fetch_source_data(self, source_name: str) -> List[Dict[str, Any]]:
        """
        Fetch data from a specific source.

        Args:
            source_name: Name of the source to fetch from

        Returns:
            List of fetched items
        """
        source_config = self.sources.get(source_name)
        if not source_config or not source_config["enabled"]:
            logger.debug(f"Source {source_name} is disabled or not configured")
            return []

        fetcher = source_config["fetcher"]
        if not fetcher:
            logger.warning(f"No fetcher implemented for {source_name}")
            return []

        async with self.fetch_semaphore:
            start_time = time.time()
            items = []

            try:
                logger.info(f"Fetching data from {source_name}")

                if source_name == "nvd":
                    async with fetcher as nvd:
                        cve_data = await nvd.fetch_incremental()
                        items = [asdict(cve) for cve in cve_data]

                # Add other source implementations here

                duration = time.time() - start_time
                metrics_collector.record_fetch(
                    source=source_name,
                    duration=duration,
                    items=len(items),
                    status="success",
                )

                logger.info(
                    f"Fetched {len(items)} items from {source_name} in {duration:.2f}s"
                )

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error fetching from {source_name}: {e}")
                metrics_collector.record_fetch(
                    source=source_name,
                    duration=duration,
                    items=0,
                    status="error",
                )
                metrics_collector.record_error(
                    source=source_name,
                    error_type=type(e).__name__,
                )
                self.stats["errors"] += 1

            return items

    async def process_source_data(
        self,
        source_name: str,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Process fetched data through deduplication and quality analysis.

        Args:
            source_name: Name of the data source
            items: Raw items from the source

        Returns:
            Processing results
        """
        if not items:
            return {
                "source": source_name,
                "unique_items": [],
                "quality_score": 0.0,
                "statistics": {},
            }

        # Deduplication
        start_time = time.time()
        strategy = self.sources[source_name]["strategy"]
        dedup_result = self.deduplicator.deduplicate(items, strategy)
        dedup_duration = time.time() - start_time

        metrics_collector.record_deduplication(
            source=source_name,
            total=len(items),
            unique=len(dedup_result.unique_items),
            duration=dedup_duration,
        )

        # Quality Analysis
        start_time = time.time()
        quality_result = self.quality_analyzer.analyze_source(
            source_name=source_name,
            items=dedup_result.unique_items,
        )
        quality_duration = time.time() - start_time

        metrics_collector.record_quality(
            source=source_name,
            metrics={
                "timeliness": quality_result.metrics.freshness_score,
                "completeness": quality_result.metrics.completeness_score,
                "consistency": quality_result.metrics.consistency_score,
                "accuracy": quality_result.metrics.accuracy_score,
            },
            duration=quality_duration,
        )

        return {
            "source": source_name,
            "unique_items": dedup_result.unique_items,
            "quality_score": quality_result.metrics.overall_score,
            "quality_metrics": asdict(quality_result.metrics),
            "recommendations": quality_result.recommendations,
            "statistics": dedup_result.statistics,
        }

    async def save_results(self, results: Dict[str, Any]) -> None:
        """
        Save processed results to storage.

        Args:
            results: Processing results to save
        """
        source_name = results["source"]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Save deduplicated data
        output_dir = self.data_dir / "processed" / source_name
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{source_name}_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "source": source_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "total_items": len(results["unique_items"]),
                        "quality_score": results["quality_score"],
                        "quality_metrics": results["quality_metrics"],
                    },
                    "items": results["unique_items"],
                },
                f,
                indent=2,
            )

        logger.info(f"Saved {len(results['unique_items'])} items to {output_file}")

        # Save quality report
        quality_dir = self.data_dir / "quality_reports"
        quality_dir.mkdir(parents=True, exist_ok=True)

        quality_file = quality_dir / f"{source_name}_{timestamp}.json"
        with open(quality_file, "w") as f:
            json.dump(
                {
                    "source": source_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "quality_score": results["quality_score"],
                    "metrics": results["quality_metrics"],
                    "recommendations": results["recommendations"],
                    "statistics": results["statistics"],
                },
                f,
                indent=2,
            )

    async def run_fetch_cycle(self) -> None:
        """Run a single fetch cycle for all enabled sources."""
        logger.info("Starting fetch cycle")
        cycle_start = time.time()

        # Collect enabled sources
        enabled_sources = [
            name for name, config in self.sources.items() if config["enabled"]
        ]

        if not enabled_sources:
            logger.warning("No sources enabled")
            return

        # Fetch from all sources concurrently
        fetch_tasks = [self.fetch_source_data(source) for source in enabled_sources]
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Process results
        total_fetched = 0
        total_unique = 0

        for source_name, result in zip(enabled_sources, fetch_results):
            if isinstance(result, Exception):
                logger.error(f"Fetch failed for {source_name}: {result}")
                continue

            if not result:
                logger.info(f"No new data from {source_name}")
                continue

            total_fetched += len(result)

            # Process the data
            processed = await self.process_source_data(source_name, result)
            total_unique += len(processed["unique_items"])

            # Save results
            await self.save_results(processed)

        # Update statistics
        self.stats["fetch_cycles"] += 1
        self.stats["total_items_fetched"] += total_fetched
        self.stats["total_unique_items"] += total_unique
        self.stats["total_duplicates"] += total_fetched - total_unique

        # Update metrics
        active_sources = len([s for s in enabled_sources if s])
        metrics_collector.update_counts(
            active_sources_count=active_sources,
            total_vulns=self.stats["total_unique_items"],
        )

        cycle_duration = time.time() - cycle_start
        logger.info(
            f"Fetch cycle complete: {total_fetched} items fetched, "
            f"{total_unique} unique, duration: {cycle_duration:.2f}s"
        )

    async def run(self) -> None:
        """Run the pipeline continuously."""
        self.running = True
        logger.info("Pipeline orchestrator started")

        while self.running:
            try:
                await self.run_fetch_cycle()

                if self.running:
                    logger.info(
                        f"Waiting {self.fetch_interval.total_seconds()}s until next cycle"
                    )
                    await asyncio.sleep(self.fetch_interval.total_seconds())

            except asyncio.CancelledError:
                logger.info("Pipeline cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in pipeline: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(60)  # Wait before retry

        logger.info("Pipeline orchestrator stopped")

    def stop(self) -> None:
        """Stop the pipeline."""
        logger.info("Stopping pipeline orchestrator")
        self.running = False

    def get_statistics(self) -> Dict[str, Any]:
        """Get current pipeline statistics."""
        return {
            **self.stats,
            "deduplicator_stats": {
                "total_hashes": len(self.deduplicator.exact_hashes),
                "cache_size": len(self.deduplicator.item_cache),
                "merge_history": len(self.deduplicator.merge_history),
            },
            "quality_analyzer_stats": {
                "sources_analyzed": len(self.quality_analyzer.history),
            },
        }


async def main():
    """Main entry point for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        data_dir="data",
        max_concurrent_sources=3,
        fetch_interval_minutes=60,  # Fetch every hour
    )

    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        orchestrator.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run pipeline
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Print final statistics
        stats = orchestrator.get_statistics()
        logger.info(f"Final statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
