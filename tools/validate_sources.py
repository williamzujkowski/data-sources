#!/usr/bin/env python3
"""
Validate all source files against schema.
"""

import json
import jsonschema
import glob
from pathlib import Path

# Get project root
root_dir = Path(__file__).parent.parent
schema_path = root_dir / "schemas" / "source.schema.json"
sources_pattern = str(root_dir / "data-sources" / "**" / "*.json")

# Load schema
with open(schema_path, "r") as f:
    schema = json.load(f)

# Create validator
validator = jsonschema.Draft7Validator(schema)

# Validate all source files
all_valid = True
for file_path in glob.glob(sources_pattern, recursive=True):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        validator.validate(data)
        print(f"{file_path} is valid")
    except Exception as e:
        print(f"{file_path} is INVALID: {e}")
        all_valid = False

# Print overall status
if all_valid:
    print("\nValidation succeeded! All source files conform to schema.")
    exit(0)
else:
    print("\nValidation failed! Some source files do not conform to schema.")
    exit(1)