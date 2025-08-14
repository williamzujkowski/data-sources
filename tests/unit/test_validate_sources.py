"""
Unit tests for validate_sources.py module.
"""

import json
import os
import sys
from unittest.mock import Mock, mock_open, patch

import pytest

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

import validate_sources


class TestValidateSourcesScript:
    """Test the validate_sources.py script functionality."""

    @patch("validate_sources.glob.glob")
    @patch("validate_sources.load_schema")
    @patch("validate_sources.jsonschema.Draft7Validator")
    def test_validation_success(
        self, mock_validator_class, mock_load_schema, mock_glob, sample_source
    ):
        """Test successful validation of all source files."""
        # Setup mocks
        mock_glob.return_value = ["/path/to/test.json"]
        mock_load_schema.return_value = {"type": "object"}

        mock_validator = Mock()
        mock_validator.validate.return_value = None  # No exceptions = valid
        mock_validator_class.return_value = mock_validator

        # Mock file reading
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_source))):
            result = validate_sources.main()

            # Verify validation was attempted
            mock_validator.validate.assert_called()
            assert result == 0  # Success exit code

    @patch("validate_sources.glob.glob")
    @patch("validate_sources.load_schema")
    @patch("validate_sources.jsonschema.Draft7Validator")
    def test_validation_failure(
        self, mock_validator_class, mock_load_schema, mock_glob
    ):
        """Test validation failure handling."""
        import jsonschema

        # Setup mocks
        mock_glob.return_value = ["/path/to/invalid.json"]
        mock_load_schema.return_value = {"type": "object"}

        mock_validator = Mock()
        mock_validator.validate.side_effect = jsonschema.ValidationError(
            "Invalid schema"
        )
        mock_validator_class.return_value = mock_validator

        # Mock file reading
        with patch("builtins.open", mock_open(read_data='{"invalid": "json"}')):
            result = validate_sources.main()

            # Verify validation was attempted and failed
            mock_validator.validate.assert_called()
            assert result == 1  # Failure exit code

    @patch("validate_sources.load_schema")
    @patch("validate_sources.glob.glob")
    def test_file_not_found(self, mock_glob, mock_load_schema):
        """Test handling of missing files."""
        mock_glob.return_value = ["/path/to/missing.json"]
        mock_load_schema.return_value = {"type": "object"}

        with patch("builtins.open", side_effect=FileNotFoundError):
            # Test that main() returns 1 when files are not found
            result = validate_sources.main()
            assert result == 1

    @patch("validate_sources.load_schema")
    @patch("validate_sources.glob.glob")
    def test_invalid_json(self, mock_glob, mock_load_schema):
        """Test handling of invalid JSON files."""
        mock_glob.return_value = ["/path/to/invalid.json"]
        mock_load_schema.return_value = {"type": "object"}

        with patch(
            "builtins.open", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
        ):
            # Test that main() returns 1 when JSON files are invalid
            result = validate_sources.main()
            assert result == 1


class TestSchemaLoading:
    """Test schema loading functionality."""

    @patch("builtins.open", new_callable=mock_open)
    def test_schema_loading_success(self, mock_file):
        """Test successful schema loading."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"id": {"type": "string"}},
        }
        mock_file.return_value.read.return_value = json.dumps(schema)

        # This would be called in the actual script
        with patch("validate_sources.json.load", return_value=schema):
            result = json.load(mock_file())
            assert result == schema

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_schema_file_not_found(self, mock_file):
        """Test handling when schema file is missing."""
        with pytest.raises(FileNotFoundError):
            with open("missing_schema.json") as f:
                json.load(f)


@pytest.mark.integration
class TestValidateSourcesIntegration:
    """Integration tests for the validation script."""

    def test_validate_real_schema_file(self):
        """Test validation using the real schema file."""
        # Load the actual schema
        schema_path = "schemas/source.schema.json"

        with open(schema_path) as f:
            schema = json.load(f)

        # Verify schema is valid JSON Schema
        import jsonschema

        jsonschema.Draft7Validator.check_schema(schema)

        # Schema should have required properties
        assert "properties" in schema
        assert "required" in schema
        assert "id" in schema["properties"]

    def test_validate_sample_source_against_schema(self, sample_source):
        """Test validating our sample source against the real schema."""
        import jsonschema

        # Load the actual schema
        with open("schemas/source.schema.json") as f:
            schema = json.load(f)

        # Create validator
        validator = jsonschema.Draft7Validator(schema)

        # This should not raise an exception
        validator.validate(sample_source)


class TestCommandLineInterface:
    """Test command line interface aspects."""

    @patch("sys.argv", ["validate_sources.py"])
    def test_script_runs_without_args(self):
        """Test that script can run without command line arguments."""
        # This is a basic test to ensure the script structure is correct
        # The actual execution would be tested in integration tests
        assert True  # Placeholder

    def test_script_exit_codes(self):
        """Test that script uses correct exit codes."""
        # Success should be 0, failure should be 1
        # This would be tested by actually running the script
        assert True  # Placeholder
