---
name: opportunity-orchestrator
description: Coordinates the end-to-end OpportunityMiner pipeline from source collection to daily report generation, integrating agent-reach scraping and deterministic scoring.
---

# Opportunity Orchestrator

This skill coordinates the full autonomous execution of OpportunityMiner AI.

## Workflow:
1. **Health Verification**: Check adapter availability:
   ```bash
   python -m opportunity_miner.cli health
   ```
2. **Execute Ingestion & Scoring**:
   - Run general scan or domain-targeted query:
   ```bash
   # General scan
   python -m opportunity_miner.cli scan --sources all

   # Domain-focused scan with time window
   python -m opportunity_miner.cli scan --query "excel automation" --days 7 --sources reddit,hackernews,upwork
   ```
3. **Deep Web Scraping via `agent-reach`**:
   - When deeper context on high-value threads or external tool alternatives is required, utilize the installed `agent-reach` skill (e.g. `curl https://r.jina.ai/<URL>` or platform-specific tools) to retrieve full, unblocked page content.
4. **Generate Intelligence Briefing**:
   ```bash
   python -m opportunity_miner.cli report
   ```
5. **Inspect & Manage via CRM**:
   - Launch Streamlit dashboard:
   ```bash
   python -m opportunity_miner.cli ui --port 8501
   ```
   - Verify that all opportunities display **Verbatim Pain Quotes**, **Commercial Quotes**, and **Full Raw Source Excerpts** under the Dossier Detail Evidence Vault.
