"""pytest configuration and fixtures for data-sources tests."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def sample_source() -> Dict[str, Any]:
    """Return a sample source data structure for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "sample_source.json") as f:
        return json.load(f)


@pytest.fixture
def temp_source_file(sample_source: Dict[str, Any]):
    """Create a temporary source file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_source, f, indent=2)
        f.flush()
        yield f.name
    # Cleanup is handled by tempfile


@pytest.fixture
def mock_requests_response():
    """Mock requests response for HTTP testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {"status": "ok"}
    return mock_response


@pytest.fixture
def mock_http_success():
    """Mock successful HTTP requests."""
    with patch("requests.head") as mock_head, patch("requests.get") as mock_get:
        mock_head.return_value.status_code = 200
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        yield mock_head, mock_get


@pytest.fixture
def mock_http_failure():
    """Mock failed HTTP requests."""
    with patch("requests.head") as mock_head, patch("requests.get") as mock_get:
        mock_head.return_value.status_code = 404
        mock_get.return_value.status_code = 404
        yield mock_head, mock_get


@pytest.fixture
def scoring_config():
    """Return sample scoring configuration."""
    return {
        "weights": {
            "freshness": 0.4,
            "authority": 0.3,
            "coverage": 0.2,
            "availability": 0.1,
        }
    }


@pytest.fixture
def temp_data_sources_dir(tmp_path):
    """Create a temporary data sources directory structure."""
    data_sources_dir = tmp_path / "data-sources"
    data_sources_dir.mkdir()

    # Create subdirectories
    vuln_dir = data_sources_dir / "vulnerability" / "cve"
    vuln_dir.mkdir(parents=True)

    return data_sources_dir


@pytest.fixture
def temp_config_dir(tmp_path, scoring_config):
    """Create a temporary config directory with sample files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create scoring config
    scoring_config_file = config_dir / "scoring-config.json"
    with open(scoring_config_file, "w") as f:
        json.dump(scoring_config, f, indent=2)

    return config_dir
