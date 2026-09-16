# Antigravity Build Specification: OpportunityMiner AI Skill Package (Enhanced v2.0)

## 1. Project name

**OpportunityMiner AI**

### Purpose

Build an autonomous, evidence-driven **problem discovery and opportunity intelligence system** that continuously searches public online communities and freelance marketplaces for people expressing:

* business problems
* repetitive workflows
* data-analysis needs
* reporting problems
* spreadsheet problems
* automation requirements
* software requests
* missing functionality
* AI opportunities
* API/integration requirements
* requests for freelance/technical assistance

The system must transform these raw signals into **structured, deduplicated, clustered, and deterministically scored commercial opportunities** that the user can investigate, offer as a service, or convert into software/SaaS products.

The system is **not an idea generator**. It must prioritize **verifiable, real-world evidence of existing problems**.

---

# 2. Primary objective

Every scheduled execution should attempt to produce approximately:

**10–20 high-quality opportunities per day**

from a substantially larger pool of discovered signals through a cost-controlled, multi-stage filtration funnel:

```text
1,000–3,000 Raw Ingested Posts
        ↓  (SHA-256 Content Hash Deduplication)
800–1,500 Unique Signals
        ↓  (Regex & Lexical Keyword Pre-Filter - Zero Cost)
150–300 Candidate Signals
        ↓  (Local Embedding Negative-Niche Filter - Near Zero Cost)
50–100 Vetted Signals
        ↓  (Batch LLM Problem & Evidence Extraction)
20–50 Extracted Problems
        ↓  (Centroid-Based Incremental Clustering & Deterministic Scoring)
10–20 High-Value Commercial Opportunities
```

The exact number may vary depending on source availability.

The system must **never fabricate missing evidence simply to reach 10–20 opportunities**. If only 7 opportunities meet the quality and evidence threshold, report 7.

---

# 3. Target user profile

Optimize recommendations for a technical entrepreneur with expertise in:

* Python
* pandas
* NumPy
* SQL
* statistics
* machine learning
* data analysis
* data visualization
* Streamlit
* Dash/Plotly
* APIs
* automation
* AI/LLM applications
* survey/statistical analysis

The system should therefore give additional relevance to problems that can realistically be solved using these capabilities.

However, do not artificially force every problem into a Python/data-science solution.

---

# 4. Core principle

The system must maintain strict architectural separation between four distinct layers:

### Evidence
What a real person actually said/requested (exact quotes, source URLs, timestamps, metadata).

### Interpretation
What the system objectively infers the underlying business problem is (clearly tagged as `INFERRED`).

### Proposed solution
What could realistically solve it (technical stack, MVP scope, complexity).

### Commercial hypothesis
Why the solution is monetizable (willingness to pay, target customer, packaging model).

**These must never be conflated or hallucinated.**

---

# 5. Dual-Layer Architecture: Antigravity Skills & Python Engine

The project is structured into two complementary layers:
1. **Antigravity Skills (`.agents/skills/`)**: Markdown-defined agent workflows and decision protocols that orchestrate tasks, formulate hypotheses, and present insights in the IDE.
2. **Core Python Runtime (`src/opportunity_miner/`)**: A fast, deterministic CLI and library managing data models, scraping, vector stores, clustering math, and UI.

