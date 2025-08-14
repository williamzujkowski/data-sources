"""Fetcher for abuse.ch threat intelligence feeds."""

import asyncio
import csv
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AbuseCHFetcher:
    """Fetcher for abuse.ch threat feeds.

    Includes URLhaus, MalwareBazaar, Feodo Tracker, ThreatFox feeds."""

    FEEDS = {
        "urlhaus": {
            "url": "https://urlhaus.abuse.ch/downloads/csv_recent/",
            "type": "malware_urls",
            "description": "Malicious URL feed",
        },
        "malwarebazaar": {
            "url": "https://bazaar.abuse.ch/export/csv/recent/",
            "type": "malware_samples",
            "description": "Malware sample repository",
        },
        "feodotracker": {
            "url": (
                "https://feodotracker.abuse.ch/downloads/" "ipblocklist_recommended.csv"
            ),
            "type": "c2_servers",
            "description": "Feodo Trojan C2 tracker",
        },
        "threatfox": {
            "url": "https://threatfox.abuse.ch/export/csv/recent/",
            "type": "iocs",
            "description": "IOC sharing platform",
        },
    }

    def __init__(self) -> None:
        """Initialize abuse.ch fetcher."""
        self.session = None
        self.cache = {}

    async def __aenter__(self) -> "AbuseCHFetcher":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch_all_feeds(self) -> Dict[str, List]:
        """Fetch all abuse.ch feeds concurrently.

        Returns:
            Dictionary mapping feed names to their parsed data
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        tasks = [self.fetch_feed(name, config) for name, config in self.FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        feed_data = {}
        for name, result in zip(self.FEEDS.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {name}: {result}")
                feed_data[name] = []
            else:
                feed_data[name] = result

        return feed_data

    async def fetch_feed(self, name: str, config: Dict) -> List[Dict]:
        """Fetch and parse a single abuse.ch feed.

        Args:
            name: Feed name (urlhaus, malwarebazaar, etc.)
            config: Feed configuration with URL and type

        Returns:
            List of parsed feed entries
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(config["url"]) as response:
                response.raise_for_status()
                content = await response.text()

                if name == "urlhaus":
                    return self._parse_urlhaus(content)
                elif name == "malwarebazaar":
                    return self._parse_malwarebazaar(content)
                elif name == "feodotracker":
                    return self._parse_feodotracker(content)
                elif name == "threatfox":
                    return self._parse_threatfox(content)
                else:
                    return self._parse_generic_csv(name, content, config["type"])

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching {name} feed: {e}")
            return []

    def _parse_urlhaus(self, content: str) -> List[Dict]:
        """Parse URLhaus CSV feed.

        Args:
            content: Raw CSV content from URLhaus

        Returns:
            List of parsed URL entries
        """
        parsed_data = []

        # Skip comment lines
        lines = [line for line in content.split("\n") if not line.startswith("#")]

        if not lines:
            return parsed_data

        # URLhaus CSV format (after comments):
        # id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter

        reader = csv.DictReader(io.StringIO("\n".join(lines)))

        for row in reader:
            if not row.get("url"):
                continue

            entry = {
                "source": "abuse.ch_urlhaus",
                "type": "malware_url",
                "indicator": row.get("url", ""),
                "indicator_type": "url",
                "first_seen": row.get("dateadded", ""),
                "last_seen": row.get("last_online", ""),
                "status": row.get("url_status", ""),
                "threat": row.get("threat", ""),
                "tags": [
                    tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()
                ],
                "reference": row.get("urlhaus_link", ""),
                "reporter": row.get("reporter", ""),
                "metadata": {"urlhaus_id": row.get("id", ""), "feed": "urlhaus"},
                "timestamp": datetime.utcnow().isoformat(),
            }
            parsed_data.append(entry)

        return parsed_data

    def _parse_malwarebazaar(self, content: str) -> List[Dict]:
        """Parse MalwareBazaar CSV feed.

        Args:
            content: Raw CSV content from MalwareBazaar

        Returns:
            List of parsed malware sample entries
        """
        parsed_data = []

        # Skip comment lines
        lines = [line for line in content.split("\n") if not line.startswith("#")]

        if not lines:
            return parsed_data

        # MalwareBazaar CSV format:
        # first_seen,sha256_hash,md5_hash,sha1_hash,reporter,file_name,file_type_guess,mime_type,signature,clamav,imphash,ssdeep,tags

        reader = csv.DictReader(io.StringIO("\n".join(lines)))

        for row in reader:
            if not row.get("sha256_hash"):
                continue

            entry = {
                "source": "abuse.ch_malwarebazaar",
                "type": "malware_sample",
                "indicator": row.get("sha256_hash", ""),
                "indicator_type": "sha256",
                "first_seen": row.get("first_seen", ""),
                "file_name": row.get("file_name", ""),
                "file_type": row.get("file_type_guess", ""),
                "mime_type": row.get("mime_type", ""),
                "signature": row.get("signature", ""),
                "malware_family": row.get("signature", ""),
                "tags": [
                    tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()
                ],
                "reporter": row.get("reporter", ""),
                "hashes": {
                    "md5": row.get("md5_hash", ""),
                    "sha1": row.get("sha1_hash", ""),
                    "sha256": row.get("sha256_hash", ""),
                    "imphash": row.get("imphash", ""),
                    "ssdeep": row.get("ssdeep", ""),
                },
                "detection": {
                    "signature": row.get("signature", ""),
                    "clamav": row.get("clamav", ""),
                },
                "metadata": {"feed": "malwarebazaar"},
                "timestamp": datetime.utcnow().isoformat(),
            }
            parsed_data.append(entry)

        return parsed_data

    def _parse_feodotracker(self, content: str) -> List[Dict]:
        """Parse Feodo Tracker blocklist.

        Args:
            content: Raw CSV content from Feodo Tracker

        Returns:
            List of parsed C2 server entries
        """
        parsed_data = []

        # Skip comment lines
        lines = [line for line in content.split("\n") if not line.startswith("#")]

        if not lines:
            return parsed_data

        # Feodo Tracker format:
        # first_seen,ip_address,port,last_online,malware

        # Check if first non-comment line is a header
        first_line = lines[0] if lines else ""
        has_header = "first_seen" in first_line.lower()

        if has_header:
            reader = csv.DictReader(io.StringIO("\n".join(lines)))
        else:
            # No header, define field names
            fieldnames = ["first_seen", "ip_address", "port", "last_online", "malware"]
            reader = csv.DictReader(
                io.StringIO("\n".join(lines)), fieldnames=fieldnames
            )

        for row in reader:
            if not row.get("ip_address"):
                continue

            entry = {
                "source": "abuse.ch_feodotracker",
                "type": "c2_server",
                "indicator": row.get("ip_address", ""),
                "indicator_type": "ipv4",
                "first_seen": row.get("first_seen", ""),
                "last_seen": row.get("last_online", ""),
                "port": row.get("port", ""),
                "malware_family": row.get("malware", "Feodo"),
                "status": "active" if row.get("last_online") else "inactive",
                "tags": ["c2", "botnet", row.get("malware", "feodo").lower()],
                "metadata": {"feed": "feodotracker"},
                "timestamp": datetime.utcnow().isoformat(),
            }
            parsed_data.append(entry)

        return parsed_data

    def _parse_threatfox(self, content: str) -> List[Dict]:
        """Parse ThreatFox IOC feed.

        Args:
            content: Raw CSV content from ThreatFox

        Returns:
            List of parsed IOC entries
        """
        parsed_data = []

        # Skip comment lines
        lines = [line for line in content.split("\n") if not line.startswith("#")]

        if not lines:
            return parsed_data

        # ThreatFox CSV format:
        # first_seen,ioc_id,ioc_value,ioc_type,threat_type,malware,malware_alias,reporter,tags

        reader = csv.DictReader(io.StringIO("\n".join(lines)))

        for row in reader:
            if not row.get("ioc_value"):
                continue

            # Determine indicator type
            ioc_type = row.get("ioc_type", "").lower()
            if "ip:port" in ioc_type:
                indicator_type = "ip_port"
            elif "domain" in ioc_type:
                indicator_type = "domain"
            elif "url" in ioc_type:
                indicator_type = "url"
            elif "md5" in ioc_type:
                indicator_type = "md5"
            elif "sha256" in ioc_type:
                indicator_type = "sha256"
            else:
                indicator_type = "unknown"

            entry = {
                "source": "abuse.ch_threatfox",
                "type": "ioc",
                "indicator": row.get("ioc_value", ""),
                "indicator_type": indicator_type,
                "first_seen": row.get("first_seen", ""),
                "threat_type": row.get("threat_type", ""),
                "malware_family": row.get("malware", ""),
                "malware_alias": [
                    alias.strip()
                    for alias in row.get("malware_alias", "").split(",")
                    if alias.strip()
                ],
                "tags": [
                    tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()
                ],
                "reporter": row.get("reporter", ""),
                "metadata": {
                    "threatfox_id": row.get("ioc_id", ""),
                    "ioc_type": row.get("ioc_type", ""),
                    "feed": "threatfox",
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
            parsed_data.append(entry)

        return parsed_data

    def _parse_generic_csv(
        self, feed_name: str, content: str, feed_type: str
    ) -> List[Dict[str, Any]]:
        """Generic CSV parser for unknown feed formats.

        Args:
            feed_name: Name of the feed
            content: Raw CSV content
            feed_type: Type of feed data

        Returns:
            List of parsed entries
        """
        parsed_data = []

        # Skip comment lines
        lines = [line for line in content.split("\n") if not line.startswith("#")]
        csv_content = "\n".join(lines)

        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            parsed_data.append(
                {
                    "source": f"abuse.ch_{feed_name}",
                    "type": feed_type,
                    "data": row,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return parsed_data

    async def get_urlhaus_url_info(self, url: str) -> Optional[Dict]:
        """Get detailed information about a specific URL from URLhaus.

        Args:
            url: URL to look up

        Returns:
            URL information or None if not found
        """
        api_url = "https://urlhaus-api.abuse.ch/v1/url/"

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            data = {"url": url}
            async with self.session.post(api_url, data=data) as response:
                response.raise_for_status()
                result = await response.json()

                if result.get("query_status") == "ok":
                    return result
                else:
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"Error querying URLhaus for {url}: {e}")
            return None

    async def get_malwarebazaar_hash_info(self, file_hash: str) -> Optional[Dict]:
        """Get detailed information about a file hash from MalwareBazaar.

        Args:
            file_hash: MD5, SHA1, or SHA256 hash

        Returns:
            Malware information or None if not found
        """
        api_url = "https://mb-api.abuse.ch/api/v1/"

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            data = {"query": "get_info", "hash": file_hash}
            async with self.session.post(api_url, data=data) as response:
                response.raise_for_status()
                result = await response.json()

                if result.get("query_status") == "ok":
                    return result
                else:
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"Error querying MalwareBazaar for {file_hash}: {e}")
            return None


async def main() -> None:
    """Example usage of abuse.ch fetcher."""
    async with AbuseCHFetcher() as fetcher:
        # Fetch all feeds
        logger.info("Fetching all abuse.ch feeds...")
        feeds = await fetcher.fetch_all_feeds()

        for feed_name, data in feeds.items():
            logger.info(f"{feed_name}: {len(data)} entries")

            # Show sample entry if available
            if data:
                logger.info(f"  Sample: {data[0].get('indicator', 'N/A')}")

        # Query specific URL
        test_url = "http://malicious.example.com"
        url_info = await fetcher.get_urlhaus_url_info(test_url)
        if url_info:
            logger.info(f"URL info: {url_info}")

        # Query specific hash
        test_hash = (
            "0123456789abcdef0123456789abcdef" "0123456789abcdef0123456789abcdef"
        )
        hash_info = await fetcher.get_malwarebazaar_hash_info(test_hash)
        if hash_info:
            logger.info(f"Hash info: {hash_info}")


if __name__ == "__main__":
    asyncio.run(main())
