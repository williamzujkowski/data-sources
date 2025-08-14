"""
Source quality analysis system for monitoring data source health and quality.
Provides metrics, scoring, and recommendations for each data source.
"""

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for a data source."""

    freshness_score: float
    completeness_score: float
    uniqueness_score: float
    consistency_score: float
    accuracy_score: float
    overall_score: float

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            "freshness": round(self.freshness_score, 3),
            "completeness": round(self.completeness_score, 3),
            "uniqueness": round(self.uniqueness_score, 3),
            "consistency": round(self.consistency_score, 3),
            "accuracy": round(self.accuracy_score, 3),
            "overall": round(self.overall_score, 3),
        }


@dataclass
class SourceQualityReport:
    """Complete quality report for a source."""

    source_id: str
    timestamp: str
    metrics: QualityMetrics
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    historical_trend: Optional[str] = None
    data_samples: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "metrics": self.metrics.to_dict(),
            "issues": self.issues,
            "recommendations": self.recommendations,
            "historical_trend": self.historical_trend,
            "data_samples": self.data_samples,
        }


class SourceQualityAnalyzer:
    """
    Analyzes and scores data source quality.

    Tracks multiple quality dimensions and provides actionable recommendations.
    """

    # Quality thresholds
    THRESHOLDS = {
        "freshness_hours": 48,
        "min_completeness": 0.7,
        "min_uniqueness": 0.1,
        "min_consistency": 0.8,
        "min_accuracy": 0.85,
        "min_overall": 0.7,
    }

    # Weights for composite scoring
    WEIGHTS = {
        "freshness": 0.25,
        "completeness": 0.20,
        "uniqueness": 0.20,
        "consistency": 0.20,
        "accuracy": 0.15,
    }

    def __init__(self, history_file: str = "data/quality_history.json") -> None:
        """Initialize quality analyzer."""
        self.history_file = Path(history_file)
        self.history: Dict[str, List[Dict[str, Any]]] = self._load_history()
        self.field_requirements = self._define_field_requirements()

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load historical quality data."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load quality history: {e}")
        return defaultdict(list)

    def _save_history(self) -> None:
        """Save quality history."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(dict(self.history), f, indent=2)

    def _define_field_requirements(self) -> Dict[str, List[str]]:
        """Define required fields for different data types."""
        return {
            "vulnerability": [
                "cve_id",
                "description",
                "published",
                "cvss_score",
            ],
            "threat_intelligence": [
                "indicator",
                "type",
                "source",
                "timestamp",
            ],
            "malware": ["hash", "name", "type", "first_seen"],
            "default": ["id", "source", "timestamp"],
        }

    def analyze_source(
        self,
        source_id: str,
        data: List[Dict[str, Any]],
        data_type: str = "default",
    ) -> SourceQualityReport:
        """
        Perform comprehensive quality analysis on source data.

        Args:
            source_id: Identifier for the data source
            data: List of data items from the source
            data_type: Type of data

        Returns:
            SourceQualityReport with metrics and recommendations
        """
        if not data:
            return self._create_empty_report(source_id)

        # Calculate individual metrics
        freshness = self._calculate_freshness(data)
        completeness = self._calculate_completeness(data, data_type)
        uniqueness = self._calculate_uniqueness(source_id, data)
        consistency = self._calculate_consistency(data)
        accuracy = self._estimate_accuracy(source_id, data)

        # Calculate overall score
        overall = self._calculate_overall_score(
            {
                "freshness": freshness,
                "completeness": completeness,
                "uniqueness": uniqueness,
                "consistency": consistency,
                "accuracy": accuracy,
            }
        )

        metrics = QualityMetrics(
            freshness_score=freshness,
            completeness_score=completeness,
            uniqueness_score=uniqueness,
            consistency_score=consistency,
            accuracy_score=accuracy,
            overall_score=overall,
        )

        # Identify issues
        issues = self._identify_issues(metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(source_id, metrics, issues)

        # Analyze historical trend
        trend = self._analyze_trend(source_id, overall)

        # Create report
        report = SourceQualityReport(
            source_id=source_id,
            timestamp=datetime.utcnow().isoformat(),
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            historical_trend=trend,
            data_samples=len(data),
        )

        # Store in history
        self._store_in_history(source_id, report)

        return report

    def _calculate_freshness(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate freshness score based on data timestamps.

        Returns score from 0 (stale) to 1 (fresh).
        """
        if not data:
            return 0.0

        now = datetime.utcnow()
        freshness_scores = []

        # Fields to check for timestamps
        date_fields = [
            "modified",
            "last_modified",
            "updated",
            "published",
            "created",
            "timestamp",
        ]

        for item in data:
            item_date = None

            # Find the most recent date field
            for field in date_fields:
                if field in item and item[field]:
                    try:
                        # Parse ISO format date
                        item_date = datetime.fromisoformat(
                            item[field].replace("Z", "+00:00")
                        )
                        break
                    except (ValueError, AttributeError):
                        continue

            if item_date:
                hours_old = (now - item_date).total_seconds() / 3600
                # Linear decay over threshold period
                score = max(0, 1 - (hours_old / self.THRESHOLDS["freshness_hours"]))
                freshness_scores.append(score)
            else:
                # No date found - assume stale
                freshness_scores.append(0.0)

        return statistics.mean(freshness_scores) if freshness_scores else 0.0

    def _calculate_completeness(
        self, data: List[Dict[str, Any]], data_type: str
    ) -> float:
        """
        Calculate completeness based on required fields.

        Returns score from 0 (incomplete) to 1 (complete).
        """
        if not data:
            return 0.0

        required_fields = self.field_requirements.get(
            data_type, self.field_requirements["default"]
        )

        completeness_scores = []

        for item in data:
            # Count how many required fields are present and non-empty
            present_fields = sum(
                1
                for field in required_fields
                if field in item and item[field] is not None and item[field] != ""
            )

            score = present_fields / len(required_fields) if required_fields else 1.0
            completeness_scores.append(score)

        return statistics.mean(completeness_scores)

    def _calculate_uniqueness(
        self, source_id: str, data: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate uniqueness score based on duplicate ratio.

        Returns score from 0 (all duplicates) to 1 (all unique).
        """
        if not data:
            return 0.0

        # Use deduplicator to find unique items
        from tools.deduplication import IntelligentDeduplicator

        dedup = IntelligentDeduplicator()
        result = dedup.deduplicate(data)

        unique_ratio = len(result.unique_items) / len(data)

        # Adjust score based on source type
        # Some sources are expected to have more duplicates
        if source_id in ["nvd", "cisa_kev"]:
            # Official sources should have fewer duplicates
            return unique_ratio
        else:
            # Community sources may have more duplicates
            return min(1.0, unique_ratio * 1.2)  # Slight boost

    def _calculate_consistency(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate consistency score based on data structure uniformity.

        Returns score from 0 (inconsistent) to 1 (consistent).
        """
        if not data:
            return 0.0

        # Analyze field consistency
        field_counts: Dict[str, int] = defaultdict(int)
        total_items = len(data)

        for item in data:
            for field in item.keys():
                if item[field] is not None and item[field] != "":
                    field_counts[field] += 1

        # Calculate consistency for each field
        consistency_scores = []
        for field, count in field_counts.items():
            # How consistently does this field appear?
            consistency = count / total_items
            consistency_scores.append(consistency)

        # Also check value type consistency
        type_consistency = self._check_type_consistency(data)
        consistency_scores.append(type_consistency)

        return statistics.mean(consistency_scores) if consistency_scores else 0.0

    def _check_type_consistency(self, data: List[Dict[str, Any]]) -> float:
        """Check if field types are consistent across items."""
        if not data:
            return 1.0

        field_types: Dict[str, Set[str]] = defaultdict(set)

        for item in data:
            for field, value in item.items():
                if value is not None:
                    field_types[field].add(type(value).__name__)

        # Calculate type consistency
        consistency_scores = []
        for field, types in field_types.items():
            # Ideally, each field should have only one type
            score = 1.0 / len(types) if types else 1.0
            consistency_scores.append(score)

        return statistics.mean(consistency_scores) if consistency_scores else 1.0

    def _estimate_accuracy(self, source_id: str, data: List[Dict[str, Any]]) -> float:
        """
        Estimate accuracy based on historical performance.

        This is a simplified estimation - in production, this would involve
        more sophisticated validation against ground truth.
        """
        # Base accuracy scores for known sources
        base_scores = {
            "nvd": 0.98,
            "cisa_kev": 0.99,
            "mitre_attack": 0.95,
            "epss": 0.90,
            "otx": 0.85,
            "abuse_ch": 0.88,
        }

        base_score = base_scores.get(source_id, 0.80)

        # Adjust based on data quality indicators
        adjustments = []

        # Check for suspicious patterns
        if data:
            # Check for test data
            test_indicators = ["test", "example", "demo", "sample"]
            test_count = sum(
                1
                for item in data
                if any(
                    indicator in str(item.get("description", "")).lower()
                    for indicator in test_indicators
                )
            )
            if test_count > len(data) * 0.1:  # More than 10% test data
                adjustments.append(-0.1)

            # Check for missing critical fields
            critical_missing = sum(
                1
                for item in data
                if not item.get("id")
                and not item.get("cve_id")
                and not item.get("indicator")
            )
            if critical_missing > len(data) * 0.05:  # More than 5% missing
                adjustments.append(-0.05)

        # Apply adjustments
        final_score = base_score + sum(adjustments)
        return max(0.0, min(1.0, final_score))

    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate weighted overall quality score."""
        score = sum(metrics[metric] * self.WEIGHTS[metric] for metric in self.WEIGHTS)
        return round(score, 3)

    def _identify_issues(self, metrics: QualityMetrics) -> List[str]:
        """Identify quality issues based on metrics."""
        issues = []

        if metrics.freshness_score < 0.5:
            issues.append("Data freshness is below acceptable levels")

        if metrics.completeness_score < self.THRESHOLDS["min_completeness"]:
            issues.append(
                f"Data completeness ({metrics.completeness_score:.1%}) "
                f"is below threshold"
            )

        if metrics.uniqueness_score < self.THRESHOLDS["min_uniqueness"]:
            issues.append("High duplicate rate detected")

        if metrics.consistency_score < self.THRESHOLDS["min_consistency"]:
            issues.append("Inconsistent data structure detected")

        if metrics.accuracy_score < self.THRESHOLDS["min_accuracy"]:
            issues.append("Potential accuracy issues detected")

        if metrics.overall_score < self.THRESHOLDS["min_overall"]:
            issues.append(
                f"Overall quality score ({metrics.overall_score:.2f}) "
                f"below threshold"
            )

        return issues

    def _generate_recommendations(
        self,
        source_id: str,
        metrics: QualityMetrics,
        issues: List[str],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if metrics.freshness_score < 0.5:
            recommendations.append(
                f"Increase update frequency for {source_id} or check "
                f"if source is still active"
            )

        if metrics.completeness_score < self.THRESHOLDS["min_completeness"]:
            recommendations.append(
                "Review field mapping and ensure all required fields "
                "are being extracted"
            )

        if metrics.uniqueness_score < self.THRESHOLDS["min_uniqueness"]:
            recommendations.append(
                "Implement or improve deduplication before processing " "this source"
            )

        if metrics.consistency_score < self.THRESHOLDS["min_consistency"]:
            recommendations.append(
                "Standardize data parsing and add validation for field types"
            )

        if metrics.accuracy_score < self.THRESHOLDS["min_accuracy"]:
            recommendations.append(
                f"Validate {source_id} data against authoritative sources"
            )

        if not issues:
            recommendations.append(
                f"{source_id} is performing well - maintain current " f"configuration"
            )

        return recommendations

    def _analyze_trend(self, source_id: str, current_score: float) -> str:
        """Analyze historical trend for the source."""
        history = self.history.get(source_id, [])

        if len(history) < 2:
            return "insufficient_data"

        # Get last 10 scores
        recent_scores = [h["metrics"]["overall"] for h in history[-10:]]
        recent_scores.append(current_score)

        # Calculate trend
        if len(recent_scores) >= 3:
            # Simple linear regression trend
            x = list(range(len(recent_scores)))
            y = recent_scores

            # Calculate slope
            n = len(x)
            slope = (n * sum(i * j for i, j in zip(x, y)) - sum(x) * sum(y)) / (
                n * sum(i**2 for i in x) - sum(x) ** 2
            )

            if slope > 0.01:
                return "improving"
            elif slope < -0.01:
                return "degrading"
            else:
                return "stable"

        return "stable"

    def _store_in_history(self, source_id: str, report: SourceQualityReport) -> None:
        """Store report in history."""
        if source_id not in self.history:
            self.history[source_id] = []

        self.history[source_id].append(report.to_dict())

        # Keep only last 100 entries per source
        if len(self.history[source_id]) > 100:
            self.history[source_id] = self.history[source_id][-100:]

        self._save_history()

    def _create_empty_report(self, source_id: str) -> SourceQualityReport:
        """Create empty report for sources with no data."""
        return SourceQualityReport(
            source_id=source_id,
            timestamp=datetime.utcnow().isoformat(),
            metrics=QualityMetrics(0, 0, 0, 0, 0, 0),
            issues=["No data available from source"],
            recommendations=["Check source connectivity and configuration"],
            data_samples=0,
        )

    def get_historical_summary(self, source_id: str) -> Dict[str, Any]:
        """Get historical summary for a source."""
        history = self.history.get(source_id, [])

        if not history:
            return {"error": "No historical data available"}

        scores = [h["metrics"]["overall"] for h in history]

        return {
            "source_id": source_id,
            "total_analyses": len(history),
            "average_score": statistics.mean(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "std_deviation": (statistics.stdev(scores) if len(scores) > 1 else 0),
            "recent_trend": self._analyze_trend(source_id, scores[-1] if scores else 0),
            "last_analysis": (history[-1]["timestamp"] if history else None),
        }


def main() -> None:
    """Example usage of quality analyzer."""
    analyzer = SourceQualityAnalyzer()

    # Sample data for analysis
    sample_data = [
        {
            "cve_id": "CVE-2024-1234",
            "description": "Test vulnerability",
            "published": datetime.utcnow().isoformat(),
            "cvss_score": 7.5,
            "source": "nvd",
        },
        {
            "cve_id": "CVE-2024-5678",
            "description": "Another test",
            "published": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "cvss_score": 5.0,
            "source": "nvd",
        },
    ]

    report = analyzer.analyze_source("nvd", sample_data, "vulnerability")

    print("Quality Analysis Report")
    print("=" * 50)
    print(f"Source: {report.source_id}")
    print(f"Samples: {report.data_samples}")
    print(f"Overall Score: {report.metrics.overall_score:.2f}")
    print("\nMetrics:")
    for metric, score in report.metrics.to_dict().items():
        print(f"  {metric}: {score:.3f}")
    print("\nIssues:")
    for issue in report.issues:
        print(f"  - {issue}")
    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")


if __name__ == "__main__":
    main()
