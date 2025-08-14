"""Unit tests for score_sources.py module."""

import datetime
import json
import os
import sys
from unittest.mock import mock_open, patch

import pytest

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

import score_sources


class TestLoadScoringConfig:
    """Test the load_scoring_config function."""

    @patch("builtins.open", new_callable=mock_open)
    def test_load_scoring_config_success(self, mock_file, scoring_config):
        """Test successful loading of scoring configuration."""
        mock_file.return_value.read.return_value = json.dumps(scoring_config)

        result = score_sources.load_scoring_config()

        assert result == scoring_config
        assert result["weights"]["freshness"] == 0.4

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_scoring_config_file_not_found(self, mock_file):
        """Test fallback to default config when file not found."""
        with patch("score_sources.logger") as mock_logger:
            result = score_sources.load_scoring_config()

            assert "weights" in result
            assert result["weights"]["freshness"] == 0.4
            mock_logger.error.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_load_scoring_config_invalid_json(self, mock_file):
        """Test fallback to default config when JSON is invalid."""
        mock_file.return_value.read.return_value = "invalid json"

        with patch("score_sources.logger") as mock_logger:
            result = score_sources.load_scoring_config()

            assert "weights" in result
            mock_logger.error.assert_called()


class TestCalculateFreshnessScore:
    """Test the calculate_freshness_score function."""

    def test_calculate_freshness_score_no_date(self):
        """Test freshness score with no last updated date."""
        result = score_sources.calculate_freshness_score(None)
        assert result == 0

        result = score_sources.calculate_freshness_score("")
        assert result == 0

    def test_calculate_freshness_score_recent_update(self):
        """Test freshness score with recent update."""
        # Mock current time to be consistent
        with patch("score_sources.datetime") as mock_datetime:
            mock_now = datetime.datetime(
                2025, 8, 14, 12, 0, 0, tzinfo=datetime.timezone.utc
            )
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.fromisoformat = datetime.datetime.fromisoformat
            mock_datetime.timezone = datetime.timezone

            # Test with today's date
            today_iso = "2025-08-14T11:00:00+00:00"
            result = score_sources.calculate_freshness_score(today_iso)
            assert result == 100.0

    def test_calculate_freshness_score_old_update(self):
        """Test freshness score with old update."""
        with patch("score_sources.datetime") as mock_datetime:
            mock_now = datetime.datetime(
                2025, 8, 14, 12, 0, 0, tzinfo=datetime.timezone.utc
            )
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.fromisoformat = datetime.datetime.fromisoformat
            mock_datetime.timezone = datetime.timezone

            # Test with 60+ days old (should be 0)
            old_iso = "2025-06-10T11:00:00+00:00"
            result = score_sources.calculate_freshness_score(old_iso)
            assert result == 0.0

    def test_calculate_freshness_score_z_format(self):
        """Test freshness score with Z timezone format."""
        with patch("score_sources.datetime") as mock_datetime:
            mock_now = datetime.datetime(
                2025, 8, 14, 12, 0, 0, tzinfo=datetime.timezone.utc
            )
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.datetime.fromisoformat = datetime.datetime.fromisoformat
            mock_datetime.timezone = datetime.timezone

            # Test with Z format
            z_format_iso = "2025-08-14T11:00:00Z"
            result = score_sources.calculate_freshness_score(z_format_iso)
            assert result == 100.0

    def test_calculate_freshness_score_invalid_format(self):
        """Test freshness score with invalid date format."""
        with patch("score_sources.logger") as mock_logger:
            result = score_sources.calculate_freshness_score("invalid date")

            assert result == 0
            mock_logger.error.assert_called()


class TestCalculateQualityScore:
    """Test the calculate_quality_score function."""

    def test_calculate_quality_score_all_values_present(
        self, sample_source, scoring_config
    ):
        """Test quality score calculation with all values present."""
        weights = scoring_config["weights"]

        with patch("score_sources.calculate_freshness_score", return_value=95.0):
            result = score_sources.calculate_quality_score(sample_source, weights)

            # Expected: 95*0.4 + 90*0.3 + 80*0.2 + 95*0.1 = 38 + 27 + 16 + 9.5 = 90.5
            assert result == 90.5

    def test_calculate_quality_score_missing_values(self, scoring_config):
        """Test quality score calculation with missing values."""
        source = {
            "id": "test",
            "authority": None,
            "coverage": None,
            "availability": None,
        }
        weights = scoring_config["weights"]

        with patch("score_sources.calculate_freshness_score", return_value=0.0):
            result = score_sources.calculate_quality_score(source, weights)

            # Expected: 0*0.4 + 50*0.3 + 50*0.2 + 50*0.1 = 0 + 15 + 10 + 5 = 30.0
            assert result == 30.0

    def test_calculate_quality_score_custom_weights(self, sample_source):
        """Test quality score calculation with custom weights."""
        custom_weights = {
            "freshness": 0.5,
            "authority": 0.5,
            "coverage": 0.0,
            "availability": 0.0,
        }

        with patch("score_sources.calculate_freshness_score", return_value=80.0):
            result = score_sources.calculate_quality_score(
                sample_source, custom_weights
            )

            # Expected: 80*0.5 + 90*0.5 + 80*0.0 + 95*0.0 = 40 + 45 + 0 + 0 = 85.0
            assert result == 85.0


