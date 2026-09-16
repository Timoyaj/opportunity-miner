---
name: opportunity-orchestrator
description: Coordinates the end-to-end OpportunityMiner pipeline from source collection to daily report generation.
---

# Opportunity Orchestrator

This skill coordinates the full autonomous execution of OpportunityMiner AI.

## Workflow:
1. **Health Verification**: Check adapter availability:
   ```bash
   python -m opportunity_miner.cli health
   ```
2. **Execute Ingestion & Scoring**:
   ```bash
   python -m opportunity_miner.cli scan --sources all
   ```
3. **Generate Intelligence Briefing**:
   ```bash
   python -m opportunity_miner.cli report
   ```
4. **Present Results**: Read the latest report from `reports/YYYY/MM/` and present the top opportunities to the user.