```text
OpportunityMiner/
├── .agents/
│   ├── agents/
│   │   └── opportunity-researcher/
│   │       └── agent.md                      # Master agent persona & tools
│   └── skills/
│       ├── opportunity-orchestrator/SKILL.md # Master pipeline controller
│       ├── source-reddit/SKILL.md            # Reddit ingestion & parsing
│       ├── source-hackernews/SKILL.md        # Algolia HN API scraper
│       ├── source-upwork/SKILL.md            # RSS/Job feed extractor
│       ├── source-indiehackers/SKILL.md      # IH pain crawler
│       ├── source-producthunt/SKILL.md       # PH review & gap parser
│       ├── problem-extractor/SKILL.md        # Pydantic problem extraction
│       ├── problem-deduplicator/SKILL.md     # Lexical & embedding dedup
│       ├── opportunity-clusterer/SKILL.md    # Incremental centroid clustering
│       ├── opportunity-scorer/SKILL.md       # Deterministic Python scoring
│       ├── solution-designer/SKILL.md        # Technical spec & offer ladder
│       ├── competitor-researcher/SKILL.md    # Alternative & gap researcher
│       ├── validation-planner/SKILL.md       # Discovery interview planner
│       └── daily-opportunity-report/SKILL.md # Markdown & JSON generator
│
├── config/
│   ├── sources.yaml                          # Communities, subreddits, feeds
│   ├── keywords.yaml                         # Pain, automation, and WTP keywords
│   ├── scoring.yaml                          # Weightings and rubric caps
│   ├── profile.yaml                          # User skills and tech stack weights
│   └── settings.yaml                         # LLM, DB, and embedding configs
│
├── src/
│   └── opportunity_miner/
│       ├── __init__.py
│       ├── cli.py                            # CLI command interface
│       ├── adapters/                         # Pluggable source adapters
│       │   ├── base.py
│       │   ├── reddit_adapter.py
│       │   ├── hackernews_adapter.py
│       │   ├── upwork_adapter.py
│       │   ├── indiehackers_adapter.py
│       │   └── producthunt_adapter.py
│       ├── core/
│       │   ├── prefilter.py                  # Regex & keyword pruning
│       │   ├── extractor.py                  # LLM structured extraction
│       │   ├── vector_store.py               # Local FastEmbed & similarity
│       │   ├── clusterer.py                  # Incremental centroid engine
│       │   └── scoring.py                    # Deterministic mathematical rubric
│       ├── database/
│       │   ├── models.py                     # SQLAlchemy 3NF models
│       │   └── session.py                    # SQLite/PostgreSQL engine
│       ├── generators/
│       │   ├── outreach_generator.py         # Consultative message drafter
│       │   ├── solution_hypotheses.py        # Technical spec generator
│       │   └── report_generator.py           # Daily markdown/JSON outputs
│       └── ui/
│           └── app.py                        # Streamlit CRM & explorer
│
├── data/
│   ├── raw/                                  # Cached source dumps
│   ├── opportunity_miner.db                  # Local SQLite database
│   └── vectors/                              # Local vector index
├── reports/
│   └── 2026/09/
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

---

# 6. Master Orchestrator Pipeline

The `opportunity-orchestrator` coordinates the end-to-end execution flow:

```text
1. SOURCE INGESTION
   ├── Reddit (OAuth API / JSON / RSS)
   ├── Hacker News (Algolia Search API)
   ├── Upwork (Public RSS / JSON Import)
   ├── Indie Hackers (Feed / Search Index)
   └── Product Hunt (GraphQL API v2 / Atom)
       ↓
2. STAGE 1 PRE-FILTERING (Zero Token Cost)
   ├── Content Hashing (SHA-256 exact dedup)
   └── Regex Trie Keyword Matching (Pain + Domain keywords)
       ↓
3. STAGE 2 VECTOR PRE-FILTERING (Local Embeddings)
   └── Negative Niche Cosine Pruning (Drop user-rejected vectors)
       ↓
4. PROBLEM & EVIDENCE EXTRACTION (LLM Batch)
   └── Pydantic Schema Validation (Strict JSON extraction)
       ↓
5. INCREMENTAL CENTROID CLUSTERING
   ├── Match to Existing Cluster Centroids (Cosine > 0.82)
   └── Form New Clusters (Min 3 candidate threshold)
       ↓
6. DETERMINISTIC OPPORTUNITY SCORING (Pure Python Math)
   ├── Pain (25 pts) + Frequency (15 pts) + Willingness-to-Pay (20 pts)
   └── Recurrence (15 pts) + Feasibility (15 pts) + User Fit (10 pts)
       ↓
