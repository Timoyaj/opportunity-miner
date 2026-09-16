---
name: opportunity-scorer
description: Applies the deterministic mathematical scoring rubric (out of 100) and classifies evidence strength (Levels 1 to 5).
---

# Opportunity Scorer Skill

Executes the pure Python deterministic scoring formula.

## 100-Point Formula:
- **Pain Score**: Up to 25 pts (severity, financial loss, hours wasted)
- **Frequency Score**: Up to 15 pts (daily/continuous cadence)
- **Willingness to Pay**: Up to 20 pts (explicit budget, actively seeking help, paying for workaround)
- **Market Recurrence**: Up to 15 pts (cluster mention volume across sources)
- **Technical Feasibility**: Up to 15 pts (Python, API, pandas suitability)
- **Founder Skill Fit**: Up to 10 pts (match with target capability profile)

The scoring is 100% auditable and reproducible without LLM temperature drift.
