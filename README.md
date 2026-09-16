# OpportunityMiner AI 🎯

Autonomous, evidence-driven problem discovery and commercial opportunity intelligence system.

OpportunityMiner scans public communities (Reddit, Hacker News, Upwork, Indie Hackers, Product Hunt), filters noise via regex and embeddings, extracts commercial problems using Pydantic schemas, clusters problems via centroid matching, scores opportunities deterministically in Python, and packages commercial action assets (3-stage offer ladder + consultative outreach drafts).

---

## Quick Start

### 1. Installation

```bash
cd C:\Users\USER\.gemini\antigravity-ide\scratch\opportunity-miner
pip install -e .
```

Or install dependencies directly:
```bash
pip install -r requirements.txt
```

### 2. Run Diagnostics & Ingest Signals

```bash
# Check status of public data feeds (Hacker News Algolia, Reddit, Upwork RSS)
python -m opportunity_miner.cli health

# Run a live scan across all active sources
python -m opportunity_miner.cli scan --sources all --limit 25
```

### 3. Generate Daily Intelligence Briefing

```bash
python -m opportunity_miner.cli report
```
Reports are stored in `reports/YYYY/MM/` as human-readable Markdown and structured JSON.

### 4. Launch Interactive Streamlit CRM

```bash
streamlit run src/opportunity_miner/ui/app.py
```
Or via CLI:
```bash
python -m opportunity_miner.cli ui
```

---

## System Architecture

```text
1,000+ Raw Signals (Hacker News, Reddit, Upwork, Indie Hackers, Product Hunt)
        ↓
Stage 1: SHA-256 Hash Dedup & Regex Trie Pre-Filter (Zero Cost)
        ↓
Stage 2: Local Vector Negative-Niche Filter (Zero Cost)
        ↓
Stage 3: Pydantic Problem & Verbatim Evidence Extraction
        ↓
Stage 4: Incremental Centroid Clustering (Persistent Cluster IDs)
        ↓
Stage 5: Deterministic Python Scoring (0–100 pts & Evidence Levels 1–5)
        ↓
Stage 6: Commercial Action Packaging (3-Stage Offer Ladder & Cold Outreach)
        ↓
Output: SQLite 3NF Database + Daily Reports + Streamlit CRM
```

---

## Directory Structure

```text
opportunity-miner/
├── .agents/
│   ├── agents/
│   │   └── opportunity-researcher/agent.md
│   └── skills/
│       ├── opportunity-orchestrator/SKILL.md
│       ├── source-reddit/SKILL.md
│       ├── source-hackernews/SKILL.md
│       ├── source-upwork/SKILL.md
│       ├── source-indiehackers/SKILL.md
│       ├── source-producthunt/SKILL.md
│       ├── problem-extractor/SKILL.md
│       ├── problem-deduplicator/SKILL.md
│       ├── opportunity-clusterer/SKILL.md
│       ├── opportunity-scorer/SKILL.md
│       ├── solution-designer/SKILL.md
│       ├── competitor-researcher/SKILL.md
│       ├── validation-planner/SKILL.md
│       └── daily-opportunity-report/SKILL.md
├── config/
│   ├── sources.yaml
│   ├── keywords.yaml
│   ├── scoring.yaml
│   ├── profile.yaml
│   └── settings.yaml
├── src/
│   └── opportunity_miner/
│       ├── adapters/
│       ├── core/
│       ├── database/
│       ├── generators/
│       ├── ui/
│       └── cli.py
├── tests/
├── pyproject.toml
└── requirements.txt
```