7. SOLUTION DESIGN & COMMERCIAL PACKAGING
   ├── Technical Architecture & MVP Scope
   ├── 3-Stage Offer Ladder (Service → Retainer → Micro-SaaS)
   └── Consultative Discovery Message Draft
       ↓
8. COMPETITIVE & VALIDATION RESEARCH
   ├── Competitor Gap Matrix
   └── 5-Question Customer Discovery Plan
       ↓
9. PERSISTENCE & REPORT GENERATION
   ├── Write to Relational Database
   ├── Output Markdown & JSON Reports
   └── Sync to Streamlit CRM
```

---

# 7. Source Coverage & Anti-Ban Ingestion Strategy

To ensure zero downtime, prevent IP blocks, and avoid brittle scraping, all source adapters implement resilient fallback tiers:

### 1. Hacker News Adapter (`hackernews_adapter.py`)
* **Primary Tier:** **Algolia HN Search API** (`https://hn.algolia.com/api/v1/search_by_date`).
* **Authentication:** None required (100% public, free, fast, zero rate limit friction).
* **Queries:** `tags=ask_hn`, `tags=show_hn`, and query terms: `"manual"`, `"automate"`, `"spreadsheet"`, `"looking for tool"`.

### 2. Reddit Adapter (`reddit_adapter.py`)
* **Tier 1:** Official Reddit API via `praw` (Client ID + Secret + Script User-Agent).
* **Tier 2 (Fallback):** Public `.json` endpoints (e.g. `https://www.reddit.com/r/excel/new.json?limit=100`) with customized descriptive `User-Agent`.
* **Tier 3 (Fallback):** Reddit Subreddit RSS Feeds (`https://www.reddit.com/r/excel/new/.rss`).
* **Target Subreddits:**
  ```text
  r/smallbusiness, r/Entrepreneur, r/startups, r/SaaS, r/indiehackers,
  r/SideProject, r/freelance, r/dataanalysis, r/datascience, r/excel,
  r/PowerBI, r/SQL, r/BusinessIntelligence, r/Statistics, r/learnpython
  ```

### 3. Upwork Adapter (`upwork_adapter.py`)
* **Constraint:** Upwork enforces strict Cloudflare anti-bot checks on interactive search. Direct unauthorized web scraping is forbidden.
* **Tier 1:** Upwork Public Job Search RSS Feeds (e.g., `https://www.upwork.com/ab/feed/jobs/rss?q=python+automation&sort=recency`).
* **Tier 2:** Structured JSON Dropzone (`data/imports/upwork/`): allows automated imports from verified API integrations, MCP browser sidecars, or user-provided exports.
* **Signals:** Job title, client spend tier, payment verification status, stated budget, skills required.

### 4. Indie Hackers Adapter (`indiehackers_adapter.py`)
* **Tier 1:** Public community RSS feeds and search syndication APIs.
* **Tier 2:** Search API syndication via Google search operators (`site:indiehackers.com "tedious" OR "manual"`).

### 5. Product Hunt Adapter (`producthunt_adapter.py`)
* **Tier 1:** Official Product Hunt GraphQL API v2 using developer token.
* **Tier 2:** Product Hunt Atom / RSS feeds.
* **Focus:** Negative reviews, product comments starting with *"This product is good, but..."* or requests for integrations and alternatives.

---

# 8. Keyword Matrix (`config/keywords.yaml`)

Keyword matching operates as a fast lexical sieve before LLM processing:

```yaml
pain_keywords:
  - "manual"
  - "manually"
  - "tedious"
  - "frustrating"
  - "time consuming"
  - "takes hours"
  - "takes days"
  - "waste time"
  - "repetitive"
  - "nightmare"
  - "struggle"
  - "bottleneck"
  - "error prone"

automation_keywords:
  - "automate"
  - "automation"
  - "script"
  - "workflow"
  - "API"
  - "integration"
  - "Excel"
  - "spreadsheet"
  - "CSV"
  - "copy paste"
  - "reporting"
  - "Google Sheets"

demand_keywords:
  - "looking for"
  - "need a tool"
  - "need software"
  - "is there a tool"
  - "is there an app"
  - "does anyone know"
  - "wish there was"
  - "alternative to"
  - "looking for someone"
  - "need help"
  - "would pay"
  - "budget"
  - "hire"

data_keywords:
  - "dashboard"
  - "analytics"
  - "report"
  - "KPI"
  - "data cleaning"
  - "data analysis"
  - "visualization"
  - "forecast"
  - "prediction"
  - "SQL"
  - "Power BI"
  - "ETL"
  - "pipeline"
```

