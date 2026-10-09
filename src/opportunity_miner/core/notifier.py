"""Free OSS notifier — Apprise (MIT) + ntfy (Apache-2.0) + Gotify (MIT) + webhooks.

All pip-installable from pypi.org, no paid SendGrid/Mailgun/Slack paid plan required.

Providers:
  - Apprise (MIT): 80+ services via one API — Telegram, Discord, Slack, email, etc.
    `pip install apprise` -> apprise.Apprise().add("tgram://bot_token/chat_id")
  - ntfy (Apache-2.0): self-hosted `docker run binwiederhier/ntfy serve` + `curl -d msg ntfy.sh/topic`
  - Gotify (MIT): self-hosted `gotify/server`
  - Raw webhooks: Discord, Slack, Mattermost, Zulip via plain POST

Env:
  NOTIFY_URLS = comma-separated Apprise URLs (e.g., "tgram://xxx,discord://yyy")
  NTFY_TOPIC  = https://ntfy.sh/opportunityminer  (or self-hosted http://localhost/ntfy_topic)
  GOTIFY_URL / GOTIFY_TOKEN
  SLACK_WEBHOOK_URL, DISCORD_WEBHOOK_URL (plain)
"""

import logging
import os
import requests

logger = logging.getLogger(__name__)


class Notifier:
    """Send OpportunityMiner alerts via free OSS channels."""

    def __init__(self, apprise_urls: str | None = None, ntfy_topic: str | None = None):
        self.apprise_urls = apprise_urls or os.environ.get("NOTIFY_URLS") or ""
        self.ntfy_topic = ntfy_topic or os.environ.get("NTFY_TOPIC") or ""
        self.slack_webhook = os.environ.get("SLACK_WEBHOOK_URL") or ""
        self.discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL") or ""
        self.gotify_url = os.environ.get("GOTIFY_URL") or ""
        self.gotify_token = os.environ.get("GOTIFY_TOKEN") or ""

    def send(self, title: str, body: str, priority: str = "default") -> dict[str, bool]:
        """Broadcast to all configured free endpoints. Returns {provider: success}."""
        results: dict[str, bool] = {}

        # 1. Apprise (MIT) — covers 80+ services if installed
        if self.apprise_urls:
            try:
                import apprise  # type: ignore

                apobj = apprise.Apprise()
                for url in [u.strip() for u in self.apprise_urls.split(",") if u.strip()]:
                    apobj.add(url)
                ok = apobj.notify(title=title, body=body)
                results["apprise"] = bool(ok)
            except ImportError:
                logger.warning("Apprise not installed — pip install apprise (MIT) for 80+ providers")
                results["apprise"] = False
            except Exception as e:
                logger.debug(f"Apprise notify failed: {e}")
                results["apprise"] = False

        # 2. ntfy (Apache-2.0) — simplest free push (self-hosted or ntfy.sh)
        if self.ntfy_topic:
            try:
                # ntfy_topic can be full URL https://ntfy.sh/mytopic or host/topic
                url = self.ntfy_topic if self.ntfy_topic.startswith("http") else f"https://ntfy.sh/{self.ntfy_topic}"
                resp = requests.post(
                    url,
                    data=body.encode("utf-8"),
                    headers={"Title": title[:60], "Priority": priority, "Tags": "rocket,money_bag"},
                    timeout=6,
                )
                results["ntfy"] = resp.status_code in (200, 204)
            except Exception as e:
                logger.debug(f"ntfy notify failed: {e}")
                results["ntfy"] = False

        # 3. Slack webhook (free Incoming Webhooks)
        if self.slack_webhook:
            try:
                resp = requests.post(self.slack_webhook, json={"text": f"*{title}*\n{body}"}, timeout=6)
                results["slack"] = resp.status_code == 200
            except Exception as e:
                logger.debug(f"Slack webhook failed: {e}")
                results["slack"] = False

        # 4. Discord webhook (free)
        if self.discord_webhook:
            try:
                resp = requests.post(self.discord_webhook, json={"content": f"**{title}**\n{body[:1800]}"}, timeout=6)
                results["discord"] = resp.status_code in (200, 204)
            except Exception as e:
                logger.debug(f"Discord webhook failed: {e}")
                results["discord"] = False

        # 5. Gotify (MIT, self-hosted)
        if self.gotify_url and self.gotify_token:
            try:
                resp = requests.post(
                    f"{self.gotify_url.rstrip('/')}/message",
                    params={"token": self.gotify_token},
                    json={"title": title, "message": body, "priority": 5},
                    timeout=6,
                )
                results["gotify"] = resp.status_code == 200
            except Exception as e:
                logger.debug(f"Gotify notify failed: {e}")
                results["gotify"] = False

        if not results:
            logger.info("Notifier: no endpoints configured — set NTFY_TOPIC, NOTIFY_URLS, or webhook envs (all free OSS)")
            results["noop"] = True

        return results

    def notify_new_opportunity(self, opp_id: str, title: str, score: float, evidence_level: int) -> dict[str, bool]:
        """Helper for pipeline: formats a new opportunity alert."""
        body = (
            f"New commercial opportunity detected!\n"
            f"ID: {opp_id}\nTitle: {title}\nScore: {int(score)}/100 | Evidence L{evidence_level}/5\n"
            f"View in CRM: `opportunity-miner scan` or Streamlit dashboard"
        )
        prio = "high" if score >= 75 else "default"
        return self.send(title=f"🎯 {opp_id} — {int(score)}/100", body=body, priority=prio)
