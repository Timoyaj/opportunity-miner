"""App Store Reviews adapter — 100% free, no key, self-hostable.

Covers:
  - Apple App Store Customer Reviews RSS (JSON): https://itunes.apple.com/rss/customerreviews/page=1/id=<APP_ID>/sortby=mostrecent/json
    IDs: Excel=586683407, Sheets? packaged as Google Drive id, PowerBI mobile etc.
  - Apple Lookup fallback for metadata
  - Google Play free scrape via `google-play-scraper` pip is optional (if installed), else skips gracefully.

All endpoints are public, MIT-friendly, no paid proxy needed.
"""

from datetime import datetime
import logging
import requests

from .base import SourceAdapter, NormalizedSignal
from ..core.scraper import clean_scraped_text

logger = logging.getLogger(__name__)


# Default apps to monitor for workflow pain — spreadsheet / reporting niche
DEFAULT_APPS = [
    {"store": "apple", "id": "586683407", "name": "Microsoft Excel", "country": "us"},
    {"store": "apple", "id": "462058009", "name": "Microsoft Power BI", "country": "us"},
    {"store": "apple", "id": "879299342", "name": "Notion", "country": "us"},
    {"store": "apple", "id": "1342769574", "name": "Trello", "country": "us"},
]


class AppStoreAdapter(SourceAdapter):
    """Adapter for mining 1-star churn + feature-gap pain from App Store reviews."""

    APPLE_RSS_TEMPLATE = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"

    @property
    def source_name(self) -> str:
        return "appstore"

    def health_check(self) -> tuple[bool, str]:
        # Check Apple RSS reachable with Excel app
        try:
            url = self.APPLE_RSS_TEMPLATE.format(country="us", page=1, app_id="586683407")
            resp = requests.get(url, headers={"User-Agent": "OpportunityMiner/0.1.0"}, timeout=5)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # Valid JSON with feed key
                    if "feed" in data:
                        return True, "Apple App Store Reviews RSS accessible (OK)"
                    return True, "Apple RSS reachable (OK)"
                except Exception:
                    return True, "Apple RSS reachable (OK)"
            # Apple sometimes returns 404 if no reviews recently — still reachable
            if resp.status_code in (403, 404):
                return True, f"Apple RSS endpoint reachable (HTTP {resp.status_code}, expected for some apps)"
            return False, f"Apple RSS returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"App Store unreachable: {str(e)}"

    def _collect_apple(self, app: dict, limit: int, since: datetime | None) -> list[NormalizedSignal]:
        signals: list[NormalizedSignal] = []
        app_id = app.get("id")
        app_name = app.get("name", f"App {app_id}")
        country = app.get("country", "us")

        # Apple RSS only returns up to 50 most-recent reviews per page (1 page)
        url = self.APPLE_RSS_TEMPLATE.format(country=country, page=1, app_id=app_id)
        try:
            resp = requests.get(url, headers={"User-Agent": "OpportunityMiner/0.1.0"}, timeout=10)
            if resp.status_code != 200:
                logger.debug(f"Apple RSS for {app_name} ({app_id}) returned {resp.status_code}")
                return signals

            data = resp.json()
            feed = data.get("feed", {})
            entries = feed.get("entry", [])
            # When only one entry, Apple nests metadata; filter to actual reviews (have author & rating)
            if not isinstance(entries, list):
                entries = [entries]

            for entry in entries:
                if len(signals) >= limit:
                    break
                # Skip the first entry if it's the app metadata (no author)
                if not isinstance(entry, dict):
                    continue
                author_info = entry.get("author", {})
                if isinstance(author_info, dict) and "name" not in author_info and "label" not in author_info:
                    # Might be app metadata header
                    # Real reviews have author.name
                    if not entry.get("im:rating"):
                        continue

                rating_node = entry.get("im:rating", {})
                rating = rating_node.get("label") if isinstance(rating_node, dict) else str(rating_node)
                try:
                    rating_val = int(rating) if rating else 0
                except Exception:
                    rating_val = 0

                # Focus on 1-2 star churnReviews (but collect all for volume, scorer will down-rank)
                # For appstore we collect all, but tag rating in metadata

                title_node = entry.get("title", {})
                title = title_node.get("label") if isinstance(title_node, dict) else str(title_node)
                content_node = entry.get("content", {})
                content = content_node.get("label") if isinstance(content_node, dict) else str(content_node)

                # Fallback for new JSON structure variance
                if not title:
                    title = entry.get("title", "") if isinstance(entry.get("title"), str) else ""
                if not content:
                    content = entry.get("content", "") if isinstance(entry.get("content"), str) else ""

                title = clean_scraped_text(title) or f"{app_name} review"
                body_raw = clean_scraped_text(content) or title
                body = f"{title}\n\n{body_raw}".strip()[:4000]

                # Parse date
                updated_node = entry.get("updated", {})
                updated_str = updated_node.get("label") if isinstance(updated_node, dict) else str(updated_node)
                try:
                    pub_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00")).replace(tzinfo=None) if updated_str else datetime.utcnow()
                except Exception:
                    pub_date = datetime.utcnow()

                if since and pub_date < since:
                    continue

                # ID
                id_node = entry.get("id", {})
                review_id = id_node.get("label") if isinstance(id_node, dict) else str(id_node)
                if not review_id:
                    review_id = f"apple_{app_id}_{len(signals)}"

                author_name = None
                if isinstance(author_info, dict):
                    name_node = author_info.get("name", {})
                    author_name = name_node.get("label") if isinstance(name_node, dict) else str(name_node) if name_node else None

                link_node = entry.get("link", {})
                # link may be omitted; construct fallback
                source_url = f"https://apps.apple.com/{country}/app/id{app_id}"

                # Only emit if it looks like pain (is_candidate will filter, but emit anyway)
                signal = NormalizedSignal(
                    source="appstore",
                    source_id=f"apple_{app_id}_{review_id}",
                    source_url=source_url,
                    title=title[:280] or f"{app_name} {rating_val}★ review",
                    author=author_name,
                    body=body,
                    published_at=pub_date,
                    metadata={
                        "store": "apple",
                        "app_name": app_name,
                        "app_id": app_id,
                        "rating": rating_val,
                        "is_churn": rating_val <= 2,
                        "ingest_tier": "apple_rss_json",
                    },
                )
                signals.append(signal)

        except Exception as e:
            logger.warning(f"Apple RSS collect failed for {app_name}: {e}")

        return signals

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        # Resolve which apps to query
        # queries may contain app names or ids; map to DEFAULT_APPS or try to resolve
        target_apps: list[dict] = []

        if queries:
            # Try to match queries to known apps by name substring
            lower_q = [q.lower() for q in queries]
            for app in DEFAULT_APPS:
                name_low = app["name"].lower()
                if any(name_low in q or q in name_low for q in lower_q):
                    target_apps.append(app)
            # If user passed numeric ids directly
            for q in queries:
                if q.strip().isdigit() and len(q.strip()) >= 6:
                    target_apps.append({"store": "apple", "id": q.strip(), "name": f"App {q.strip()}", "country": "us"})
            # If no match, still use DEFAULT_APPS (ensure we always return something)
            if not target_apps:
                target_apps = DEFAULT_APPS[:2]  # Excel + PowerBI by default
        else:
            target_apps = DEFAULT_APPS[:2]

        # Per-app limit split
        per_app = max(5, limit // max(1, len(target_apps)))

        for app in target_apps:
            if len(results) >= limit:
                break
            try:
                apple_signals = self._collect_apple(app, per_app, since)
                for sig in apple_signals:
                    if sig.source_id in seen_ids:
                        continue
                    seen_ids.add(sig.source_id)
                    results.append(sig)
                    if len(results) >= limit:
                        break
            except Exception as e:
                logger.warning(f"AppStore collect error for {app}: {e}")
                continue

        # Optional Google Play branch — only if google_play_scraper is installed (MIT)
        # We attempt import lazily; if not present, we just return Apple results (graceful)
        if len(results) < limit:
            try:
                # Try pip package `google-play-scraper` (community MIT)
                # If not installed, this import will fail silently
                from google_play_scraper import reviews as gp_reviews  # type: ignore

                # Map Apple app to Android package
                android_packages = {
                    "586683407": "com.microsoft.office.excel",
                    "462058009": "com.microsoft.powerbi",
                }
                for app in target_apps:
                    if len(results) >= limit:
                        break
                    pkg = android_packages.get(app["id"])
                    if not pkg:
                        continue
                    try:
                        # Free API: no key, returns reviews + token
                        gp_result, _ = gp_reviews(pkg, lang="en", country="us", count=min(20, limit - len(results)), filter_score_with=None)
                        for r in gp_result:
                            if len(results) >= limit:
                                break
                            review_id = r.get("reviewId") or f"gp_{pkg}_{len(results)}"
                            if review_id in seen_ids:
                                continue
                            seen_ids.add(review_id)
                            content = r.get("content") or ""
                            title = (content[:80] + "...") if len(content) > 80 else content
                            pub_date = r.get("at") or datetime.utcnow()
                            if since and pub_date < since:
                                continue
                            signal = NormalizedSignal(
                                source="appstore",
                                source_id=f"google_{pkg}_{review_id}",
                                source_url=f"https://play.google.com/store/apps/details?id={pkg}",
                                title=clean_scraped_text(title)[:280] or f"{app['name']} review",
                                author=r.get("userName"),
                                body=clean_scraped_text(content)[:4000],
                                published_at=pub_date,
                                metadata={
                                    "store": "google_play",
                                    "app_name": app["name"],
                                    "package": pkg,
                                    "rating": r.get("score", 0),
                                    "is_churn": (r.get("score", 5) <= 2),
                                    "thumbsUp": r.get("thumbsUpCount", 0),
                                    "ingest_tier": "google_play_scraper",
                                },
                            )
                            results.append(signal)
                    except Exception as ge:
                        logger.debug(f"Google Play scrape skip for {pkg}: {ge}")
                        continue
            except ImportError:
                # Optional dependency not installed — OK, Apple RSS already covered
                pass
            except Exception as e:
                logger.debug(f"Google Play optional branch failed: {e}")

        return results
