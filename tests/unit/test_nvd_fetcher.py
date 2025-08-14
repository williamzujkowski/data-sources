"""Tests for NVD fetcher."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tools.sources.nvd_fetcher import CVEData, NVDFetcher


class TestNVDFetcher:
    """Test NVD fetcher functionality."""

    @pytest.fixture
    def fetcher(self, tmp_path):
        """Create NVD fetcher instance."""
        fetcher = NVDFetcher()
        fetcher.STATE_FILE = str(tmp_path / "nvd_state.json")
        return fetcher

    @pytest.fixture
    def mock_cve_response(self):
        """Mock NVD API response."""
        return {
            "resultsPerPage": 1,
            "startIndex": 0,
            "totalResults": 1,
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1234",
                        "published": "2024-01-15T10:00:00.000",
                        "lastModified": "2024-01-16T12:00:00.000",
                        "descriptions": [
                            {
                                "lang": "en",
                                "value": "Test vulnerability description",
                            }
                        ],
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {
                                        "baseScore": 7.5,
                                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                                    }
                                }
                            ]
                        },
                        "weaknesses": [
                            {"description": [{"lang": "en", "value": "CWE-79"}]}
                        ],
                        "configurations": [
                            {
                                "nodes": [
                                    {
                                        "cpeMatch": [
                                            {
                                                "vulnerable": True,
                                                "criteria": "cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*",
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                        "references": [
                            {
                                "url": "https://example.com/advisory",
                                "source": "vendor",
                            }
                        ],
                    }
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_fetch_recent(self, fetcher, mock_cve_response):
        """Test fetching recent CVEs."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_cve_response)
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            cves = await fetcher.fetch_recent(days=7)

            assert len(cves) == 1
            assert cves[0].cve_id == "CVE-2024-1234"
            assert cves[0].cvss_v3_score == 7.5
            assert "CWE-79" in cves[0].cwe_ids

    @pytest.mark.asyncio
    async def test_incremental_fetch_first_sync(self, fetcher, mock_cve_response):
        """Test incremental fetching for first sync."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_cve_response)
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            cves = await fetcher.fetch_incremental()

            assert len(cves) == 1
            assert fetcher.sync_state["total_processed"] == 1
            assert fetcher.sync_state["last_sync"] is not None

    @pytest.mark.asyncio
    async def test_incremental_fetch_subsequent_sync(
        self, fetcher, mock_cve_response, tmp_path
    ):
        """Test incremental fetching for subsequent sync."""
        # Set up state file with previous sync
        fetcher.sync_state = {
            "last_sync": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "total_processed": 100,
        }
        fetcher._save_sync_state()

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_cve_response)
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            cves = await fetcher.fetch_incremental()

            assert len(cves) == 1
            assert fetcher.sync_state["total_processed"] == 101

    @pytest.mark.asyncio
    async def test_rate_limiting(self, fetcher):
        """Test rate limiting enforcement."""
        fetcher.RATE_LIMIT_DELAY = 0.1  # Short delay for testing

        start_time = asyncio.get_event_loop().time()
        await fetcher._rate_limit()
        await fetcher._rate_limit()
        elapsed = asyncio.get_event_loop().time() - start_time

        assert elapsed >= 0.1  # Should have delayed

    def test_parse_cve(self, fetcher, mock_cve_response):
        """Test CVE parsing."""
        vuln_data = mock_cve_response["vulnerabilities"][0]
        cve = fetcher._parse_cve(vuln_data)

        assert isinstance(cve, CVEData)
        assert cve.cve_id == "CVE-2024-1234"
        assert cve.description == "Test vulnerability description"
        assert cve.cvss_v3_score == 7.5
        assert cve.vendor == "vendor"
        assert cve.product == "product"

    def test_extract_cvss_scores(self, fetcher):
        """Test CVSS score extraction."""
        metrics = {
            "cvssMetricV31": [
                {
                    "cvssData": {
                        "baseScore": 9.8,
                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    }
                }
            ],
            "cvssMetricV2": [
                {
                    "cvssData": {
                        "baseScore": 10.0,
                        "vectorString": "AV:N/AC:L/Au:N/C:C/I:C/A:C",
                    }
                }
            ],
        }

        v3_data = fetcher._extract_cvss_v3(metrics)
        v2_data = fetcher._extract_cvss_v2(metrics)

        assert v3_data["score"] == 9.8
        assert v2_data["score"] == 10.0

    def test_extract_cwe_ids(self, fetcher):
        """Test CWE ID extraction."""
        weaknesses = [
            {
                "description": [
                    {"lang": "en", "value": "CWE-79"},
                    {"lang": "en", "value": "CWE-89"},
                ]
            }
        ]

        cwe_ids = fetcher._extract_cwe_ids(weaknesses)

        assert "CWE-79" in cwe_ids
        assert "CWE-89" in cwe_ids

    def test_extract_vendor_product(self, fetcher):
        """Test vendor/product extraction from CPE."""
        cpe_matches = [
            {
                "cpe": "cpe:2.3:a:microsoft:edge:1.0:*:*:*:*:*:*:*",
                "version_start": "1.0",
                "version_end": "2.0",
            }
        ]

        vendor, product = fetcher._extract_vendor_product(cpe_matches)

        assert vendor == "microsoft"
        assert product == "edge"

    def test_state_persistence(self, fetcher, tmp_path):
        """Test state persistence to disk."""
        fetcher.sync_state = {
            "last_sync": datetime.utcnow().isoformat(),
            "total_processed": 500,
        }
        fetcher._save_sync_state()

        # Load state in new instance
        new_fetcher = NVDFetcher()
        new_fetcher.STATE_FILE = fetcher.STATE_FILE
        loaded_state = new_fetcher._load_sync_state()

        assert loaded_state["total_processed"] == 500
        assert loaded_state["last_sync"] is not None

    @pytest.mark.asyncio
    async def test_context_manager(self, fetcher):
        """Test async context manager functionality."""
        async with fetcher as f:
            assert f.session is not None
            assert f == fetcher
        assert fetcher.session is None  # Should be closed
