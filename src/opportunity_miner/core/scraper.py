"""Scraping and text cleaning utilities integrating agent-reach protocols."""

from datetime import datetime
import html
import logging
import re
import requests

logger = logging.getLogger(__name__)


def clean_scraped_text(raw_text: str) -> str:
    """Cleans raw scraped text, unescaping HTML entities, removing HTML tags, and stripping RSS noise."""
    if not raw_text:
        return ""

    # Unescape HTML entities (&amp;, &#39;, &quot;, etc.)
    text = html.unescape(raw_text)

    # Remove Reddit RSS metadata footers
    text = re.sub(r"submitted by\s+/u/\S+.*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[link\]\s+\[comments\].*", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Clean Markdown image / link clutter while preserving text
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_url_clean(url: str, timeout: int = 8) -> str | None:
    """Fetch clean markdown content for any public URL.

    FREE OSS cascade (all zero-cost, self-hostable):
      1. Trafilatura (MIT, pip: trafilatura) — best open-source article extractor
      2. BeautifulSoup (MIT, pip: beautifulsoup4 + lxml) — fallback HTML parse
      3. Jina Reader (free service, https://r.jina.ai/) — last-resort zero-config
    """
    if not url or not url.startswith("http"):
        return None

    # 1. Local Trafilatura (MIT) — no network to external AI service
    try:
        import trafilatura  # type: ignore

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if extracted:
                return clean_scraped_text(extracted)
    except Exception as e:
        logger.debug(f"Trafilatura fetch failed for {url}: {e}")

    # 2. Direct requests + BeautifulSoup (MIT)
    try:
        try:
            from bs4 import BeautifulSoup  # type: ignore

            headers = {"User-Agent": "OpportunityMiner-Research/0.2.0 (Commercial problem discovery)"}
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text, "lxml")
                # Remove noise
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)
                cleaned = clean_scraped_text(text)
                if cleaned and len(cleaned) > 80:
                    return cleaned
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"BeautifulSoup fetch failed for {url}: {e}")
    except Exception:
        pass

    # 3. Jina Reader fallback (free, no key)
    try:
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "User-Agent": "OpportunityMiner-Research/0.2.0 (Commercial problem discovery)",
            "Accept": "text/plain, text/markdown",
        }
        resp = requests.get(jina_url, headers=headers, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return clean_scraped_text(resp.text)
    except Exception as e:
        logger.debug(f"Jina Reader fetch failed for {url}: {e}")

    return None


def extract_verbatim_quotes(text: str, max_quotes: int = 3) -> list[str]:
    """Extracts authentic, verbatim sentences expressing user pain, friction, tasks, or confusion."""
    cleaned = clean_scraped_text(text)
    if not cleaned:
        return []

    # Split into candidate sentences
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", cleaned)
    candidates = []

    pain_triggers = [
        "tedious", "manual", "manually", "takes hours", "frustrating", "waste", "struggle",
        "error", "can't", "cannot", "broken", "issue", "problem", "trying to", "dilemma",
        "need help", "how do i", "how to", "stuck", "automate", "macro", "script", "copy paste",
        "nightmare", "impossible", "failed", "failing", "why does", "doesn't work", "formula"
    ]

    for s in raw_sentences:
        s_str = s.strip()
        if len(s_str) < 18 or len(s_str) > 280:
            continue
        # Skip lines that are just urls or author lines
        if s_str.startswith("http") or s_str.startswith("r/") or "submitted by" in s_str.lower():
            continue

        s_low = s_str.lower()
        if any(t in s_low for t in pain_triggers):
            candidates.append(s_str)
            if len(candidates) >= max_quotes:
                break

    # If no explicit keyword was hit, capture the most substantive user sentence
    if not candidates:
        for s in raw_sentences:
            s_str = s.strip()
            if 25 <= len(s_str) <= 200 and not s_str.startswith("http"):
                candidates.append(s_str)
                if len(candidates) >= 2:
                    break

    return candidates
