---
name: source-reddit
description: Collects and normalizes problem signals from Reddit communities (r/excel, r/smallbusiness, r/dataanalysis, etc.) using multi-tier fallback and agent-reach scraping.
---

# Reddit Source Skill

Monitors target subreddits and scrapes genuine user problems, workflow bottlenecks, and tool complaints.

## Scraping & Retrieval Strategy:
1. **Multi-Tier Pipeline**:
   - **Tier 1 (Public Endpoints & RSS)**: Rapid zero-auth ingestion across target subreddits configured in `config/sources.yaml`.
   - **Tier 2 (`agent-reach` Router)**: When deep post threads or comments are needed, leverage the installed `agent-reach` skill (using `opencli reddit` or Jina Reader `curl https://r.jina.ai/<reddit_url>`).
   - **Tier 3 (Clean Text Pipeline)**: Clean HTML entities, unescape Unicode, and strip RSS metadata boilerplate (`submitted by /u/... [link] [comments]`) using `opportunity_miner.core.scraper.clean_scraped_text`.

## Execution Commands:
```bash
# General scan across default subreddits
python -m opportunity_miner.cli scan --sources reddit --limit 25

# Targeted domain and time-filtered scan
python -m opportunity_miner.cli scan --sources reddit --query "excel automation" --days 7 --limit 30
```

## Verbatim Quote Quality Assurance:
- Always preserve exact user quotes containing friction cues ("tedious", "manual", "takes hours", "broken", "formula error", "how do I automate").
- Never allow HTML markup or RSS footer fragments in `pain_evidence` or `body`.
