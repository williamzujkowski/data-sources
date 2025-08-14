"""
Intelligent deduplication system with fuzzy matching and authority ranking.
Uses bloom filters for efficient duplicate detection and multiple strategies
for handling near-duplicates.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import mmh3
from pybloom_live import BloomFilter
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    """Results from deduplication process."""

    unique_items: List[Dict[str, Any]]
    duplicates: List[Dict[str, Any]]
    merged_items: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    processing_time: float

    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Deduplication Results:\n"
            f"  Unique items: {len(self.unique_items)}\n"
            f"  Duplicates removed: {len(self.duplicates)}\n"
            f"  Items merged: {len(self.merged_items)}\n"
            f"  Reduction ratio: {self.statistics.get('reduction_ratio', 0):.2%}\n"
            f"  Processing time: {self.processing_time:.2f}s"
        )


@dataclass
class DuplicateStrategy:
    """Strategy for handling duplicates."""

    name: str
    merge_fields: bool = False
    keep_highest_authority: bool = True
    aggregate_scores: bool = False
    preserve_all_sources: bool = True


class IntelligentDeduplicator:
    """
    Advanced deduplication with multiple strategies.

    Features:
    - Bloom filter for O(1) duplicate checking
    - Fuzzy matching for near-duplicates
    - Authority-based conflict resolution
    - Field merging for complementary data
    - Performance optimized for large datasets
    """

    # Authority scores for different sources (higher = more authoritative)
    AUTHORITY_SCORES = {
        "cisa_kev": 10,
        "nvd": 9,
        "mitre_attack": 9,
        "mitre_defend": 8,
        "epss": 8,
        "otx": 7,
        "abuse_ch_urlhaus": 6,
        "abuse_ch_malwarebazaar": 6,
        "abuse_ch_feodotracker": 6,
        "abuse_ch_threatfox": 6,
        "community": 5,
        "unknown": 1,
    }

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        bloom_capacity: int = 1000000,
        bloom_error_rate: float = 0.001,
    ) -> None:
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity score for duplicates
            bloom_capacity: Expected number of unique items
            bloom_error_rate: Acceptable false positive rate
        """
        self.similarity_threshold = similarity_threshold
        self.bloom_filter = BloomFilter(
            capacity=bloom_capacity, error_rate=bloom_error_rate
        )
        self.exact_hashes: Set[str] = set()
        self.item_cache: Dict[str, Dict[str, Any]] = {}
        self.merge_history: List[Tuple[str, str]] = []

    def deduplicate(
        self,
        items: List[Dict[str, Any]],
        strategy: Optional[DuplicateStrategy] = None,
    ) -> DeduplicationResult:
        """
        Perform intelligent deduplication on items.

        Args:
            items: List of items to deduplicate
            strategy: Deduplication strategy to use

        Returns:
            DeduplicationResult with unique items and statistics
        """
        start_time = datetime.utcnow()

        if strategy is None:
            strategy = DuplicateStrategy(
                name="default",
                keep_highest_authority=True,
                merge_fields=True,
                preserve_all_sources=True,
            )

        # Sort by authority score (highest first)
        sorted_items = self._sort_by_authority(items)

        unique_items: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []
        merged_items: List[Dict[str, Any]] = []

        for item in sorted_items:
            item_hash = self._generate_hash(item)

            # Check exact duplicate
            if item_hash in self.exact_hashes:
                duplicates.append(item)  # Always track as duplicate
                if strategy.merge_fields:
                    # Find the matching item to merge with
                    matching_item = self.item_cache.get(item_hash)
                    if matching_item and matching_item in unique_items:
                        merged = self._merge_items(matching_item, item, strategy)
                        merged_items.append(merged)
                        idx = unique_items.index(matching_item)
                        unique_items[idx] = merged
                        self.item_cache[item_hash] = merged
                continue

            # Check bloom filter for potential duplicates
            if item_hash in self.bloom_filter:
                # Potential duplicate - do detailed check
                similar_item = self._find_similar(item, unique_items)

                if similar_item:
                    if strategy.merge_fields:
                        # Merge complementary fields
                        merged = self._merge_items(similar_item, item, strategy)
                        merged_items.append(merged)
                        # Update the item in unique_items
                        idx = unique_items.index(similar_item)
                        unique_items[idx] = merged
                    else:
                        duplicates.append(item)
                    continue

            # Add to unique items
            unique_items.append(item)
            self.exact_hashes.add(item_hash)
            self.bloom_filter.add(item_hash)
            self.item_cache[item_hash] = item

        # Calculate statistics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        statistics = self._calculate_statistics(
            len(items), len(unique_items), len(duplicates), len(merged_items)
        )

        return DeduplicationResult(
            unique_items=unique_items,
            duplicates=duplicates,
            merged_items=merged_items,
            statistics=statistics,
            processing_time=processing_time,
        )

    def _sort_by_authority(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort items by authority score (highest first)."""

        def get_authority(item: Dict[str, Any]) -> int:
            source = item.get("source", "unknown").lower()
            return self.AUTHORITY_SCORES.get(source, 1)

        return sorted(items, key=get_authority, reverse=True)

    def _generate_hash(self, item: Dict[str, Any]) -> str:
        """
        Generate hash for an item based on key fields.

        Uses multiple fields to create a unique identifier.
        """
        key_parts = []

        # Primary identifiers
        if "cve_id" in item:
            key_parts.append(f"cve:{item['cve_id']}")

        if "indicator" in item:
            # For IoCs (IPs, domains, hashes)
            key_parts.append(f"ioc:{item['indicator']}")

        if "pulse_id" in item:
            # For OTX pulses
            key_parts.append(f"pulse:{item['pulse_id']}")

        if "md5" in item or "sha256" in item:
            # For malware samples
            hash_val = item.get("sha256") or item.get("md5")
            key_parts.append(f"hash:{hash_val}")

        # Secondary identifiers for items without primary IDs
        if not key_parts:
            # Use description/title fingerprint
            if "description" in item:
                # Normalize and truncate description
                desc = item["description"].lower().strip()[:200]
                desc_hash = mmh3.hash(desc)
                key_parts.append(f"desc:{desc_hash}")

            if "title" in item or "name" in item:
                title = item.get("title") or item.get("name", "")
                title_hash = mmh3.hash(title.lower().strip())
                key_parts.append(f"title:{title_hash}")

        # Combine all parts
        if not key_parts:
            # Fallback to full item hash
            key_parts.append(f"full:{mmh3.hash(json.dumps(item, sort_keys=True))}")

        combined = "|".join(key_parts)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _find_similar(
        self, item: Dict[str, Any], existing_items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find similar item using fuzzy matching.

        Returns the most similar item if similarity exceeds threshold.
        """
        if not existing_items:
            return None

        # Quick check for exact ID matches
        if "cve_id" in item:
            for existing in existing_items:
                if existing.get("cve_id") == item["cve_id"]:
                    return existing

        # Fuzzy matching on descriptions
        if "description" in item:
            item_desc = item["description"]

            # Build list of descriptions from existing items
            existing_descs = [
                (existing, existing.get("description", ""))
                for existing in existing_items
                if existing.get("description")
            ]

            if existing_descs:
                # Use rapidfuzz for efficient fuzzy matching
                matches = process.extract(
                    item_desc,
                    [desc for _, desc in existing_descs],
                    scorer=fuzz.token_sort_ratio,
                    limit=1,
                )

                if matches and matches[0][1] >= self.similarity_threshold * 100:
                    # Return the matching item
                    idx = [desc for _, desc in existing_descs].index(matches[0][0])
                    return existing_descs[idx][0]

        return None

    def _merge_items(
        self,
        primary: Dict[str, Any],
        secondary: Dict[str, Any],
        strategy: DuplicateStrategy,
    ) -> Dict[str, Any]:
        """
        Merge two similar items according to strategy.

        Primary item (higher authority) takes precedence.
        """
        merged = primary.copy()

        # Track merge in history
        self.merge_history.append(
            (self._generate_hash(primary), self._generate_hash(secondary))
        )

        # Preserve source information
        if strategy.preserve_all_sources:
            sources = set(merged.get("sources", [merged.get("source", "unknown")]))
            sources.add(secondary.get("source", "unknown"))
            merged["sources"] = list(sources)

        # Merge complementary fields
        if strategy.merge_fields:
            # Merge lists
            list_fields = [
                "references",
                "tags",
                "cwe_ids",
                "attack_techniques",
            ]
            for field in list_fields:
                if field in secondary and field not in merged:
                    merged[field] = secondary[field]
                elif field in secondary and field in merged:
                    # Combine and deduplicate
                    combined = list(
                        set(merged.get(field, []) + secondary.get(field, []))
                    )
                    merged[field] = combined

            # Merge scores (take maximum)
            score_fields = ["cvss_v3_score", "cvss_v2_score", "epss_score"]
            for field in score_fields:
                if field in secondary:
                    merged[field] = max(merged.get(field, 0), secondary.get(field, 0))

            # Add missing fields
            for key, value in secondary.items():
                if key not in merged and value is not None:
                    merged[key] = value

        # Update metadata
        merged["deduplication"] = {
            "merged": True,
            "merge_time": datetime.utcnow().isoformat(),
            "primary_source": primary.get("source"),
            "secondary_source": secondary.get("source"),
        }

        return merged

    def _calculate_statistics(
        self, total: int, unique: int, duplicates: int, merged: int
    ) -> Dict[str, Any]:
        """Calculate deduplication statistics."""
        return {
            "total_input": total,
            "unique_output": unique,
            "duplicates_removed": duplicates,
            "items_merged": merged,
            "reduction_ratio": (total - unique) / total if total > 0 else 0,
            "merge_ratio": merged / total if total > 0 else 0,
            "bloom_filter_size": len(self.bloom_filter),
            "exact_hashes_stored": len(self.exact_hashes),
        }

    def reset(self) -> None:
        """Reset deduplicator state."""
        # Recreate bloom filter as pybloom_live doesn't have clear method
        self.bloom_filter = BloomFilter(
            capacity=self.bloom_filter.capacity, error_rate=self.bloom_filter.error_rate
        )
        self.exact_hashes.clear()
        self.item_cache.clear()
        self.merge_history.clear()


def main() -> None:
    """Example usage of deduplicator."""
    # Create sample data with duplicates
    items = [
        {
            "cve_id": "CVE-2024-1234",
            "source": "nvd",
            "description": "SQL injection vulnerability",
            "cvss_v3_score": 7.5,
        },
        {
            "cve_id": "CVE-2024-1234",
            "source": "cisa_kev",
            "description": "SQL injection vulnerability in Product X",
            "cvss_v3_score": 7.5,
            "kev_date_added": "2024-01-15",
        },
        {
            "cve_id": "CVE-2024-5678",
            "source": "nvd",
            "description": "XSS vulnerability",
            "cvss_v3_score": 6.1,
        },
    ]

    # Deduplicate with merging
    dedup = IntelligentDeduplicator()
    result = dedup.deduplicate(items)

    print(result.summary())
    print(f"\nUnique items: {len(result.unique_items)}")
    for item in result.unique_items:
        print(f"  - {item.get('cve_id')}: {item.get('sources', [item.get('source')])}")


if __name__ == "__main__":
    main()
