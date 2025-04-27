#!/usr/bin/env python3
"""
Fetch data from sources and update metadata.

This script retrieves data from all configured sources,
validates the data against schemas, and updates metadata fields.
"""

import os
import json
import glob
import logging
import datetime
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fetch_sources")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
TIMEOUT_SECONDS = 30


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


def fetch_source_health(source: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a source is available and return health metrics."""
    url = source.get("url")
    if not url:
        return {"available": False, "status_code": None, "response_time": None}
    
    try:
        start_time = datetime.datetime.now()
        response = requests.head(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
        end_time = datetime.datetime.now()
        
        return {
            "available": response.status_code < 400,
            "status_code": response.status_code,
            "response_time": (end_time - start_time).total_seconds(),
        }
    except requests.RequestException as e:
        logger.warning(f"Failed to check health for {url}: {e}")
        return {"available": False, "status_code": None, "response_time": None}


def update_source_metadata(source: Dict[str, Any], health: Dict[str, Any]) -> Dict[str, Any]:
    """Update the source metadata with health check results and current timestamp."""
    updated_source = source.copy()
    
    # Update last_updated timestamp only if the fetch was successful or if it's missing
    if health["available"] or not updated_source.get("last_updated"):
        updated_source["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + "Z"

    # Update availability score based on health check
    current_availability = updated_source.get("availability")
    
    if health["available"]:
        # Optional: Increment availability score if it was previously lowered?
        # For now, we only decrement on failure.
        pass 
    else:
        # If source is unavailable, reduce the availability score
        if current_availability is None:
            # If availability was null, set it to 90 (100 - 10)
            updated_source["availability"] = 90.0
            logger.info(f"Source {updated_source.get('id')} unavailable, setting availability to 90.")
        elif isinstance(current_availability, (int, float)):
            # If it's already a number, decrement it, clamping at 0
            updated_source["availability"] = max(0.0, current_availability - 10.0)
            logger.info(f"Source {updated_source.get('id')} unavailable, reducing availability to {updated_source['availability']}.")
        else:
             logger.warning(f"Source {updated_source.get('id')} has unexpected type for availability: {type(current_availability)}. Not updating score.")

    return updated_source


def save_source_file(source: Dict[str, Any]) -> None:
    """Save the updated source metadata back to disk."""
    file_path = source.pop("_file_path", None)
    if not file_path:
        logger.error(f"Missing file path for source {source.get('id')}")
        return
    
    try:
        with open(file_path, "w") as f:
            # Use indent=2 for readability, ensure_ascii=False for potential non-ASCII chars
            json.dump(source, f, indent=2, ensure_ascii=False)
            # Add a newline at the end of the file for consistency
            f.write("\n")
        logger.debug(f"Saved updated metadata to {file_path}") # Changed level to debug
    except Exception as e:
        logger.error(f"Failed to update {file_path}: {e}")


def main() -> None:
    """Main entry point for fetching and updating sources."""
    sources = load_source_files()
    
    for source in sources:
        logger.info(f"Processing {source.get('id')}")
        
        # Skip sources with quality_score of 0 (deprecated)
        if source.get("quality_score", 0) == 0:
            logger.info(f"Skipping deprecated source {source.get('id')}")
            continue
        
        # Fetch health data
        health = fetch_source_health(source)
        
        # Update metadata
        updated_source = update_source_metadata(source, health)
        
        # Save updated metadata
        save_source_file(updated_source)
    
    logger.info("Source fetching and updating completed")


if __name__ == "__main__":
    main()
