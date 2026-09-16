---
name: daily-opportunity-report
description: Compiles and publishes the daily executive Markdown and JSON intelligence briefings to reports/YYYY/MM/.
---

# Daily Opportunity Report Skill

Generates structured daily intelligence reports.

## Command:
```bash
python -m opportunity_miner.cli report --format md,json
```

Outputs:
- `reports/YYYY/MM/YYYY-MM-DD.md` (Human-readable executive briefing)
- `reports/YYYY/MM/YYYY-MM-DD.json` (Structured data export)

Includes source health coverage, funnel conversion metrics, and ranked top opportunities with complete evidence citations.
