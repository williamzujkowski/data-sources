#!/usr/bin/env python3
"""
Migrate existing source files to include new optional fields from the updated schema.
Adds 'freshness', 'authority', 'coverage', 'availability', 'update_frequency', 
'api_details', and 'data_format_sample' with null values if they are missing.
"""

import json
import glob
import os
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("migrate_source_schema")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
SOURCES_PATTERN = str(DATA_SOURCES_DIR / "**" / "*.json")

# Fields to ensure exist (with null default)
OPTIONAL_FIELDS = [
    "freshness",
    "authority",
    "coverage",
    "availability",
    "update_frequency",
    "api_details",
    "data_format_sample",
    "user_weighted_score" # Also ensure this nullable field exists
]

def migrate_file(file_path: str) -> bool:
    """Loads a source file, adds missing optional fields, and saves it."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse {file_path} as JSON. Skipping.")
        return False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}. Skipping.")
        return False

    updated = False
    for field in OPTIONAL_FIELDS:
        if field not in data:
            data[field] = None
            updated = True
            logger.debug(f"Added missing field '{field}' to {file_path}")

    if updated:
        try:
            with open(file_path, "w") as f:
                # Use indent=2 for readability, ensure_ascii=False for potential non-ASCII chars
                json.dump(data, f, indent=2, ensure_ascii=False) 
                # Add a newline at the end of the file for consistency
                f.write("\n") 
            logger.info(f"Updated {file_path} with missing optional fields.")
            return True
        except Exception as e:
            logger.error(f"Failed to write updated data to {file_path}: {e}")
            return False
    else:
        logger.debug(f"No updates needed for {file_path}")
        return True # No update needed, but file is compliant

def main() -> None:
    """Main migration process."""
    logger.info("Starting migration of source files...")
    all_files = glob.glob(SOURCES_PATTERN, recursive=True)
    logger.info(f"Found {len(all_files)} potential source files.")
    
    processed_count = 0
    updated_count = 0 # Not currently tracking which files were *actually* changed vs just processed
    failed_count = 0

    for file_path in all_files:
        # Skip schema files or other non-source json files if necessary
        # Check if the file is directly inside a directory named 'schemas' or 'config'
        path_obj = Path(file_path)
        if path_obj.parent.name in ["schemas", "config"]:
             logger.debug(f"Skipping non-source file: {file_path}")
             continue
             
        processed_count += 1
        if migrate_file(file_path):
             pass # Handled within migrate_file logging
        else:
             failed_count += 1

    logger.info(f"Migration finished. Processed: {processed_count}, Failed: {failed_count}.")
    if failed_count > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Migrate existing source files to include new optional fields from the updated schema.
Adds 'freshness', 'authority', 'coverage', 'availability', 'update_frequency', 
'api_details', and 'data_format_sample' with null values if they are missing.
"""

import json
import glob
import os
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("migrate_source_schema")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
SOURCES_PATTERN = str(DATA_SOURCES_DIR / "**" / "*.json")

# Fields to ensure exist (with null default)
OPTIONAL_FIELDS = [
    "freshness",
    "authority",
    "coverage",
    "availability",
    "update_frequency",
    "api_details",
    "data_format_sample",
    "user_weighted_score" # Also ensure this nullable field exists
]

