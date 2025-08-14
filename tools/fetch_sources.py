#!/usr/bin/env python3
"""
Fetch data from sources and update metadata.

This script retrieves data from all configured sources,
validates the data against schemas, and updates metadata fields.
"""

import datetime
import glob
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests


# Custom Exceptions
class DataSourceError(Exception):
    """Base exception for data source operations."""

    pass


class SourceFileError(DataSourceError):
    """Exception raised when source file operations fail."""

    pass


class HealthCheckError(DataSourceError):
    """Exception raised when health check operations fail."""

    pass


class MetadataUpdateError(DataSourceError):
    """Exception raised when metadata update operations fail."""

    pass


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
    """
    Load all source metadata files from the data sources directory.

    Returns:
        List of source metadata dictionaries with _file_path added.

    Raises:
        SourceFileError: If no source files are found or directory doesn't exist.
    """
    if not DATA_SOURCES_DIR.exists():
        raise SourceFileError(
            f"Data sources directory does not exist: {DATA_SOURCES_DIR}"
        )

    sources: List[Dict[str, Any]] = []
    pattern = f"{DATA_SOURCES_DIR}/**/*.json"
    file_paths = glob.glob(pattern, recursive=True)

    if not file_paths:
        logger.warning(f"No JSON files found in {DATA_SOURCES_DIR}")
        return sources

    failed_files = []
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = json.load(f)

                # Validate required fields
                if not isinstance(source, dict):
                    logger.error(
                        f"Invalid source format in {file_path}: expected dict, got {type(source)}"
                    )
                    failed_files.append(file_path)
                    continue

                if "id" not in source:
                    logger.error(f"Missing required 'id' field in {file_path}")
                    failed_files.append(file_path)
                    continue

                source["_file_path"] = file_path
                sources.append(source)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path} as JSON: {e}")
            failed_files.append(file_path)
        except (IOError, OSError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            failed_files.append(file_path)
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}")
            failed_files.append(file_path)

    logger.info(f"Successfully loaded {len(sources)} source files")
    if failed_files:
        logger.warning(
            f"Failed to load {len(failed_files)} files: {failed_files[:5]}{'...' if len(failed_files) > 5 else ''}"
        )

    return sources