---

# 9. Source Adapter Base Interface (`adapters/base.py`)

Every adapter must inherit from this strict contract:

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from pydantic import BaseModel

class NormalizedSignal(BaseModel):
    source: str
    source_id: str
    source_url: str
    title: str
    author: str | None
    body: str
    published_at: datetime
    metadata: dict[str, Any] = {}

class SourceAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def health_check(self) -> tuple[bool, str]:
        """Returns (is_available, status_message)"""
        pass

    @abstractmethod
    def collect(self, queries: list[str], since: datetime | None = None) -> list[NormalizedSignal]:
        """Collects and returns standardized signals without crashing on network errors"""
        pass
```

---

# 10. Normalized Relational Database Schema (`models.py`)

The system stores all state in a **3NF relational database** (SQLite by default, PostgreSQL-compatible via SQLAlchemy):

```text
┌─────────────────┐
│   RawSignal     │ (Raw ingested post/job/comment)
└────────┬────────┘
         │ 1
         │
         ▼ N
┌─────────────────┐
│ ExtractedProblem│ (Atomic problem extracted by LLM)
└────────┬────────┘
         │ N
         │
         ▼ 1
┌─────────────────┐
│ ProblemCluster  │ (Semantic grouping with running centroid)
└────────┬────────┘
         │ 1
         │
         ▼ 1
┌─────────────────┐       ┌─────────────────┐
│   Opportunity   ├──────►│  UserFeedback   │ (Explicit CRM actions & negative labels)
└────┬───────┬────┘       └─────────────────┘
     │ 1     │ 1
     ▼ N     ▼ N
