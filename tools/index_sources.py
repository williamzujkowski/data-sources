#!/usr/bin/env python3
"""
Build index for fast, minimal-token lookups.

This script creates and updates a search index for efficient
querying of data sources based on various attributes.
"""

import glob
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from sqlitedict import SqliteDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("index_sources")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
INDEX_PATH = ROOT_DIR / "index.db"


def load_source_files() -> List[Dict[str, Any]]:
    """Load all source metadata files."""
    sources = []
    for file_path in glob.glob(f"{DATA_SOURCES_DIR}/**/*.json", recursive=True):
        try:
            with open(file_path, "r") as f:
                source = json.load(f)
                sources.append(source)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse {file_path} as JSON")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    logger.info(f"Loaded {len(sources)} source files")
    return sources


def build_category_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build index of sources by category."""
    category_index = {}

    for source in sources:
        category = source.get("category")
        if not category:
            continue

        if category not in category_index:
            category_index[category] = []

        category_index[category].append(source["id"])

    return category_index


def build_tag_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build index of sources by tag."""
    tag_index = {}

    for source in sources:
        tags = source.get("tags", [])
        for tag in tags:
            if tag not in tag_index:
                tag_index[tag] = []

            tag_index[tag].append(source["id"])

    return tag_index


def build_format_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build index of sources by format."""
    format_index = {}

    for source in sources:
        format_type = source.get("format")
        if not format_type:
            continue

        if format_type not in format_index:
            format_index[format_type] = []

        format_index[format_type].append(source["id"])

    return format_index


def build_source_lookup(sources: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build lookup dictionary for source details by ID."""
    source_lookup = {}

    for source in sources:
        source_id = source.get("id")
        if not source_id:
            continue

        # Create a minimal version of the source with just essential fields
        # to keep the index size small
        minimal_source = {
            "id": source["id"],
            "name": source["name"],
            "url": source["url"],
            "category": source["category"],
            "format": source["format"],
            "quality_score": source["quality_score"],
            "last_updated": source["last_updated"],
        }

        # Add optional fields if they exist
        for field in ["sub_category", "description", "user_weighted_score"]:
            if field in source:
                minimal_source[field] = source[field]

        source_lookup[source_id] = minimal_source

    return source_lookup


def build_quality_index(sources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build index of sources by quality score buckets."""
    quality_index = {
        "excellent": [],  # 90-100
        "good": [],  # 70-89
        "average": [],  # 50-69
        "poor": [],  # 1-49
        "deprecated": [],  # 0
    }

    for source in sources:
        source_id = source.get("id")
        if not source_id:
            continue

        score = source.get("quality_score", 0)

        if score >= 90:
            quality_index["excellent"].append(source_id)
        elif score >= 70:
            quality_index["good"].append(source_id)
        elif score >= 50:
            quality_index["average"].append(source_id)
        elif score > 0:
            quality_index["poor"].append(source_id)
        else:
            quality_index["deprecated"].append(source_id)

    return quality_index


def save_index(
    category_index: Dict[str, List[str]],
    tag_index: Dict[str, List[str]],
    format_index: Dict[str, List[str]],
    source_lookup: Dict[str, Dict[str, Any]],
    quality_index: Dict[str, List[str]],
) -> None:
    """Save all index data to SQLite database."""
    try:
        with SqliteDict(str(INDEX_PATH), autocommit=False) as db:
            # Store each index type
            db["category_index"] = category_index
            db["tag_index"] = tag_index
            db["format_index"] = format_index
            db["source_lookup"] = source_lookup
            db["quality_index"] = quality_index

            # Store index metadata
            db["index_metadata"] = {
                "source_count": len(source_lookup),
                "category_count": len(category_index),
                "tag_count": len(tag_index),
                "format_count": len(format_index),
            }

            # Commit changes
            db.commit()

        logger.info(f"Successfully saved index to {INDEX_PATH}")
        logger.info(f"Indexed {len(source_lookup)} sources")
    except Exception as e:
        logger.error(f"Failed to save index: {e}")


def main() -> None:
    """Main entry point for indexing sources."""
    # Load all source files
    sources = load_source_files()

    # Build indices
    category_index = build_category_index(sources)
    tag_index = build_tag_index(sources)
    format_index = build_format_index(sources)
    source_lookup = build_source_lookup(sources)
    quality_index = build_quality_index(sources)

    # Save indices to database
    save_index(category_index, tag_index, format_index, source_lookup, quality_index)

    logger.info("Source indexing completed")


if __name__ == "__main__":
    main()
