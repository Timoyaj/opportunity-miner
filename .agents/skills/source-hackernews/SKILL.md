---
name: source-hackernews
description: Ingests problems, tool requests, and workflow complaints from Hacker News using the Algolia Search API.
---

# Hacker News Source Skill

Leverages the public unauthenticated Algolia HN API (`hn.algolia.com/api/v1/search_by_date`).

## Target Queries:
- `tags=ask_hn`
- `tags=show_hn`
- Keywords: "manual", "automate", "spreadsheet", "looking for tool", "tedious"

## Execution:
```bash
python -m opportunity_miner.cli scan --sources hackernews --limit 30
```
