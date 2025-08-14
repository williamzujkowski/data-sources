"""
Performance metrics collection for threat intelligence pipeline.
Provides Prometheus-compatible metrics for monitoring and alerting.
"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

import psutil
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)

# Custom registry for isolation
metrics_registry = CollectorRegistry()

# =============================================================================
# Core Metrics Definitions
# =============================================================================

# Source Fetching Metrics
source_fetch_duration = Histogram(
    "threatintel_source_fetch_duration_seconds",
    "Time spent fetching data from source",
    ["source", "status"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=metrics_registry,
)

source_fetch_total = Counter(
    "threatintel_source_fetch_total",
    "Total number of source fetch attempts",
    ["source", "status"],
    registry=metrics_registry,
)

source_items_fetched = Histogram(
    "threatintel_source_items_fetched",
    "Number of items fetched from source",
    ["source"],
    buckets=(0, 10, 50, 100, 500, 1000, 5000, 10000),
    registry=metrics_registry,
)

# Deduplication Metrics
deduplication_duration = Histogram(
    "threatintel_deduplication_duration_seconds",
    "Time spent on deduplication",
    ["strategy"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
    registry=metrics_registry,
)

deduplication_ratio = Gauge(
    "threatintel_deduplication_ratio",
    "Ratio of unique items after deduplication",
    ["source"],
    registry=metrics_registry,
)

duplicates_removed = Counter(
    "threatintel_duplicates_removed_total",
    "Total number of duplicates removed",
    ["source"],
    registry=metrics_registry,
)

# Quality Metrics
source_quality_score = Gauge(
    "threatintel_source_quality_score",
    "Quality score for data source",
    ["source", "dimension"],
    registry=metrics_registry,
)

quality_analysis_duration = Histogram(
    "threatintel_quality_analysis_duration_seconds",
    "Time spent analyzing source quality",
    ["source"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
    registry=metrics_registry,
)

# API Performance Metrics
api_request_duration = Histogram(
    "threatintel_api_request_duration_seconds",
    "API request duration",
    ["endpoint", "method", "status"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=metrics_registry,
)

api_request_total = Counter(
    "threatintel_api_request_total",
    "Total API requests",
    ["endpoint", "method", "status"],
    registry=metrics_registry,
)

# System Metrics
active_sources = Gauge(
    "threatintel_active_sources",
    "Number of active data sources",
    registry=metrics_registry,
)

total_vulnerabilities = Gauge(
    "threatintel_total_vulnerabilities",
    "Total number of vulnerabilities in database",
    registry=metrics_registry,
)

memory_usage_bytes = Gauge(
    "threatintel_memory_usage_bytes",
    "Memory usage in bytes",
    registry=metrics_registry,
)

cpu_usage_percent = Gauge(
    "threatintel_cpu_usage_percent",
    "CPU usage percentage",
    registry=metrics_registry,
)

# Cache Metrics
cache_hits = Counter(
    "threatintel_cache_hits_total",
    "Total cache hits",
    ["cache_type"],
    registry=metrics_registry,
)

cache_misses = Counter(
    "threatintel_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
    registry=metrics_registry,
)

cache_size = Gauge(
    "threatintel_cache_size_bytes",
    "Current cache size in bytes",
    ["cache_type"],
    registry=metrics_registry,
)

# Error Metrics
errors_total = Counter(
    "threatintel_errors_total",
    "Total number of errors",
    ["source", "error_type"],
    registry=metrics_registry,
)

# Info Metrics
pipeline_info = Info(
    "threatintel_pipeline",
    "Pipeline information",
    registry=metrics_registry,
)

# =============================================================================
# Decorators for Metric Collection
# =============================================================================


def track_duration(metric: Histogram, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track function duration.

    Args:
        metric: Prometheus Histogram to track duration
        labels: Labels to apply to the metric
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metric_labels = {**(labels or {}), "status": status}
                metric.labels(**metric_labels).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metric_labels = {**(labels or {}), "status": status}
                metric.labels(**metric_labels).observe(duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_counter(metric: Counter, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to increment a counter.

    Args:
        metric: Prometheus Counter to increment
        labels: Labels to apply to the metric
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                metric_labels = {**(labels or {}), "status": status}
                metric.labels(**metric_labels).inc()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                metric_labels = {**(labels or {}), "status": status}
                metric.labels(**metric_labels).inc()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Metrics Collection Functions
# =============================================================================


class MetricsCollector:
    """
    Central metrics collector for the threat intelligence pipeline.
    """

    def __init__(self):
        self.start_time = datetime.utcnow()
        self._setup_info_metrics()

    def _setup_info_metrics(self):
        """Setup static info metrics"""
        pipeline_info.info(
            {"version": "1.0.0", "start_time": self.start_time.isoformat()}
        )

    def record_fetch(
        self, source: str, duration: float, items: int, status: str = "success"
    ):
        """Record source fetch metrics"""
        source_fetch_duration.labels(source=source, status=status).observe(duration)
        source_fetch_total.labels(source=source, status=status).inc()
        if status == "success":
            source_items_fetched.labels(source=source).observe(items)

    def record_deduplication(
        self, source: str, total: int, unique: int, duration: float
    ):
        """Record deduplication metrics"""
        ratio = unique / total if total > 0 else 1.0
        deduplication_ratio.labels(source=source).set(ratio)
        duplicates_removed.labels(source=source).inc(total - unique)
        deduplication_duration.labels(strategy="default").observe(duration)

    def record_quality(self, source: str, metrics: Dict[str, float], duration: float):
        """Record quality analysis metrics"""
        for dimension, score in metrics.items():
            source_quality_score.labels(source=source, dimension=dimension).set(score)
        quality_analysis_duration.labels(source=source).observe(duration)

    def record_api_request(
        self, endpoint: str, method: str, status: int, duration: float
    ):
        """Record API request metrics"""
        status_group = f"{status // 100}xx"
        api_request_duration.labels(
            endpoint=endpoint, method=method, status=status_group
        ).observe(duration)
        api_request_total.labels(
            endpoint=endpoint, method=method, status=status_group
        ).inc()

    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access"""
        if hit:
            cache_hits.labels(cache_type=cache_type).inc()
        else:
            cache_misses.labels(cache_type=cache_type).inc()

    def record_error(self, source: str, error_type: str):
        """Record error occurrence"""
        errors_total.labels(source=source, error_type=error_type).inc()

    def update_system_metrics(self):
        """Update system resource metrics"""
        # Memory usage
        process = psutil.Process()
        memory_usage_bytes.set(process.memory_info().rss)

        # CPU usage
        cpu_usage_percent.set(process.cpu_percent())

    def update_counts(self, active_sources_count: int, total_vulns: int):
        """Update count metrics"""
        active_sources.set(active_sources_count)
        total_vulnerabilities.set(total_vulns)


# Global collector instance
metrics_collector = MetricsCollector()

# =============================================================================
# Metrics Export Functions
# =============================================================================


def get_metrics() -> bytes:
    """
    Generate metrics in Prometheus format.

    Returns:
        Metrics data in Prometheus text format
    """
    # Update system metrics before export
    metrics_collector.update_system_metrics()

    return generate_latest(metrics_registry)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST
