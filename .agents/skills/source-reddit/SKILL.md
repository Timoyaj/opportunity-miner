---
name: source-reddit
description: Collects and normalizes problem signals from Reddit communities (r/excel, r/smallbusiness, r/dataanalysis, etc.).
---

# Reddit Source Skill

Monitors target subreddits using multi-tier fallback (JSON endpoints -> RSS feeds -> PRAW).

## Usage:
```bash
python -m opportunity_miner.cli scan --sources reddit --limit 25
```
Target communities are configured in `config/sources.yaml`.
All items are parsed into standard `NormalizedSignal` records with upvote and comment telemetry.