def migrate_file(file_path: str) -> bool:
    """Loads a source file, adds missing optional fields, and saves it."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse {file_path} as JSON. Skipping.")
        return False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}. Skipping.")
        return False

    updated = False
    for field in OPTIONAL_FIELDS:
        if field not in data:
            data[field] = None
            updated = True
            logger.debug(f"Added missing field '{field}' to {file_path}")

    if updated:
        try:
            with open(file_path, "w") as f:
                # Use indent=2 for readability, ensure_ascii=False for potential non-ASCII chars
                json.dump(data, f, indent=2, ensure_ascii=False) 
                # Add a newline at the end of the file for consistency
                f.write("\n") 
            logger.info(f"Updated {file_path} with missing optional fields.")
            return True
        except Exception as e:
            logger.error(f"Failed to write updated data to {file_path}: {e}")
            return False
    else:
        logger.debug(f"No updates needed for {file_path}")
        return True # No update needed, but file is compliant

def main() -> None:
    """Main migration process."""
    logger.info("Starting migration of source files...")
    all_files = glob.glob(SOURCES_PATTERN, recursive=True)
    logger.info(f"Found {len(all_files)} potential source files.")
    
    processed_count = 0
    updated_count = 0 # Not currently tracking which files were *actually* changed vs just processed
    failed_count = 0

    for file_path in all_files:
        # Skip schema files or other non-source json files if necessary
        # Check if the file is directly inside a directory named 'schemas' or 'config'
        path_obj = Path(file_path)
        if path_obj.parent.name in ["schemas", "config"]:
             logger.debug(f"Skipping non-source file: {file_path}")
             continue
             
        processed_count += 1
        if migrate_file(file_path):
             pass # Handled within migrate_file logging
        else:
             failed_count += 1

    logger.info(f"Migration finished. Processed: {processed_count}, Failed: {failed_count}.")
    if failed_count > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Migrate existing source files to include new optional fields from the updated schema.
Adds 'freshness', 'authority', 'coverage', 'availability', 'update_frequency', 
'api_details', and 'data_format_sample' with null values if they are missing.
"""

import json
import glob
import os
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("migrate_source_schema")

# Constants
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SOURCES_DIR = ROOT_DIR / "data-sources"
SOURCES_PATTERN = str(DATA_SOURCES_DIR / "**" / "*.json")

# Fields to ensure exist (with null default)
OPTIONAL_FIELDS = [
    "freshness",
    "authority",
    "coverage",
    "availability",
    "update_frequency",
    "api_details",
    "data_format_sample",
    "user_weighted_score" # Also ensure this nullable field exists
]

def migrate_file(file_path: str) -> bool:
    """Loads a source file, adds missing optional fields, and saves it."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse {file_path} as JSON. Skipping.")
        return False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}. Skipping.")
        return False

    updated = False
    for field in OPTIONAL_FIELDS:
        if field not in data:
            data[field] = None
            updated = True
            logger.debug(f"Added missing field '{field}' to {file_path}")

    if updated:
        try:
            with open(file_path, "w") as f:
                # Use indent=2 for readability, ensure_ascii=False for potential non-ASCII chars
                json.dump(data, f, indent=2, ensure_ascii=False) 
                # Add a newline at the end of the file for consistency
                f.write("\n") 
            logger.info(f"Updated {file_path} with missing optional fields.")
            return True
        except Exception as e:
            logger.error(f"Failed to write updated data to {file_path}: {e}")
            return False
    else:
        logger.debug(f"No updates needed for {file_path}")
        return True # No update needed, but file is compliant

def main() -> None:
    """Main migration process."""
    logger.info("Starting migration of source files...")
    all_files = glob.glob(SOURCES_PATTERN, recursive=True)
    logger.info(f"Found {len(all_files)} potential source files.")
    
    processed_count = 0
    updated_count = 0 # Not currently tracking which files were *actually* changed vs just processed
    failed_count = 0

    for file_path in all_files:
        # Skip schema files or other non-source json files if necessary
        # Check if the file is directly inside a directory named 'schemas' or 'config'
        path_obj = Path(file_path)
        if path_obj.parent.name in ["schemas", "config"]:
             logger.debug(f"Skipping non-source file: {file_path}")
             continue
             
        processed_count += 1
        if migrate_file(file_path):
             pass # Handled within migrate_file logging
        else:
             failed_count += 1

    logger.info(f"Migration finished. Processed: {processed_count}, Failed: {failed_count}.")
    if failed_count > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
