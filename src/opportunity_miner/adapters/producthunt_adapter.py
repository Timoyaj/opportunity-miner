"""Product Hunt source adapter for product gaps and workflow complaints."""

from datetime import datetime
import logging
import os
import re
import xml.etree.ElementTree as ET
import requests

from .base import SourceAdapter, NormalizedSignal

logger = logging.getLogger(__name__)


class ProductHuntAdapter(SourceAdapter):
    """Adapter for detecting feature gaps and missing functionality on Product Hunt."""

    ATOM_FEED = "https://www.producthunt.com/feed"
    DEFAULT_USER_AGENT = "OpportunityMiner-Research/0.1.0"

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("PRODUCTHUNT_TOKEN")

    @property
    def source_name(self) -> str:
        return "producthunt"

    def health_check(self) -> tuple[bool, str]:
        if self.token:
            return True, "Product Hunt API v2 token configured (OK)"
        try:
            resp = requests.get(self.ATOM_FEED, headers={"User-Agent": self.DEFAULT_USER_AGENT}, timeout=5)
            if resp.status_code == 200:
                return True, "Product Hunt Atom feed accessible (OK)"
            return False, f"Product Hunt Atom feed HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Product Hunt unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 25, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        try:
            resp = requests.get(self.ATOM_FEED, headers={"User-Agent": self.DEFAULT_USER_AGENT}, timeout=8)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)
                for entry in entries:
                    if len(results) >= limit:
                        break

                    entry_id = entry.findtext("atom:id", default="", namespaces=ns)
                    if not entry_id or entry_id in seen_ids:
                        continue
                    seen_ids.add(entry_id)

                    title = entry.findtext("atom:title", default="", namespaces=ns)
                    content = entry.findtext("atom:content", default="", namespaces=ns)
                    link_elem = entry.find("atom:link", ns)
                    link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                    author = entry.findtext("atom:author/atom:name", default="", namespaces=ns)

                    clean_body = re.sub(r"<[^>]+>", " ", content).strip()
                    body = f"{title}\n\n{clean_body}".strip()

                    signal = NormalizedSignal(
                        source="producthunt",
                        source_id=entry_id.split("/")[-1] if "/" in entry_id else entry_id,
                        source_url=link,
                        title=title,
                        author=author,
                        body=body,
                        published_at=datetime.utcnow(),
                        metadata={"ingest_tier": "atom_feed"}
                    )
                    results.append(signal)
        except Exception as e:
            logger.warning(f"Product Hunt collection failed: {e}")

        return results
