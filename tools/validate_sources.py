#!/usr/bin/env python3
"""
Validate all source files against schema.
"""

import glob
import json
from pathlib import Path

import jsonschema


def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema from file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_source_file(
    file_path: str, validator: jsonschema.protocols.Validator
) -> bool:
    """Validate a single source file against the schema."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        validator.validate(data)
        print(f"{file_path} is valid")
        return True
    except Exception as e:
        print(f"{file_path} is INVALID: {e}")
        return False


def main() -> int:
    """Main validation function."""
    # Get project root
    root_dir = Path(__file__).parent.parent
    schema_path = root_dir / "schemas" / "source.schema.json"
    sources_pattern = str(root_dir / "data-sources" / "**" / "*.json")

    # Load schema
    schema = load_schema(schema_path)

    # Create validator
    validator = jsonschema.Draft7Validator(schema)

    # Validate all source files
    all_valid = True
    for file_path in glob.glob(sources_pattern, recursive=True):
        if not validate_source_file(file_path, validator):
            all_valid = False

    # Print overall status
    if all_valid:
        print("\nValidation succeeded! All source files conform to schema.")
        return 0
    else:
        print("\nValidation failed! Some source files do not conform to schema.")
        return 1


if __name__ == "__main__":
    exit(main())