def fetch_source_health(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if a source is available and return health metrics.

    Args:
        source: Source metadata dictionary containing URL and other details.

    Returns:
        Dictionary with health check results including:
        - available: bool indicating if source is reachable
        - status_code: HTTP status code or None if request failed
        - response_time: Response time in seconds or None if request failed
        - error_message: Error message if request failed (optional)

    Raises:
        HealthCheckError: If source data is invalid.
    """
    if not isinstance(source, dict):
        raise HealthCheckError(
            f"Invalid source data: expected dict, got {type(source)}"
        )

    source_id = source.get("id", "unknown")
    url = source.get("url")

    if not url:
        logger.debug(f"No URL provided for source {source_id}")
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": "No URL provided",
        }

    if not isinstance(url, str):
        logger.error(
            f"Invalid URL type for source {source_id}: expected str, got {type(url)}"
        )
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": f"Invalid URL type: {type(url)}",
        }

    try:
        start_time = datetime.datetime.now()

        # Configure request with appropriate headers and timeout
        headers = {"User-Agent": "data-sources-manager/0.1.0", "Accept": "*/*"}

        response = requests.head(
            url, timeout=TIMEOUT_SECONDS, allow_redirects=True, headers=headers
        )
        end_time = datetime.datetime.now()

        response_time = (end_time - start_time).total_seconds()
        is_available = response.status_code < 400

        if not is_available:
            logger.debug(f"Source {source_id} returned HTTP {response.status_code}")

        return {
            "available": is_available,
            "status_code": response.status_code,
            "response_time": response_time,
        }

    except requests.exceptions.Timeout:
        logger.warning(
            f"Timeout checking health for {source_id} ({url}) after {TIMEOUT_SECONDS}s"
        )
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": f"Timeout after {TIMEOUT_SECONDS}s",
        }
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Connection error checking health for {source_id} ({url}): {e}")
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": f"Connection error: {str(e)}",
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error checking health for {source_id} ({url}): {e}")
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": f"Request error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Unexpected error checking health for {source_id} ({url}): {e}")
        return {
            "available": False,
            "status_code": None,
            "response_time": None,
            "error_message": f"Unexpected error: {str(e)}",
        }


def update_source_metadata(
    source: Dict[str, Any], health: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update the source metadata with health check results and current timestamp.

    Args:
        source: Original source metadata dictionary.
        health: Health check results dictionary.

    Returns:
        Updated source metadata dictionary.

    Raises:
        MetadataUpdateError: If source or health data is invalid.
    """
    if not isinstance(source, dict):
        raise MetadataUpdateError(
            f"Invalid source data: expected dict, got {type(source)}"
        )

    if not isinstance(health, dict):
        raise MetadataUpdateError(
            f"Invalid health data: expected dict, got {type(health)}"
        )

    if "available" not in health:
        raise MetadataUpdateError("Health data missing required 'available' field")

    source_id = source.get("id", "unknown")
    updated_source = source.copy()

    try:
        # Update last_updated timestamp only if the fetch was successful or if it's missing
        if health["available"] or not updated_source.get("last_updated"):
            timestamp = (
                datetime.datetime.now(datetime.timezone.utc).isoformat(
                    timespec="seconds"
                )
                + "Z"
            )
            updated_source["last_updated"] = timestamp
            logger.debug(f"Updated timestamp for source {source_id}")

        # Update availability score based on health check
        current_availability = updated_source.get("availability")

        if health["available"]:
            # For successful health checks, we could optionally improve the score
            # For now, we only decrement on failure to be conservative
            logger.debug(f"Source {source_id} is available")
        else:
            # If source is unavailable, reduce the availability score
            if current_availability is None:
                # If availability was null, set it to 90 (100 - 10)
                updated_source["availability"] = 90.0
                logger.info(
                    f"Source {source_id} unavailable, setting availability to 90"
                )
            elif isinstance(current_availability, (int, float)):
                # If it's already a number, decrement it, clamping at 0
                new_availability = max(0.0, float(current_availability) - 10.0)
                updated_source["availability"] = new_availability
                logger.info(
                    f"Source {source_id} unavailable, reducing availability to {new_availability}"
                )
            else:
                logger.warning(
                    f"Source {source_id} has unexpected type for availability: "
                    f"{type(current_availability)}. Not updating score."
                )

        # Store the health check results for debugging
        if health.get("error_message"):
            logger.debug(
                f"Health check error for {source_id}: {health['error_message']}"
            )

        return updated_source

    except Exception as e:
        raise MetadataUpdateError(
            f"Failed to update metadata for source {source_id}: {e}"
        ) from e


def save_source_file(source: Dict[str, Any]) -> None:
    """
    Save the updated source metadata back to disk.

    Args:
        source: Source metadata dictionary with _file_path field.

    Raises:
        SourceFileError: If file operations fail.
    """
    source_id = source.get("id", "unknown")
    file_path = source.pop("_file_path", None)

    if not file_path:
        raise SourceFileError(f"Missing file path for source {source_id}")

    if not isinstance(file_path, str):
        raise SourceFileError(
            f"Invalid file path type for source {source_id}: expected str, got {type(file_path)}"
        )

    try:
        # Create backup of original file
        file_path_obj = Path(file_path)
        backup_path = None
        if file_path_obj.exists():
            backup_path = file_path_obj.with_suffix(f".backup{file_path_obj.suffix}")
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")

        # Write updated source data
        with open(file_path, "w", encoding="utf-8") as f:
            # Use indent=2 for readability, ensure_ascii=False for potential non-ASCII chars
            json.dump(source, f, indent=2, ensure_ascii=False, sort_keys=True)
            # Add a newline at the end of the file for consistency
            f.write("\n")

        logger.debug(f"Saved updated metadata to {file_path}")

        # Remove backup if write was successful
        if backup_path and Path(backup_path).exists():
            Path(backup_path).unlink()

    except (IOError, OSError) as e:
        raise SourceFileError(f"Failed to write file {file_path}: {e}") from e
    except json.JSONEncodeError as e:
        raise SourceFileError(f"Failed to encode JSON for {file_path}: {e}") from e
    except Exception as e:
        raise SourceFileError(f"Unexpected error saving {file_path}: {e}") from e


def main() -> int:
    """
    Main entry point for fetching and updating sources.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    try:
        logger.info("Starting source fetching and updating process")
        sources = load_source_files()

        if not sources:
            logger.warning("No sources loaded. Exiting.")
            return 0

        processed_count = 0
        skipped_count = 0
        error_count = 0

        for source in sources:
            source_id = source.get("id", "unknown")

            try:
                logger.info(f"Processing source: {source_id}")

                # Skip sources with quality_score of 0 (deprecated)
                quality_score = source.get("quality_score", 0)
                if quality_score == 0:
                    logger.info(
                        f"Skipping deprecated source {source_id} (quality_score=0)"
                    )
                    skipped_count += 1
                    continue

                # Fetch health data
                health = fetch_source_health(source)

                # Update metadata
                updated_source = update_source_metadata(source, health)

                # Save updated metadata
                save_source_file(updated_source)

                processed_count += 1
                logger.debug(f"Successfully processed source {source_id}")

            except (HealthCheckError, MetadataUpdateError, SourceFileError) as e:
                logger.error(f"Error processing source {source_id}: {e}")
                error_count += 1
            except Exception as e:
                logger.error(f"Unexpected error processing source {source_id}: {e}")
                error_count += 1

        # Log summary
        logger.info(
            f"Source processing completed. "
            f"Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}"
        )

        # Return appropriate exit code
        if error_count > 0:
            logger.warning(f"Completed with {error_count} errors")
            return 1

        logger.info("All sources processed successfully")
        return 0

    except SourceFileError as e:
        logger.error(f"Source file error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