┌──────────┐ ┌────────────────┐
│Competitor│ │ ValidationPlan │
└──────────┘ └────────────────┘
```

### Table Definitions:

1. **`raw_signals`**:
   * `id` (VARCHAR PK): `sha256(source + source_id)`
   * `source` (VARCHAR): e.g. `reddit`, `hackernews`, `upwork`
   * `source_url` (VARCHAR UNIQUE)
   * `author` (VARCHAR, NULLABLE)
   * `title` (TEXT)
   * `body` (TEXT)
   * `published_at` (TIMESTAMP)
   * `collected_at` (TIMESTAMP)
   * `content_hash` (VARCHAR INDEX): `sha256(body)`
   * `raw_metadata` (JSON): upvotes, score, subreddit, budget

2. **`extracted_problems`**:
   * `id` (VARCHAR PK): `PR-XXXX`
   * `signal_id` (VARCHAR FK -> `raw_signals.id`)
   * `problem_statement` (TEXT): What the person is trying to do
   * `underlying_problem` (TEXT): Root cause / business bottleneck
   * `target_customer` (VARCHAR): e.g., "B2B SaaS Founder", "Operations Manager"
   * `current_workaround` (TEXT): Workaround or tool in use
   * `pain_evidence` (JSON): Array of exact quotes demonstrating pain
   * `frequency_evidence` (VARCHAR): `daily`, `weekly`, `monthly`, etc.
   * `wtp_evidence` (JSON): Quotes referencing spend, budget, or hiring
   * `embedding` (BLOB): 384-dimensional vector (`all-MiniLM-L6-v2`)
   * `cluster_id` (VARCHAR FK -> `problem_clusters.id`, NULLABLE)

3. **`problem_clusters`**:
   * `id` (VARCHAR PK): `CL-XXXX`
   * `title` (VARCHAR): e.g., "Multi-Store Shopify Inventory Syncing"
   * `description` (TEXT)
   * `centroid_embedding` (BLOB): Running mean vector of member problems
   * `mention_count` (INTEGER): Total linked problems
   * `unique_sources` (INTEGER)
   * `first_seen_at` (TIMESTAMP)
   * `last_seen_at` (TIMESTAMP)
   * `trend_velocity` (FLOAT): Mentions per week

4. **`opportunities`**:
   * `id` (VARCHAR PK): `OP-XXXX`
   * `cluster_id` (VARCHAR FK -> `problem_clusters.id`, UNIQUE)
   * `title` (VARCHAR)
   * `category` (VARCHAR): `AUTOMATION_SERVICE`, `DASHBOARD`, `MICRO_SAAS`, etc.
   * `opportunity_score` (FLOAT INDEX): 0.0 – 100.0
   * `confidence_score` (FLOAT): 0.0 – 1.0
   * `evidence_level` (INTEGER): Level 1 – 5
   * `technical_feasibility` (FLOAT): 0.0 – 15.0
   * `user_expertise_fit` (FLOAT): 0.0 – 10.0
   * `score_breakdown` (JSON): Component scores and justifications
   * `solution_hypothesis` (JSON): Tech stack, architecture, MVP scope
   * `commercial_packaging` (JSON): 3-tier offer ladder, consultative message
   * `status` (VARCHAR): `NEW`, `INVESTIGATING`, `VALIDATING`, `REJECTED`, etc.
   * `created_at` (TIMESTAMP)
   * `updated_at` (TIMESTAMP)

5. **`competitors`**:
   * `id` (VARCHAR PK)
   * `opportunity_id` (VARCHAR FK -> `opportunities.id`)
   * `name` (VARCHAR)
   * `url` (VARCHAR, NULLABLE)
   * `pricing_summary` (VARCHAR, NULLABLE)
   * `reported_weakness` (TEXT)

6. **`validation_plans`**:
   * `id` (VARCHAR PK)
   * `opportunity_id` (VARCHAR FK -> `opportunities.id`)
   * `target_interviewees` (TEXT)
   * `qualifying_questions` (JSON)
   * `landing_page_pitch` (TEXT)

7. **`user_feedback`**:
   * `id` (INTEGER PK AUTOINCREMENT)
   * `opportunity_id` (VARCHAR FK -> `opportunities.id`)
   * `action` (VARCHAR): `USEFUL`, `REJECTED`, `TOO_DIFFICULT`, `NOT_MY_NICHE`
   * `notes` (TEXT, NULLABLE)
   * `feedback_timestamp` (TIMESTAMP)

---

# 11. Deduplication & Centroid-Based Incremental Clustering

### Level 1: Exact Duplicate Pruning (Zero Cost)
* Discard immediately if `content_hash` exists in `raw_signals`.

### Level 2: Semantic Deduplication (Local Embeddings)
* Generate embeddings locally using `FastEmbed` (`BAAI/bge-small-en-v1.5` or `all-MiniLM-L6-v2`) with zero external API calls.
* If cosine similarity $> 0.92$ to a problem created within the last 48 hours, append as duplicate evidence to the existing problem.

### Level 3: Incremental Centroid-Based Clustering
1. Compare new problem embedding against active `ProblemCluster.centroid_embedding` vectors.
2. If `cosine_similarity >= 0.82`:
   * Assign problem to that cluster.
   * Update cluster running centroid: $\vec{C}_{new} = \frac{N \cdot \vec{C}_{old} + \vec{P}}{N + 1}$.
   * Increment `mention_count` and update `last_seen_at`.
3. If no cluster matches:
   * Keep problem in `unclustered` state.
   * If $\ge 3$ unclustered problems have mutual cosine similarity $\ge 0.80$, instantiate a new `ProblemCluster (CL-XXXX)`.

---

# 12. Pydantic Extraction Schema (`extractor.py`)

All LLM output must strictly satisfy:

```python
from pydantic import BaseModel, Field
from typing import Literal

