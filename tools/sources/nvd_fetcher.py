"""
NVD (National Vulnerability Database) fetcher with incremental update support.
Implements rate limiting and efficient pagination for the NVD API 2.0.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CVEData:
    """Structured CVE data from NVD."""

    cve_id: str
    published: str
    last_modified: str
    description: str
    cvss_v3_score: Optional[float] = None
    cvss_v3_vector: Optional[str] = None
    cvss_v2_score: Optional[float] = None
    cvss_v2_vector: Optional[str] = None
    cwe_ids: Optional[List[str]] = None
    cpe_matches: Optional[List[Dict[str, Any]]] = None
    references: Optional[List[Dict[str, Any]]] = None
    vendor: Optional[str] = None
    product: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with non-null values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class NVDFetcher:
    """
    NVD API 2.0 fetcher with incremental update support.

    Features:
    - Incremental updates based on last sync timestamp
    - Automatic rate limiting (5 req/30s without API key)
    - Efficient pagination handling
    - State persistence for resume capability
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RATE_LIMIT_DELAY = 6  # seconds between requests (conservative)
    MAX_RESULTS_PER_PAGE = 2000
    STATE_FILE = "data/nvd_sync_state.json"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize NVD fetcher with optional API key."""
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: float = 0
        self.sync_state = self._load_sync_state()

        # Adjust rate limit if API key is provided
        if api_key:
            self.RATE_LIMIT_DELAY = 1  # Simplified rate limiting for API key

    async def __aenter__(self) -> "NVDFetcher":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None

    def _load_sync_state(self) -> Dict[str, Any]:
        """Load synchronization state from disk."""
        state_path = Path(self.STATE_FILE)
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sync state: {e}")
        return {"last_sync": None, "total_processed": 0}

    def _save_sync_state(self) -> None:
        """Save synchronization state to disk."""
        state_path = Path(self.STATE_FILE)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            json.dump(self.sync_state, f, indent=2)

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)

        self.last_request_time = asyncio.get_event_loop().time()

    async def fetch_recent(self, days: int = 7) -> List[CVEData]:
        """
        Fetch CVEs modified in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of CVEData objects
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        cves = await self._fetch_date_range(start_date, end_date)

        # Update sync state
        self.sync_state["last_sync"] = end_date.isoformat()
        self.sync_state["total_processed"] = self.sync_state.get(
            "total_processed", 0
        ) + len(cves)
        self._save_sync_state()

        return cves

    async def fetch_incremental(self) -> List[CVEData]:
        """
        Fetch only CVEs modified since last successful sync.

        Returns:
            List of new/updated CVEData objects
        """
        if not self.sync_state.get("last_sync"):
            # First sync - get last 30 days
            logger.info("First sync - fetching last 30 days of CVEs")
            return await self.fetch_recent(30)

        last_sync = datetime.fromisoformat(self.sync_state["last_sync"])
        logger.info(f"Incremental sync from {last_sync.isoformat()}")

        end_date = datetime.utcnow()
        cves = await self._fetch_date_range(last_sync, end_date)

        # Update sync state
        self.sync_state["last_sync"] = end_date.isoformat()
        self.sync_state["total_processed"] = self.sync_state.get(
            "total_processed", 0
        ) + len(cves)
        self._save_sync_state()

        return cves

    async def _fetch_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[CVEData]:
        """
        Fetch all CVEs modified within a date range.

        Handles pagination automatically.
        """
        params = {
            "lastModStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "lastModEndDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": self.MAX_RESULTS_PER_PAGE,
        }

        if self.api_key:
            params["apiKey"] = self.api_key

        all_cves: List[CVEData] = []
        start_index = 0

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            while True:
                params["startIndex"] = start_index

                # Apply rate limiting
                await self._rate_limit()

                logger.debug(f"Fetching CVEs: startIndex={start_index}")

                async with self.session.get(self.BASE_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                vulnerabilities = data.get("vulnerabilities", [])
                if not vulnerabilities:
                    break

                # Process CVEs
                for vuln in vulnerabilities:
                    cve_data = self._parse_cve(vuln)
                    if cve_data:
                        all_cves.append(cve_data)

                # Check if more results exist
                total_results = data.get("totalResults", 0)
                if start_index + len(vulnerabilities) >= total_results:
                    break

                start_index += len(vulnerabilities)

                logger.info(f"Processed {start_index}/{total_results} CVEs")

        except Exception as e:
            logger.error(f"Error fetching CVEs: {e}")
            raise

        logger.info(f"Fetched {len(all_cves)} CVEs total")
        return all_cves

    def _parse_cve(self, vuln_data: Dict[str, Any]) -> Optional[CVEData]:
        """Parse CVE data from NVD API response."""
        try:
            cve = vuln_data.get("cve", {})

            # Extract basic information
            cve_id = cve.get("id")
            if not cve_id:
                return None

            # Extract descriptions
            descriptions = cve.get("descriptions", [])
            description = next(
                (d["value"] for d in descriptions if d.get("lang") == "en"),
                "No description available",
            )

            # Extract CVSS scores
            metrics = cve.get("metrics", {})
            cvss_v3_data = self._extract_cvss_v3(metrics)
            cvss_v2_data = self._extract_cvss_v2(metrics)

            # Extract CWE IDs
            weaknesses = cve.get("weaknesses", [])
            cwe_ids = self._extract_cwe_ids(weaknesses)

            # Extract CPE matches (affected products)
            configurations = cve.get("configurations", [])
            cpe_matches = self._extract_cpe_matches(configurations)

            # Extract vendor/product from CPE
            vendor, product = self._extract_vendor_product(cpe_matches)

            # Extract references
            references = cve.get("references", [])

            return CVEData(
                cve_id=cve_id,
                published=cve.get("published", ""),
                last_modified=cve.get("lastModified", ""),
                description=description,
                cvss_v3_score=cvss_v3_data.get("score"),
                cvss_v3_vector=cvss_v3_data.get("vector"),
                cvss_v2_score=cvss_v2_data.get("score"),
                cvss_v2_vector=cvss_v2_data.get("vector"),
                cwe_ids=cwe_ids,
                cpe_matches=cpe_matches,
                references=references,
                vendor=vendor,
                product=product,
            )

        except Exception as e:
            logger.error(f"Error parsing CVE {vuln_data.get('cve', {}).get('id')}: {e}")
            return None

    def _extract_cvss_v3(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CVSS v3 metrics."""
        cvss_v3 = metrics.get("cvssMetricV31", []) or metrics.get("cvssMetricV30", [])
        if cvss_v3:
            cvss_data = cvss_v3[0].get("cvssData", {})
            return {
                "score": cvss_data.get("baseScore"),
                "vector": cvss_data.get("vectorString"),
            }
        return {}

    def _extract_cvss_v2(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CVSS v2 metrics."""
        cvss_v2 = metrics.get("cvssMetricV2", [])
        if cvss_v2:
            cvss_data = cvss_v2[0].get("cvssData", {})
            return {
                "score": cvss_data.get("baseScore"),
                "vector": cvss_data.get("vectorString"),
            }
        return {}

    def _extract_cwe_ids(self, weaknesses: List[Dict[str, Any]]) -> List[str]:
        """Extract CWE IDs from weakness data."""
        cwe_ids = []
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    value = desc.get("value", "")
                    if value.startswith("CWE-"):
                        cwe_ids.append(value)
        return cwe_ids

    def _extract_cpe_matches(
        self, configurations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract CPE matches for affected products."""
        cpe_matches = []
        for config in configurations:
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    if match.get("vulnerable"):
                        cpe_matches.append(
                            {
                                "cpe": match.get("criteria"),
                                "version_start": match.get("versionStartIncluding"),
                                "version_end": match.get("versionEndExcluding"),
                            }
                        )
        return cpe_matches

    def _extract_vendor_product(
        self, cpe_matches: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract vendor and product from CPE strings."""
        if not cpe_matches:
            return None, None

        # Parse first CPE string
        # format: cpe:2.3:part:vendor:product:version:...
        cpe = cpe_matches[0].get("cpe", "")
        parts = cpe.split(":")

        if len(parts) >= 5:
            vendor = parts[3] if parts[3] != "*" else None
            product = parts[4] if parts[4] != "*" else None
            return vendor, product

        return None, None


async def main() -> None:
    """Example usage of NVD fetcher."""
    async with NVDFetcher() as fetcher:
        # Fetch recent CVEs
        logger.info("Fetching recent CVEs...")
        recent_cves = await fetcher.fetch_recent(days=1)
        logger.info(f"Found {len(recent_cves)} recent CVEs")

        if recent_cves:
            # Show sample CVE
            cve = recent_cves[0]
            logger.info(f"Sample CVE: {cve.cve_id}")
            logger.info(f"  Description: {cve.description[:100]}...")
            if cve.cvss_v3_score:
                logger.info(f"  CVSS v3 Score: {cve.cvss_v3_score}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