class TestCalculateUserWeightedScore:
    """Test the calculate_user_weighted_score function."""

    def test_calculate_user_weighted_score_no_user_weights(
        self, sample_source, scoring_config
    ):
        """Test user weighted score with no user weights."""
        weights = scoring_config["weights"]

        result = score_sources.calculate_user_weighted_score(
            sample_source, weights, None
        )

        assert result == sample_source["quality_score"]

    def test_calculate_user_weighted_score_missing_quality_score(self, scoring_config):
        """Test user weighted score when quality_score is missing."""
        source = {
            "id": "test",
            "quality_score": None,
            "authority": 90,
            "coverage": 80,
            "availability": 95,
        }
        weights = scoring_config["weights"]

        with patch("score_sources.calculate_freshness_score", return_value=85.0):
            result = score_sources.calculate_user_weighted_score(source, weights, None)

            # Should calculate using default weights
            assert isinstance(result, float)
            assert result > 0

    def test_calculate_user_weighted_score_with_user_weights(
        self, sample_source, scoring_config
    ):
        """Test user weighted score with custom user weights."""
        weights = scoring_config["weights"]
        user_weights = {
            "freshness": 0.6,
            "authority": 0.4,
            "coverage": 0.0,
            "availability": 0.0,
        }

        with patch("score_sources.calculate_freshness_score", return_value=90.0):
            result = score_sources.calculate_user_weighted_score(
                sample_source, weights, user_weights
            )

            # Expected: 90*0.6 + 90*0.4 + 80*0.0 + 95*0.0 = 54 + 36 + 0 + 0 = 90.0
            assert result == 90.0


class TestLoadSourceFiles:
    """Test the load_source_files function in score_sources."""

    @patch("score_sources.glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_source_files_success(self, mock_file, mock_glob, sample_source):
        """Test successful loading of source files."""
        mock_glob.return_value = ["/path/to/test.json"]
        mock_file.return_value.read.return_value = json.dumps(sample_source)

        result = score_sources.load_source_files()

        assert len(result) == 1
        assert result[0]["id"] == "test-source"


class TestSaveSourceFile:
    """Test the save_source_file function in score_sources."""

    @patch("builtins.open", new_callable=mock_open)
    def test_save_source_file_success(self, mock_file, sample_source):
        """Test successful file saving."""
        sample_source["_file_path"] = "/path/to/test.json"

        score_sources.save_source_file(sample_source)

        mock_file.assert_called_once_with("/path/to/test.json", "w")


class TestMain:
    """Test the main function in score_sources."""

    @patch("score_sources.save_source_file")
    @patch("score_sources.calculate_user_weighted_score")
    @patch("score_sources.calculate_quality_score")
    @patch("score_sources.load_source_files")
    @patch("score_sources.load_scoring_config")
    def test_main_process_sources(
        self,
        mock_load_config,
        mock_load_sources,
        mock_calc_quality,
        mock_calc_user,
        mock_save,
        sample_source,
        scoring_config,
    ):
        """Test main function processing sources."""
        mock_load_config.return_value = scoring_config
        mock_load_sources.return_value = [sample_source]
        mock_calc_quality.return_value = 85.5
        mock_calc_user.return_value = 85.5

        score_sources.main()

        mock_calc_quality.assert_called_once()
        mock_calc_user.assert_called_once()
        mock_save.assert_called_once()


@pytest.mark.integration
class TestScoreSourcesIntegration:
    """Integration tests for score_sources module."""

    def test_score_calculation_workflow(self, temp_source_file, temp_config_dir):
        """Test the complete scoring workflow."""
        with patch("score_sources.DATA_SOURCES_DIR"), patch(
            "score_sources.CONFIG_DIR", temp_config_dir
        ), patch("score_sources.glob.glob") as mock_glob:

            mock_glob.return_value = [temp_source_file]

            # This should run without errors
            score_sources.main()


# Property-based testing with Hypothesis
pytest.importorskip("hypothesis")
from hypothesis import given
from hypothesis import strategies as st


class TestScoringProperties:
    """Property-based tests for scoring functions."""

    @given(st.floats(min_value=0, max_value=100))
    def test_quality_score_bounds(self, score_value):
        """Test that quality scores are always within bounds."""
        source = {
            "authority": score_value,
            "coverage": score_value,
            "availability": score_value,
        }
        weights = {
            "freshness": 0.25,
            "authority": 0.25,
            "coverage": 0.25,
            "availability": 0.25,
        }

        with patch("score_sources.calculate_freshness_score", return_value=score_value):
            result = score_sources.calculate_quality_score(source, weights)

            assert 0 <= result <= 100

    @given(st.floats(min_value=0, max_value=1, allow_nan=False))
    def test_weights_normalization(self, weight1):
        """Test that weights can be normalized properly."""
        weight2 = 1 - weight1
        weights = {
            "freshness": weight1,
            "authority": weight2,
            "coverage": 0,
            "availability": 0,
        }

        source = {"authority": 100, "coverage": 100, "availability": 100}

        with patch("score_sources.calculate_freshness_score", return_value=100):
            result = score_sources.calculate_quality_score(source, weights)

            assert result == 100.0  # All perfect scores should yield 100