class ProblemExtractionResult(BaseModel):
    is_commercial_problem: bool = Field(
        description="True if the author expresses a genuine workflow/business struggle, not casual banter or blog promotion."
    )
    problem_statement: str = Field(
        description="Clear, 1-2 sentence description of what the user is attempting to do."
    )
    underlying_problem: str = Field(
        description="Root business cause or architectural bottleneck."
    )
    target_customer: str = Field(
        description="Role or business type of the person with the problem."
    )
    current_workaround: str | None = Field(
        default=None, description="Tools, spreadsheets, or manual steps currently used."
    )
    
    # Evidence Rubric Flags (For Deterministic Python Scoring)
    frustration_severity: Literal["none", "mild", "severe", "blocking"]
    reports_financial_loss: bool
    reported_hours_lost_per_week: float = 0.0
    frequency_cadence: Literal["unknown", "yearly", "monthly", "weekly", "daily", "continuous"]
    explicit_budget_stated: float | None = None
    currently_paying_for_workaround: bool
    actively_seeking_help: bool
    
    # Exact Verbatim Quotes
    pain_quotes: list[str] = Field(default_factory=list)
    payment_quotes: list[str] = Field(default_factory=list)
    confidence_rating: float = Field(ge=0.0, le=1.0)
```

---

# 13. Deterministic Opportunity Scoring Engine (`scoring.py`)

$$\text{Opportunity Score} = \text{Pain} + \text{Frequency} + \text{WTP} + \text{Recurrence} + \text{Feasibility} + \text{User Fit} \quad (\text{Max: } 100)$$

```python
def calculate_score(extraction: ProblemExtractionResult, cluster: ProblemCluster, user_skills: list[str]) -> tuple[float, dict]:
    # 1. Pain Score (Max 25 pts)
    pain = 0.0
    if extraction.frustration_severity == "blocking": pain += 12.0
    elif extraction.frustration_severity == "severe": pain += 8.0
    elif extraction.frustration_severity == "mild": pain += 4.0
    
    if extraction.reports_financial_loss: pain += 8.0
    if extraction.reported_hours_lost_per_week >= 5.0: pain += 5.0
    elif extraction.reported_hours_lost_per_week > 0: pain += 2.0
    pain = min(25.0, pain)

    # 2. Frequency Score (Max 15 pts)
    freq_weights = {
        "continuous": 15.0, "daily": 15.0, "weekly": 12.0,
        "monthly": 7.0, "yearly": 2.0, "unknown": 1.0
    }
    frequency = freq_weights.get(extraction.frequency_cadence, 1.0)

    # 3. Willingness to Pay (Max 20 pts)
    wtp = 0.0
    if extraction.explicit_budget_stated and extraction.explicit_budget_stated >= 100:
        wtp += 12.0
    elif extraction.actively_seeking_help:
        wtp += 8.0
    if extraction.currently_paying_for_workaround:
        wtp += 8.0
    wtp = min(20.0, wtp)

    # 4. Market Recurrence (Max 15 pts)
    if cluster.mention_count >= 10: recurrence = 15.0
    elif cluster.mention_count >= 5: recurrence = 11.0
    elif cluster.mention_count >= 2: recurrence = 7.0
    else: recurrence = 3.0

    # 5. Technical Feasibility (Max 15 pts)
    feasibility = 13.0

    # 6. User Fit (Max 10 pts)
    fit = 9.0

    total_score = round(pain + frequency + wtp + recurrence + feasibility + fit, 1)
    
    breakdown = {
        "pain": pain, "frequency": frequency, "willingness_to_pay": wtp,
        "market_recurrence": recurrence, "technical_feasibility": feasibility,
        "user_fit": fit
    }
    return total_score, breakdown
