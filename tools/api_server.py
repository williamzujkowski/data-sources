"""
FastAPI server for threat intelligence pipeline with metrics endpoint.
Provides REST API, health checks, and Prometheus metrics.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field

from tools.deduplication import IntelligentDeduplicator
from tools.metrics import get_metrics, get_metrics_content_type, metrics_collector
from tools.quality_analyzer import SourceQualityAnalyzer as QualityAnalyzer
from tools.sources.nvd_fetcher import NVDFetcher

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    uptime_seconds: float
    checks: Dict[str, str]


class DeduplicationRequest(BaseModel):
    """Request for deduplication endpoint."""

    items: List[Dict[str, Any]]
    strategy: Optional[str] = "default"
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class DeduplicationResponse(BaseModel):
    """Response from deduplication endpoint."""

    unique_items: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    processing_time: float


class QualityAnalysisRequest(BaseModel):
    """Request for quality analysis."""

    source_name: str
    items: List[Dict[str, Any]]
    analyze_timeliness: bool = True
    analyze_completeness: bool = True
    analyze_consistency: bool = True


class QualityAnalysisResponse(BaseModel):
    """Response from quality analysis."""

    source_name: str
    quality_score: float
    dimensions: Dict[str, float]
    recommendations: List[str]
    analysis_time: float


class VulnerabilityQuery(BaseModel):
    """Query parameters for vulnerability search."""

    cve_id: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    days_back: int = Field(default=7, ge=1, le=90)
    limit: int = Field(default=100, ge=1, le=1000)


# =============================================================================
# Application Lifecycle
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Initialize resources on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting Threat Intelligence API Server")
    app.state.start_time = time.time()
    app.state.deduplicator = IntelligentDeduplicator()
    app.state.quality_analyzer = QualityAnalyzer()
    app.state.nvd_fetcher = NVDFetcher()

    # Load any cached data
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Initialize metrics
    metrics_collector.update_counts(active_sources_count=3, total_vulns=0)

    yield

    # Shutdown
    logger.info("Shutting down API Server")
    if hasattr(app.state, "nvd_fetcher"):
        if app.state.nvd_fetcher.session:
            await app.state.nvd_fetcher.session.close()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Threat Intelligence Pipeline API",
    description="REST API for vulnerability data with deduplication and quality analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Middleware for Request Tracking
# =============================================================================


@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all HTTP requests for metrics."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    metrics_collector.record_api_request(
        endpoint=request.url.path,
        method=request.method,
        status=response.status_code,
        duration=duration,
    )

    # Add timing header
    response.headers["X-Process-Time"] = str(duration)

    return response


# =============================================================================
# Health and Monitoring Endpoints
# =============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for liveness probe.
    """
    checks = {}

    # Check database/cache
    try:
        cache_path = Path("data/cache")
        if cache_path.exists():
            checks["cache"] = "healthy"
        else:
            checks["cache"] = "missing"
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"

    # Check NVD connection
    try:
        if hasattr(app.state, "nvd_fetcher"):
            checks["nvd"] = "configured"
        else:
            checks["nvd"] = "not_initialized"
    except Exception as e:
        checks["nvd"] = f"error: {str(e)}"

    uptime = time.time() - app.state.start_time

    return HealthResponse(
        status="healthy" if all(v != "error" for v in checks.values()) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime,
        checks=checks,
    )


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for readiness probe.
    Returns 200 if ready to serve traffic, 503 if not.
    """
    # Check if essential components are initialized
    if not hasattr(app.state, "deduplicator"):
        raise HTTPException(status_code=503, detail="Deduplicator not initialized")

    if not hasattr(app.state, "quality_analyzer"):
        raise HTTPException(status_code=503, detail="Quality analyzer not initialized")

    return {"status": "ready"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type(),
    )


# =============================================================================
# Vulnerability Endpoints
# =============================================================================


@app.get("/api/v1/vulnerabilities")
async def get_vulnerabilities(
    cve_id: Optional[str] = Query(None, description="Specific CVE ID"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    product: Optional[str] = Query(None, description="Filter by product"),
    min_score: Optional[float] = Query(
        None, ge=0.0, le=10.0, description="Minimum CVSS score"
    ),
    max_score: Optional[float] = Query(
        None, ge=0.0, le=10.0, description="Maximum CVSS score"
    ),
    days_back: int = Query(7, ge=1, le=90, description="Days to look back"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """
    Fetch vulnerabilities with optional filtering.
    """
    start_time = time.time()

    try:
        # Fetch recent vulnerabilities
        async with app.state.nvd_fetcher as fetcher:
            cves = await fetcher.fetch_recent(days=days_back)

        # Apply filters
        filtered = cves

        if cve_id:
            filtered = [v for v in filtered if v.cve_id == cve_id]

        if vendor:
            filtered = [
                v for v in filtered if v.vendor and vendor.lower() in v.vendor.lower()
            ]

        if product:
            filtered = [
                v
                for v in filtered
                if v.product and product.lower() in v.product.lower()
            ]

        if min_score is not None:
            filtered = [
                v for v in filtered if v.cvss_v3_score and v.cvss_v3_score >= min_score
            ]

        if max_score is not None:
            filtered = [
                v for v in filtered if v.cvss_v3_score and v.cvss_v3_score <= max_score
            ]

        # Limit results
        filtered = filtered[:limit]

        # Record metrics
        duration = time.time() - start_time
        metrics_collector.record_fetch(
            source="nvd",
            duration=duration,
            items=len(filtered),
            status="success",
        )

        return {
            "total": len(filtered),
            "items": [v.to_dict() for v in filtered],
            "query_time": duration,
        }

    except Exception as e:
        logger.error(f"Error fetching vulnerabilities: {e}")
        metrics_collector.record_error(source="nvd", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vulnerabilities/{cve_id}")
async def get_vulnerability(cve_id: str):
    """
    Get details for a specific CVE.
    """
    result = await get_vulnerabilities(cve_id=cve_id, limit=1)

    if not result["items"]:
        raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")

    return result["items"][0]


# =============================================================================
# Deduplication Endpoints
# =============================================================================


@app.post("/api/v1/deduplicate", response_model=DeduplicationResponse)
async def deduplicate_items(request: DeduplicationRequest):
    """
    Deduplicate a list of threat intelligence items.
    """
    start_time = time.time()

    try:
        # Configure deduplicator
        app.state.deduplicator.similarity_threshold = request.similarity_threshold

        # Perform deduplication
        result = app.state.deduplicator.deduplicate(request.items)

        # Record metrics
        duration = time.time() - start_time
        metrics_collector.record_deduplication(
            source="api",
            total=len(request.items),
            unique=len(result.unique_items),
            duration=duration,
        )

        return DeduplicationResponse(
            unique_items=result.unique_items,
            statistics=result.statistics,
            processing_time=duration,
        )

    except Exception as e:
        logger.error(f"Deduplication error: {e}")
        metrics_collector.record_error(
            source="deduplication", error_type=type(e).__name__
        )
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Quality Analysis Endpoints
# =============================================================================


@app.post("/api/v1/analyze/quality", response_model=QualityAnalysisResponse)
async def analyze_quality(request: QualityAnalysisRequest):
    """
    Analyze the quality of threat intelligence data.
    """
    start_time = time.time()

    try:
        # Perform quality analysis
        result = app.state.quality_analyzer.analyze_source(
            source_name=request.source_name,
            items=request.items,
        )

        # Calculate dimensions
        dimensions = {}
        if request.analyze_timeliness:
            dimensions["timeliness"] = result.metrics.freshness_score
        if request.analyze_completeness:
            dimensions["completeness"] = result.metrics.completeness_score
        if request.analyze_consistency:
            dimensions["consistency"] = result.metrics.consistency_score

        # Record metrics
        duration = time.time() - start_time
        metrics_collector.record_quality(
            source=request.source_name,
            metrics=dimensions,
            duration=duration,
        )

        return QualityAnalysisResponse(
            source_name=request.source_name,
            quality_score=result.metrics.overall_score,
            dimensions=dimensions,
            recommendations=result.recommendations,
            analysis_time=duration,
        )

    except Exception as e:
        logger.error(f"Quality analysis error: {e}")
        metrics_collector.record_error(source="quality", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Statistics Endpoints
# =============================================================================


@app.get("/api/v1/stats")
async def get_statistics():
    """
    Get current pipeline statistics.
    """
    # Gather statistics from various components
    stats = {
        "uptime_seconds": time.time() - app.state.start_time,
        "deduplicator": {
            "total_processed": len(app.state.deduplicator.exact_hashes),
            "cache_size": len(app.state.deduplicator.item_cache),
            "merge_history": len(app.state.deduplicator.merge_history),
        },
        "quality": {
            "sources_analyzed": len(app.state.quality_analyzer.history),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    return stats


@app.get("/api/v1/sources")
async def get_sources():
    """
    Get list of configured data sources.
    """
    sources = [
        {
            "name": "nvd",
            "type": "vulnerability",
            "status": "active",
            "last_sync": app.state.nvd_fetcher.sync_state.get("last_sync"),
        },
        {
            "name": "cisa_kev",
            "type": "vulnerability",
            "status": "planned",
            "last_sync": None,
        },
        {
            "name": "alienvault_otx",
            "type": "indicators",
            "status": "planned",
            "last_sync": None,
        },
    ]

    return {"sources": sources, "total": len(sources)}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "tools.api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
