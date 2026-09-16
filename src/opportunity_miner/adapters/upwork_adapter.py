"""Upwork adapter using Cloudflare-safe RSS feeds and local JSON import dropzone."""

from datetime import datetime
import json
import logging
from pathlib import Path
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests

from .base import SourceAdapter, NormalizedSignal

logger = logging.getLogger(__name__)


class UpworkAdapter(SourceAdapter):
    """Adapter for extracting commercial demands from Upwork via RSS and local dropzone."""

    RSS_BASE_URL = "https://www.upwork.com/ab/feed/jobs/rss"
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def __init__(self, dropzone_path: str = "data/imports/upwork"):
        self.dropzone_path = Path(dropzone_path)

    @property
    def source_name(self) -> str:
        return "upwork"

    def health_check(self) -> tuple[bool, str]:
        # Upwork dropzone directory check
        if not self.dropzone_path.exists():
            self.dropzone_path.mkdir(parents=True, exist_ok=True)
        return True, f"Upwork adapter ready (Dropzone: {self.dropzone_path})"

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        # Tier 1: Check local JSON dropzone files
        if self.dropzone_path.exists():
            for json_file in self.dropzone_path.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        if isinstance(items, dict):
                            items = [items]
                        for item in items:
                            job_id = item.get("id") or item.get("ciphertext") or str(hash(item.get("title", "")))
                            if job_id in seen_ids:
                                continue
                            seen_ids.add(job_id)

                            title = item.get("title") or "Upwork Project Listing"
                            desc = item.get("description") or item.get("snippet") or ""
                            url = item.get("url") or f"https://www.upwork.com/jobs/{job_id}"
                            
                            signal = NormalizedSignal(
                                source="upwork",
                                source_id=job_id,
                                source_url=url,
                                title=title,
                                author=item.get("client_country", "Public Client"),
                                body=f"{title}\n\n{desc}".strip(),
                                published_at=datetime.utcnow(),
                                metadata={
                                    "budget": item.get("budget"),
                                    "hourly_rate": item.get("hourly_rate"),
                                    "skills": item.get("skills", []),
                                    "ingest_tier": "dropzone_json"
                                }
                            )
                            results.append(signal)
                except Exception as e:
                    logger.warning(f"Error reading Upwork dropzone file {json_file}: {e}")

        # Tier 2: Public RSS job feeds
        headers = {"User-Agent": self.DEFAULT_USER_AGENT}
        for query in queries:
            if len(results) >= limit:
                break

            encoded_query = urllib.parse.quote_plus(query)
            rss_url = f"{self.RSS_BASE_URL}?q={encoded_query}&sort=recency"

            try:
                resp = requests.get(rss_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    channel = root.find("channel")
                    if channel is not None:
                        for item in channel.findall("item"):
                            link = item.findtext("link", default="")
                            title = item.findtext("title", default="")
                            description = item.findtext("description", default="")
                            guid = item.findtext("guid", default=link)

                            if guid in seen_ids:
                                continue
                            seen_ids.add(guid)

                            # Parse budget from description if present
                            budget_match = re.search(r"<b>Budget</b>:\s*\$([0-9,]+)", description)
                            budget = float(budget_match.group(1).replace(",", "")) if budget_match else None

                            # Clean HTML tags from description
                            clean_body = re.sub(r"<[^>]+>", " ", description).strip()

                            signal = NormalizedSignal(
                                source="upwork",
                                source_id=guid,
                                source_url=link,
                                title=title,
                                author="Client",
                                body=f"{title}\n\n{clean_body}".strip(),
                                published_at=datetime.utcnow(),
                                metadata={
                                    "query": query,
                                    "budget": budget,
                                    "ingest_tier": "rss"
                                }
                            )
                            results.append(signal)
            except Exception as e:
                logger.debug(f"Upwork RSS search failed for '{query}': {e}")

        return results