```

### Evidence Strength Classification:
```text
LEVEL 1: Single mention, isolated complaint.
LEVEL 2: Multiple mentions (>= 2) across independent users.
LEVEL 3: Repeated complaints with documented workarounds.
LEVEL 4: Active evidence of existing spending on tools/services.
LEVEL 5: Explicit stated budget or direct request to hire/buy.
```

---

# 14. Commercial Action Assets & Solution Design

For every opportunity scoring $\ge 70$, automatically generate:

1. **3-Stage Offer Ladder:**
   * **Stage 1 (Foot-in-the-Door Service):** High-speed scripted fix ($250 one-time).
   * **Stage 2 (Retainer Automation):** Managed recurring pipeline ($500–$1,000/month).
   * **Stage 3 (Productized Micro-SaaS):** Multi-tenant web portal ($49/month).
2. **Consultative Discovery Message:**
   Empathetic, non-spammy outreach referencing their exact workaround and offering a 2-minute diagnostic breakdown.
3. **Technical MVP Architecture:**
   Core components, integration dependencies, estimated hours to build.

---

# 15. User Feedback & Negative Vector Blacklist

When an opportunity is marked `NOT_MY_NICHE` or `REJECTED`:
1. Its embedding is saved to `data/vectors/negative_blacklist.npy`.
2. Any new candidate signal with **cosine similarity $> 0.85$** to a blacklisted vector is automatically pruned in Stage 2, preventing token waste on recurring unwanted topics.

---

# 16. Streamlit Dashboard & CRM (`ui/app.py`)

A high-density Streamlit application featuring:
* **Dashboard View:** Real-time funnel metrics, source health checks, score distributions.
* **Opportunity CRM:** Kanban board tracking (`NEW` $\to$ `INVESTIGATING` $\to$ `VALIDATING` $\to$ `PROTOTYPING` $\to$ `PAID_PROJECT` $\to$ `REJECTED`).
* **Opportunity Dossier:** Score breakdown gauges, verbatim quotes with backlinks, 3-tier offer ladder, and copyable outreach templates.
* **Cluster Explorer:** Timeline trend graphs, user volume, and cross-platform recurrence.

---

# 17. Daily Intelligence Briefing (`reports/YYYY/MM/YYYY-MM-DD.md`)

Saved daily in both Markdown and structured JSON:
* Source Health & Coverage Table (Complete, Partial, Unavailable).
* Funnel Ingestion Statistics.
* Ranked Top 10–20 Opportunities with score breakdowns, verbatim evidence excerpts, and commercial roadmaps.

---

# 18. Command Line Interface (CLI)

```bash
# Ingest and scan all active sources
opportunity-miner scan --sources all

# Incremental scan
opportunity-miner scan --sources hackernews,reddit --since 24h

# Recompute clusters and score
opportunity-miner cluster --recalculate
opportunity-miner score --min-score 70

# Launch Streamlit CRM
opportunity-miner ui --port 8501

# Generate Daily Briefing
opportunity-miner report --date today --format md,json
```

---

# 19. Definition of Done

The build is considered complete only when:
1. All 14 Antigravity skills in `.agents/skills/` and the complete `src/opportunity_miner/` Python package are implemented.
2. Hacker News Algolia and Reddit JSON adapters run with zero authentication required.
3. 3NF SQLite database initializes and persists state across executions.
4. Scoring math is 100% deterministic in Python.
5. Incremental clustering maintains centroid stability across multiple runs.
6. Negative feedback vectors actively suppress unwanted niches.
7. Streamlit CRM allows real-time status transitions.
8. Synthetic tests pass.

---

# 20. Implementation Phases

```text
PHASE 1: Core Foundation (DB schema, configs, CLI skeleton)
PHASE 2: Resilient Source Ingestion (HN Algolia, Reddit, Upwork RSS)
PHASE 3: Filtering & Problem Extraction (Regex pre-filter, Pydantic extractor)
PHASE 4: Clustering & Scoring Engine (Centroid clusterer, deterministic math)
PHASE 5: Commercial Generators (Offer ladder, outreach drafter, competitor research)
PHASE 6: Streamlit CRM Dashboard (Kanban board, dossier view)
PHASE 7: Antigravity Skills & Reporting (14 SKILL.md manifests, daily reports)
PHASE 8: Testing & Verification (Synthetic fixtures, negative blacklist tests)
```
