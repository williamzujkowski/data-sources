"""Unit tests for fetch_sources.py module."""

import datetime
import json
import os
import sys
from unittest.mock import Mock, mock_open, patch

import pytest

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

import fetch_sources


class TestLoadSourceFiles:
    """Test the load_source_files function."""

    @patch("fetch_sources.glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_source_files_success(self, mock_file, mock_glob, sample_source):
        """Test successful loading of source files."""
        mock_glob.return_value = ["/path/to/test.json"]
        mock_file.return_value.read.return_value = json.dumps(sample_source)

        result = fetch_sources.load_source_files()

        assert len(result) == 1
        assert result[0]["id"] == "test-source"
        assert result[0]["_file_path"] == "/path/to/test.json"

    @patch("fetch_sources.glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_source_files_invalid_json(self, mock_file, mock_glob):
        """Test handling of invalid JSON files."""
        mock_glob.return_value = ["/path/to/invalid.json"]
        mock_file.return_value.read.return_value = "invalid json"

        with patch("fetch_sources.logger") as mock_logger:
            result = fetch_sources.load_source_files()

            assert len(result) == 0
            mock_logger.error.assert_called()

    @patch("fetch_sources.glob.glob")
    def test_load_source_files_no_files(self, mock_glob):
        """Test behavior when no source files are found."""
        mock_glob.return_value = []

        result = fetch_sources.load_source_files()

        assert len(result) == 0


class TestFetchSourceHealth:
    """Test the fetch_source_health function."""

    def test_fetch_source_health_no_url(self):
        """Test health check with no URL provided."""
        source = {"id": "test"}

        result = fetch_sources.fetch_source_health(source)

        assert result["available"] is False
        assert result["status_code"] is None
        assert result["response_time"] is None

    @patch("fetch_sources.requests.head")
    def test_fetch_source_health_success(self, mock_head):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        source = {"id": "test", "url": "https://example.com/api"}

        result = fetch_sources.fetch_source_health(source)

        assert result["available"] is True
        assert result["status_code"] == 200
        assert isinstance(result["response_time"], float)

    @patch("fetch_sources.requests.head")
    def test_fetch_source_health_failure(self, mock_head):
        """Test health check with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        source = {"id": "test", "url": "https://example.com/api"}

        result = fetch_sources.fetch_source_health(source)

        assert result["available"] is False
        assert result["status_code"] == 404

    @patch("fetch_sources.requests.head")
    def test_fetch_source_health_exception(self, mock_head):
        """Test health check with network exception."""
        import requests

        mock_head.side_effect = requests.RequestException("Network error")

        source = {"id": "test", "url": "https://example.com/api"}

        with patch("fetch_sources.logger") as mock_logger:
            result = fetch_sources.fetch_source_health(source)

            assert result["available"] is False
            assert result["status_code"] is None
            mock_logger.warning.assert_called()


class TestUpdateSourceMetadata:
    """Test the update_source_metadata function."""

    def test_update_source_metadata_success(self, sample_source):
        """Test metadata update with successful health check."""
        health = {"available": True, "status_code": 200, "response_time": 0.5}

        with patch("fetch_sources.datetime") as mock_datetime:
            mock_now = datetime.datetime(
                2025, 8, 14, 12, 0, 0, tzinfo=datetime.timezone.utc
            )
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.timezone = datetime.timezone

            result = fetch_sources.update_source_metadata(sample_source, health)

            assert "last_updated" in result
            assert result["last_updated"] == "2025-08-14T12:00:00+00:00Z"

    def test_update_source_metadata_failure_new_source(self, sample_source):
        """Test metadata update with failed health check on new source."""
        sample_source.pop("availability", None)
        health = {"available": False, "status_code": 404, "response_time": None}

        result = fetch_sources.update_source_metadata(sample_source, health)

        assert result["availability"] == 90.0

    def test_update_source_metadata_failure_existing_source(self, sample_source):
        """Test metadata update with failed health check on existing source."""
        sample_source["availability"] = 100.0
        health = {"available": False, "status_code": 503, "response_time": None}

        result = fetch_sources.update_source_metadata(sample_source, health)

        assert result["availability"] == 90.0

    def test_update_source_metadata_preserves_last_updated_on_failure(
        self, sample_source
    ):
        """Test that last_updated is preserved when health check fails."""
        original_time = sample_source["last_updated"]
        health = {"available": False, "status_code": 404, "response_time": None}

        result = fetch_sources.update_source_metadata(sample_source, health)

        assert result["last_updated"] == original_time


class TestSaveSourceFile:
    """Test the save_source_file function."""

    @patch("builtins.open", new_callable=mock_open)
    def test_save_source_file_success(self, mock_file, sample_source):
        """Test successful file saving."""
        sample_source["_file_path"] = "/path/to/test.json"

        fetch_sources.save_source_file(sample_source)

        mock_file.assert_called_once_with("/path/to/test.json", "w", encoding="utf-8")
        handle = mock_file()
        # Verify JSON was written
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "test-source" in written_content

    def test_save_source_file_missing_path(self, sample_source):
        """Test error handling when file path is missing."""
        # Remove _file_path
        sample_source.pop("_file_path", None)

        with pytest.raises(fetch_sources.SourceFileError, match="Missing file path"):
            fetch_sources.save_source_file(sample_source)

    @patch("builtins.open", side_effect=OSError("Write failed"))
    def test_save_source_file_write_error(self, mock_file, sample_source):
        """Test error handling when file write fails."""
        sample_source["_file_path"] = "/path/to/test.json"

        with pytest.raises(fetch_sources.SourceFileError, match="Failed to write file"):
            fetch_sources.save_source_file(sample_source)


class TestMain:
    """Test the main function."""

    @patch("fetch_sources.save_source_file")
    @patch("fetch_sources.update_source_metadata")
    @patch("fetch_sources.fetch_source_health")
    @patch("fetch_sources.load_source_files")
    def test_main_skip_deprecated_sources(
        self, mock_load, mock_health, mock_update, mock_save, sample_source
    ):
        """Test that deprecated sources (quality_score=0) are skipped."""
        deprecated_source = sample_source.copy()
        deprecated_source["quality_score"] = 0

        mock_load.return_value = [deprecated_source]

        with patch("fetch_sources.logger") as mock_logger:
            fetch_sources.main()

            mock_health.assert_not_called()
            mock_update.assert_not_called()
            mock_save.assert_not_called()
            mock_logger.info.assert_any_call(
                "Skipping deprecated source test-source (quality_score=0)"
            )

    @patch("fetch_sources.save_source_file")
    @patch("fetch_sources.update_source_metadata")
    @patch("fetch_sources.fetch_source_health")
    @patch("fetch_sources.load_source_files")
    def test_main_process_valid_sources(
        self, mock_load, mock_health, mock_update, mock_save, sample_source
    ):
        """Test processing of valid sources."""
        mock_load.return_value = [sample_source]
        mock_health.return_value = {"available": True, "status_code": 200}
        mock_update.return_value = sample_source

        fetch_sources.main()

        mock_health.assert_called_once_with(sample_source)
        mock_update.assert_called_once()
        mock_save.assert_called_once()


@pytest.mark.integration
class TestFetchSourcesIntegration:
    """Integration tests for fetch_sources module."""

    def test_full_workflow_with_temp_files(self, temp_source_file, mock_http_success):
        """Test the complete workflow with actual file I/O."""
        # Patch the DATA_SOURCES_DIR to use our temp file
        with patch("fetch_sources.DATA_SOURCES_DIR"), patch(
            "fetch_sources.glob.glob"
        ) as mock_glob:

            mock_glob.return_value = [temp_source_file]

            # Run the main function
            fetch_sources.main()

            # Verify the file was processed (HTTP request was made)
            mock_http_success[0].assert_called()  # requests.head was called
