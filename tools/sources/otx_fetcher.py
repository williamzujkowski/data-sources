"""AlienVault OTX fetcher for threat intelligence data."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class OTXFetcher:
    """AlienVault OTX pulse fetcher with intelligent caching."""

    def __init__(self, api_key: str) -> None:
        """Initialize OTX fetcher with API key.

        Args:
            api_key: OTX API key for authentication
        """
        self.api_key = api_key
        self.base_url = "https://otx.alienvault.com/api/v1"
        self.headers = {"X-OTX-API-KEY": api_key}
        self.pulse_cache: Dict[str, Dict[str, Any]] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "OTXFetcher":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch_recent_pulses(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch pulses from the last N hours.

        Args:
            hours: Number of hours to look back (default 24)

        Returns:
            List of processed pulse dictionaries
        """
        modified_since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            url = f"{self.base_url}/pulses/subscribed"
            params = {"modified_since": modified_since, "limit": 50}

            async with self.session.get(
                url, headers=self.headers, params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return self._process_pulses(data.get("results", []))

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching OTX pulses: {e}")
            return []

    async def fetch_pulse_details(self, pulse_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific pulse.

        Args:
            pulse_id: OTX pulse identifier

        Returns:
            Processed pulse details or None if error
        """
        # Check cache first
        if pulse_id in self.pulse_cache:
            cached = self.pulse_cache[pulse_id]
            if cached["cached_at"] > datetime.utcnow() - timedelta(hours=1):
                return cached["data"]

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            url = f"{self.base_url}/pulses/{pulse_id}"

            async with self.session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                processed = self._process_pulse_details(data)

                # Cache the result
                self.pulse_cache[pulse_id] = {
                    "data": processed,
                    "cached_at": datetime.utcnow(),
                }

                return processed

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching pulse {pulse_id}: {e}")
            return None

    def _process_pulses(self, pulses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and enrich pulse data.

        Args:
            pulses: Raw pulse data from OTX API

        Returns:
            List of processed pulse dictionaries
        """
        processed = []
        for pulse in pulses:
            processed_pulse = {
                "source": "otx",
                "pulse_id": pulse.get("id"),
                "name": pulse.get("name"),
                "description": pulse.get("description"),
                "created": pulse.get("created"),
                "modified": pulse.get("modified"),
                "author": pulse.get("author_name"),
                "indicators": self._extract_indicators(pulse),
                "tags": pulse.get("tags", []),
                "references": pulse.get("references", []),
                "targeted_countries": pulse.get("targeted_countries", []),
                "malware_families": pulse.get("malware_families", []),
                "attack_ids": self._map_to_attack_ids(pulse),
                "tlp": pulse.get("tlp", "white"),
                "adversary": pulse.get("adversary"),
                "industries": pulse.get("industries", []),
            }
            processed.append(processed_pulse)
        return processed

    def _process_pulse_details(self, pulse: Dict[str, Any]) -> Dict[str, Any]:
        """Process detailed pulse information.

        Args:
            pulse: Raw detailed pulse data

        Returns:
            Processed pulse with full indicator details
        """
        return {
            "source": "otx",
            "pulse_id": pulse.get("id"),
            "name": pulse.get("name"),
            "description": pulse.get("description"),
            "created": pulse.get("created"),
            "modified": pulse.get("modified"),
            "author": {
                "username": pulse.get("author_name"),
                "id": pulse.get("author", {}).get("id"),
            },
            "indicators": self._extract_indicators(pulse, detailed=True),
            "tags": pulse.get("tags", []),
            "references": pulse.get("references", []),
            "targeted_countries": pulse.get("targeted_countries", []),
            "malware_families": pulse.get("malware_families", []),
            "attack_ids": self._map_to_attack_ids(pulse),
            "tlp": pulse.get("tlp", "white"),
            "adversary": pulse.get("adversary"),
            "industries": pulse.get("industries", []),
            "revision": pulse.get("revision", 1),
            "public": pulse.get("public", True),
            "votes": {"up": pulse.get("upvotes", 0), "down": pulse.get("downvotes", 0)},
            "pulse_source": pulse.get("pulse_source", "user"),
            "observation": pulse.get("observation", {}),
        }

    def _extract_indicators(
        self, pulse: Dict[str, Any], detailed: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract and categorize indicators from pulse.

        Args:
            pulse: Pulse data containing indicators
            detailed: Whether to include detailed indicator metadata

        Returns:
            Dictionary of indicators categorized by type
        """
        indicators: Dict[str, List[Dict[str, Any]]] = {
            "ipv4": [],
            "ipv6": [],
            "domain": [],
            "hostname": [],
            "url": [],
            "md5": [],
            "sha1": [],
            "sha256": [],
            "imphash": [],
            "pehash": [],
            "email": [],
            "cve": [],
            "mutex": [],
            "filepath": [],
            "yara": [],
        }

        for indicator in pulse.get("indicators", []):
            ioc_type = indicator.get("type", "").lower()

            # Map OTX types to our standard types
            type_mapping = {
                "ipv4": "ipv4",
                "ipv6": "ipv6",
                "domain": "domain",
                "hostname": "hostname",
                "url": "url",
                "filehash-md5": "md5",
                "filehash-sha1": "sha1",
                "filehash-sha256": "sha256",
                "filehash-imphash": "imphash",
                "filehash-pehash": "pehash",
                "email": "email",
                "cve": "cve",
                "mutex": "mutex",
                "filepath": "filepath",
                "yara": "yara",
            }

            mapped_type = type_mapping.get(ioc_type)
            if mapped_type and mapped_type in indicators:
                if detailed:
                    indicators[mapped_type].append(
                        {
                            "value": indicator.get("indicator"),
                            "type": indicator.get("type"),
                            "description": indicator.get("description"),
                            "created": indicator.get("created"),
                            "title": indicator.get("title"),
                            "content": indicator.get("content"),
                            "is_active": indicator.get("is_active", True),
                            "observations": indicator.get("observations", 0),
                            "role": indicator.get("role"),
                        }
                    )
                else:
                    indicators[mapped_type].append(
                        {
                            "value": indicator.get("indicator"),
                            "description": indicator.get("description"),
                            "created": indicator.get("created"),
                        }
                    )

        return indicators

    def _map_to_attack_ids(self, pulse: Dict[str, Any]) -> List[str]:
        """Map pulse data to MITRE ATT&CK technique IDs.

        Args:
            pulse: Pulse data to analyze

        Returns:
            List of ATT&CK technique IDs
        """
        attack_ids = []

        # Direct ATT&CK references in tags
        for tag in pulse.get("tags", []):
            if tag.upper().startswith("T") and len(tag) == 5:
                # Likely an ATT&CK technique ID
                attack_ids.append(tag.upper())

        # Check references for ATT&CK URLs
        for ref in pulse.get("references", []):
            if "attack.mitre.org" in ref:
                # Extract technique ID from URL
                import re

                match = re.search(r"/techniques/(T\d{4})", ref)
                if match:
                    attack_ids.append(match.group(1))

        # Look for ATT&CK patterns in description
        if pulse.get("description"):
            import re

            techniques = re.findall(r"\bT\d{4}(?:\.\d{3})?\b", pulse["description"])
            attack_ids.extend(techniques)

        # Remove duplicates and return
        return list(set(attack_ids))

    async def search_indicators(
        self, indicator_value: str, indicator_type: str
    ) -> Dict[str, Any]:
        """Search for information about a specific indicator.

        Args:
            indicator_value: The indicator to search for
            indicator_type: Type of indicator (ip, domain, hash, etc.)

        Returns:
            Dictionary with indicator reputation and related pulses
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            # Map types to OTX API format
            type_map = {
                "ip": "IPv4",
                "ipv4": "IPv4",
                "ipv6": "IPv6",
                "domain": "domain",
                "hostname": "hostname",
                "url": "url",
                "md5": "file",
                "sha1": "file",
                "sha256": "file",
            }

            api_type = type_map.get(indicator_type.lower(), indicator_type)
            url = f"{self.base_url}/indicators/{api_type}/" f"{indicator_value}/general"

            async with self.session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()

                return {
                    "indicator": indicator_value,
                    "type": indicator_type,
                    "pulse_count": data.get("pulse_info", {}).get("count", 0),
                    "pulses": data.get("pulse_info", {}).get("pulses", []),
                    "reputation": data.get("reputation", 0),
                    "base_indicator": data.get("base_indicator", {}),
                    "validation": data.get("validation", []),
                }

        except aiohttp.ClientError as e:
            logger.error(f"Error searching indicator {indicator_value}: {e}")
            return {
                "indicator": indicator_value,
                "type": indicator_type,
                "error": str(e),
            }


async def main() -> None:
    """Example usage of OTX fetcher."""
    # Note: Replace with actual API key
    api_key = "YOUR_OTX_API_KEY"

    async with OTXFetcher(api_key) as fetcher:
        # Fetch recent pulses
        recent_pulses = await fetcher.fetch_recent_pulses(hours=24)
        logger.info(f"Found {len(recent_pulses)} recent pulses")

        # Get details for first pulse if available
        if recent_pulses:
            pulse_id = recent_pulses[0]["pulse_id"]
            details = await fetcher.fetch_pulse_details(pulse_id)
            if details:
                logger.info(f"Pulse: {details['name']}")
                indicator_count = sum(len(v) for v in details["indicators"].values())
                logger.info(f"Indicators: {indicator_count}")

        # Search for a specific indicator
        result = await fetcher.search_indicators("8.8.8.8", "ipv4")
        logger.info(f"Indicator reputation: {result.get('reputation', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
