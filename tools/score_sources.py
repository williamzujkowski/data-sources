#!/usr/bin/env python3
"""
Calculate quality scores for data sources.

This script recalculates quality scores for all data sources
based on freshness, authority, coverage, and availability metrics.
"""

import datetime
import glob
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("score_sources")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
CONFIG_DIR = ROOT_DIR / "config"


def load_scoring_config() -> Dict[str, Any]:
    """Load scoring configuration from config file."""
    config_path = CONFIG_DIR / "scoring-config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load scoring config: {e}")
        # Return default weights if config file can't be loaded
        return {
            "weights": {
                "freshness": 0.4,
                "authority": 0.3,
                "coverage": 0.2,
                "availability": 0.1,
            }
        }


def load_source_files() -> List[Dict[str, Any]]:
    """Load all source metadata files."""
    sources = []
    for file_path in glob.glob(f"{DATA_SOURCES_DIR}/**/*.json", recursive=True):
        try:
            with open(file_path, "r") as f:
                source = json.load(f)
                source["_file_path"] = file_path
                sources.append(source)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse {file_path} as JSON")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    logger.info(f"Loaded {len(sources)} source files")
    return sources


def calculate_freshness_score(last_updated_str: Optional[str]) -> float:
    """Calculate freshness score (0-100) based on last update date."""
    if not last_updated_str:
        # logger.warning("Missing or invalid last_updated string, returning freshness 0.")
        # Reducing noise, this is expected for new/unfetched files
        return 0
    try:
        # Handle ISO 8601 format with 'Z' for UTC explicitly
        if last_updated_str.endswith("Z"):
            # Replace 'Z' with '+00:00' for compatibility with fromisoformat
            last_updated_str = last_updated_str[:-1] + "+00:00"

        last_updated = datetime.datetime.fromisoformat(last_updated_str)

        # Ensure 'now' is timezone-aware (UTC) to compare with last_updated (which is now UTC)
        now = datetime.datetime.now(datetime.timezone.utc)

        days_since_update = (now - last_updated).days

        # Score decreases as days increase
        # 0 days = 100, 30 days = 50, 60+ days = 0
        freshness_score = max(0, 100 - (days_since_update * 100 / 60))
        return freshness_score
    except Exception as e:
        logger.error(f"Error calculating freshness: {e}")
        return 0


def calculate_quality_score(source: Dict[str, Any], weights: Dict[str, float]) -> float:
    """Calculate overall quality score based on component metrics and weights."""
    default_score = 50.0  # Default score for missing or null metrics

    # Use values from source if available, otherwise use defaults
    freshness = calculate_freshness_score(
        source.get("last_updated")
    )  # Handles None internally

    # Handle potential None values explicitly for other metrics
    authority = source.get("authority")
    authority = authority if authority is not None else default_score

    coverage = source.get("coverage")
    coverage = coverage if coverage is not None else default_score

    availability = source.get("availability")
    availability = availability if availability is not None else default_score

    # Calculate weighted score
    quality_score = (
        freshness * weights.get("freshness", 0.4)
        + authority * weights.get("authority", 0.3)
        + coverage * weights.get("coverage", 0.2)
        + availability * weights.get("availability", 0.1)
    )

    return round(quality_score, 1)


def calculate_user_weighted_score(
    source: Dict[str, Any],
    weights: Dict[str, float],
    user_weights: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate user-weighted score based on user preference weights."""
    default_score = 50.0  # Default score for missing or null metrics

    if not user_weights:
        # If no user weights provided, return the standard quality score
        # Ensure quality_score exists, otherwise calculate it
        # Check if quality_score is present and not None before returning
        existing_score = source.get("quality_score")
        if existing_score is not None:
            return existing_score
        else:
            # If quality_score is missing or null, calculate it using default weights
            return calculate_quality_score(source, weights)

    # Use values from source if available, otherwise use defaults
    freshness = calculate_freshness_score(
        source.get("last_updated")
    )  # Handles None internally

    # Handle potential None values explicitly for other metrics
    authority = source.get("authority")
    authority = authority if authority is not None else default_score

    coverage = source.get("coverage")
    coverage = coverage if coverage is not None else default_score

    availability = source.get("availability")
    availability = availability if availability is not None else default_score

    # Normalize user weights to sum to 1
    weight_sum = sum(user_weights.values())
    if weight_sum == 0:
        # If all weights are 0, return the standard quality score
        existing_score = source.get("quality_score")
        if existing_score is not None:
            return existing_score
        else:
            # If quality_score is missing or null, calculate it using default weights
            return calculate_quality_score(source, weights)

    normalized_weights = {k: v / weight_sum for k, v in user_weights.items()}
    # Calculate weighted score using user weights
    weighted_score = (
        freshness * normalized_weights.get("freshness", weights.get("freshness", 0.4))
        + authority * normalized_weights.get("authority", weights.get("authority", 0.3))
        + coverage * normalized_weights.get("coverage", weights.get("coverage", 0.2))
        + availability
        * normalized_weights.get("availability", weights.get("availability", 0.1))
    )

    return round(weighted_score, 1)


def save_source_file(source: Dict[str, Any]) -> None:
    """Save the updated source metadata back to disk."""
    file_path = source.pop("_file_path", None)
    if not file_path:
        logger.error(f"Missing file path for source {source.get('id')}")
        return

    try:
        with open(file_path, "w") as f:
            json.dump(source, f, indent=2)
        logger.info(f"Updated {file_path}")
    except Exception as e:
        logger.error(f"Failed to update {file_path}: {e}")


def main() -> None:
    """Main entry point for scoring sources."""
    # Load scoring configuration
    config = load_scoring_config()
    weights = config.get("weights", {})

    # Load all source files
    sources = load_source_files()

    # Process each source
    for source in sources:
        logger.info(f"Scoring {source.get('id')}")

        # Calculate quality score
        quality_score = calculate_quality_score(source, weights)
        source["quality_score"] = quality_score

        # Calculate user-weighted score (handles case where user_weights might be None or empty)
        user_weights = source.get(
            "user_preference_weight"
        )  # Get potential user weights
        user_weighted_score = calculate_user_weighted_score(
            source, weights, user_weights
        )
        source["user_weighted_score"] = (
            user_weighted_score  # Store it (might be same as quality_score)
        )

        # Save updated source
        save_source_file(source)

    logger.info("Source scoring completed")


if __name__ == "__main__":
    main()
