# OpportunityMiner — 100% FREE & Open-Source Connectors Proposal
*Revised 2026-10-09 per your constraint: $0/month, MIT/Apache/BSD/AGPL only, self-hostable, no per-search fees*

> This replaces the previous paid proposal. Every tool below is OSI-approved, `pip install`able from `pypi.org` or `docker pull`able from `github.com`, and runs forever on your own hardware.

---

## 0. Principles

1.  **No paid API:** No SerpApi, Bright Data, Apify Cloud, Pinecone Cloud, Octolens, Hunters. All replaced by self-hosted OSS.
2.  **Four layers preserved:** Free sources still emit `NormalizedSignal` → same `prefilter → vector_store → clusterer → scorer` pipeline.
3.  **Zero lock-in:** If a SaaS disappears, `docker compose down && docker compose up` restores it. All data stays in `data/`.

---

## 1. Ingestion — Free Public Sources (no keys, or free PAT)

You *keep* HackerNews Algolia, Reddit JSON/RSS, IndieHackers RSS, ProductHunt Atom, Upwork RSS dropzone (all $0). **Add these free endpoints:**

| New Adapter | Free Endpoint | License / Quota | Why it matters |
|---|---|---|---|
| **GitHub Issues** | `https://api.github.com/search/issues?q=manual+automation+excel+tedious` | GitHub REST API, 60/h unauth → 5,000/h with free PAT (create in settings) | Direct developer pain; mined in FL study 9k issues [paper] |
| **Stack Overflow** | `https://api.stackexchange.com/2.3/search/advanced?site=stackoverflow&tagged=excel;python` | Stack Exchange API v3, **10k req/day free, no key** [via `api.stackexchange.com`] | 495 SO posts mapped 9 pain topics — complements GitHub `How` vs `Why` |
| **DEV.to** | `https://dev.to/api/articles?tag=automation&top=7` | MIT, free, no key, `dev.to/api` | Founder complaints, no scraping |
| **Lobste.rs** | `https://lobste.rs/hottest.json` | BSD, free JSON | HN-style but different community |
| **RemoteOK / WeWorkRemotely / Remotive** | `https://remoteok.com/api?tag=excel`, `https://weworkremotely.com/remote-jobs.rss` | Free JSON/RSS | Replaces Upwork Cloudflare blocks for WTP/budget signals |
| **Google Play + App Store Reviews** | `google-play-scraper` (npm MIT) `pip install google-play-scraper` + Apple RSS `https://itunes.apple.com/rss/customerreviews/.../json` | MIT / free | 1-star reviews = churn intelligence, official free feeds — replaces paid G2/Trustpilot scraping |
| **G2 / Capterra / Trustpilot (OSS scrape fallback)** | Self-scrape with **Trafilatura/Crawlee** (see §2) on public review URLs, no Apify | Trafilatura MIT, Crawlee Apache-2.0 | Same 1-2 star churn, but via your own scraper, $0 |

All five fit `SourceAdapter.collect(queries, limit, since)` and `config/sources.yaml` `enabled: true`. Example:

```yaml
# config/sources.yaml — NEW FREE ENTRIES
sources:
  github:
    enabled: true
    adapter: "github"
    queries: ["excel automation tedious", "manual reporting nightmare", "spreadsheet bottleneck"]
    limit: 30
  stackoverflow:
    enabled: true
    adapter: "stackoverflow"
    tags: ["excel", "python", "powerbi", "google-sheets"]
    limit: 25
  devto:
    enabled: true
    adapter: "devto"
    limit: 25
  appstore:
    enabled: true
    adapter: "appstore"
    apps: ["com.microsoft.office.excel", "google.sheets"]
```

---

## 2. Scraping & Cleaning — OSS Stack (replaces Firecrawl / Apify / Bright Data)

| Tool | License | Install | Best for |
|---|---|---|---|
| **Crawlee** | Apache-2.0 [1](https://use-apify.com/blog/best-free-web-scraping-tools-2026) [2](https://reader.dev/blog/best-open-source-web-scraping-tools) | `pip install crawlee` or `npm i crawlee` | Unified HTTP + Playwright crawling, queue, anti-block [1] |
| **Scrapy** | BSD-3-Clause [1](https://use-apify.com/blog/best-free-web-scraping-tools-2026) | `pip install scrapy` | Fast static crawls, Twisted async [1] |
| **BeautifulSoup4** | MIT [2](https://reader.dev/blog/best-open-source-web-scraping-tools) | `pip install beautifulsoup4` | HTML parsing, pairs with `requests/httpx` [1] |
| **Playwright** | Apache-2.0 [2](https://reader.dev/blog/best-open-source-web-scraping-tools) | `pip install playwright && playwright install` | Real browser for JS-heavy review sites [2] |
| **Trafilatura** | MIT | `pip install trafilatura` | Clean LLM-ready markdown (replaces Firecrawl markdown) |
| **Crawl4AI** | Apache-2.0 + attribution [2](https://reader.dev/blog/best-open-source-web-scraping-tools) | `pip install crawl4ai` | RF: LLM/RAG markdown pipeline locally, no cloud |

**Pattern for adapters:**
```python
import trafilatura, httpx
from bs4 import BeautifulSoup
# instead of requests.get(...).text + regex
html = httpx.get(url, headers={"User-Agent":"OpportunityMiner/0.1.0"}).text
clean = trafilatura.extract(html) or BeautifulSoup(html, "lxml").get_text(" ", strip=True)
```
All are on `pypi.org` (allowed host) and `github.com`.

---

## 3. Search — Free Self-Hosted SERP (replaces SerpApi $25/mo & Bright Data $499/mo)

| Tool | License | One-line run | Coverage | Source |
|---|---|---|---|---|
| **OpenSERP** | MIT [1](https://openserp.org/alternatives/serpapi/) [2](https://openserp.org/blog/searxng-vs-openserp/) | `docker run -p 7000:7000 karust/openserp serve` then `curl "http://localhost:7000/google/search?text=excel+automation"` | Google, Bing, Yandex, Baidu, DuckDuckGo, Ecosia + megasearch + image search | [1](https://openserp.org/alternatives/serpapi/) [2](https://openserp.org/blog/searxng-vs-openserp/) |
| **SearXNG** | AGPL-3.0 [3](https://openclawlaunch.com/guides/openclaw-searxng) | `docker run -d -p 8080:8080 -v searxng:/etc/searxng searxng/searxng:latest` | **70+ engines** (Google, Bing, Wikipedia...) self-hosted, no API key, no limits [3](https://openclawlaunch.com/guides/openclaw-searxng) | [3](https://openclawlaunch.com/guides/openclaw-searxng) |
| **duckduckgo-search** (Python) | MIT | `pip install duckduckgo-search` | DuckDuckGo JSON, no key | lightweight for enrichment |

**OpportunityMiner fit:** Add `core/serp_enricher.py` that calls local OpenSERP before scoring:

```python
import requests
resp = requests.get("http://localhost:7000/google/search", params={"text": f"{problem} alternative pricing", "lang": "EN"}, timeout=10).json()
# resp["results"] → top competitors → writes to Competitor table
```

No per-search fee, no logs leaving host [1](https://openserp.org/alternatives/serpapi/). SearXNG is the private metasearch UI; OpenSERP is the structured JSON backend [2](https://openserp.org/blog/searxng-vs-openserp/).

---

## 4. Embeddings — Free Local (replaces OpenAI `text-embedding-3`)

All OSS, `pip install`able, run on CPU:

| Model | Params | Dim | Context | License | Install | Source |
|---|---|---|---|---|---|---|
| **BAAI/bge-m3** | 567M | 1024 + sparse | 8192 | MIT [2](https://builderai.tools/blog/best-open-source-embedding-models-2026) | `pip install sentence-transformers` then `SentenceTransformer("BAAI/bge-m3")` [2] | Hybrid dense+sparse, 100+ langs [2][5](https://localaimaster.com/blog/best-ollama-embedding-models) |
| **Qwen3-Embedding-0.6B** | 0.6B | 32-1024 (MRL) | 32K | Apache-2.0 [2](https://builderai.tools/blog/best-open-source-embedding-models-2026) [3](https://www.edenai.co/post/top-free-embedding-tools-apis-and-open-source-models) | `ollama pull qwen3-embedding:0.6b` or `sentence-transformers` | Best quality/GB, 32K ctx [2][3] |
| **nomic-embed-text** | 137M | 768 | 8192 | Apache-2.0 [5](https://localaimaster.com/blog/best-ollama-embedding-models) | `ollama pull nomic-embed-text` (274MB) [5] | Most-pulled, smallest serious [5] |
| **all-MiniLM-L6-v2** | 23M | 384 | 256 | Apache-2.0 [3](https://www.edenai.co/post/top-free-embedding-tools-apis-and-open-source-models) [5] | `pip install sentence-transformers` | 46MB, **drop-in replacement for current 384d** — zero code change |
| **FastEmbed** | ONNX quantized | varies | varies | MIT | `pip install fastembed` | No PyTorch, tiny containers |

**Recommendation:** Start with `all-MiniLM-L6-v2` (same 384d as current hash → no DB migration) then upgrade to `BGE-M3` or `Qwen3-0.6B`. FastEmbed keeps Docker <200MB vs PyTorch 2GB [2].

```python
# core/vector_store.py — FREE LOCAL REPLACEMENT
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # Apache-2.0, 80MB
def embed_text(text: str): return model.encode(text, normalize_embeddings=True)
```

---

## 5. Vector DB — Free Self-Hosted (replaces JSON file + Pinecone)

| DB | License | Self-host | Scale | Install | Source |
|---|---|---|---|---|---|
| **Qdrant** | Apache-2.0 [4](https://dreaming.press/posts/best-open-source-vector-database-2026.html) | `docker run -p 6333:6333 qdrant/qdrant` | 100M+ sharded [4] | `pip install qdrant-client` | Best standalone, Rust, single container [4] |
| **Chroma** | Apache-2.0 [1](https://iternal.ai/insights/best-vector-databases-2026) [2](https://klymentiev.com/blog/free-vector-database-credits) | `pip install chromadb` (embedded, no server) | ~1M comfortable [4] | `pip install chromadb` | SQLite of vectors, 5-min prototype [1][2] |
| **Weaviate** | BSD-3-Clause [4](https://dreaming.press/posts/best-open-source-vector-database-2026.html) | Docker/K8s | 100M+ | `docker run ... weaviate/weaviate` | Built-in hybrid + modules [1] |
| **Milvus** | Apache-2.0 [1](https://iternal.ai/insights/best-vector-databases-2026) | K8s cluster | Billions [1] | — | Only if you need B-scale [1] |
| **pgvector** | PostgreSQL [4](https://dreaming.press/posts/best-open-source-vector-database-2026.html) | `CREATE EXTENSION vector` in existing Postgres | Low millions/table [4] | Already have SQLite → add `sqlite-vec` (MIT) | No new service if on Postgres [4] |

**Recommendation:** **Chroma embedded** for dev (zero infra), **Qdrant** for production. Both free forever self-hosted; Qdrant Cloud free 1GB if you want managed later [2](https://klymentiev.com/blog/free-vector-database-credits). Chroma is Apache-2.0, trivial self-host [2][4]; Qdrant is Apache-2.0 one-container [4].

```python
# Replace data/vectors/negative_blacklist.json
import chromadb
client = chromadb.PersistentClient(path="data/vectors/chroma")
col = client.get_or_create_collection("blacklist", embedding_function=your_free_model)
col.add(ids=["rej_001"], embeddings=[vec], metadatas=[{"reason":"not my niche"}])
```

---

## 6. LLM Extraction — Free Local (replaces Gemini/OpenAI API)

| Engine | License | Run | Source |
|---|---|---|---|
| **Ollama** | MIT [2](https://itsourcecode.com/ai-framework/ollama-run-local-llms-2026-complete-guide/) [3](https://www.qovery.com/blog/self-host-open-source-llm-setups) | `curl -fsSL https://ollama.com/install.sh | sh && ollama run mistral` then `http://localhost:11434/api/generate` | One-command, OpenAI-compatible `:11434/v1` [2][3] |
| **llama.cpp** | MIT [3](https://www.qovery.com/blog/self-host-open-source-llm-setups) | CPU/Apple Silicon/1 GPU, GGUF Q4 | For raw local, no server |
| **vLLM** | Apache-2.0 [3] | `vllm serve Qwen/Qwen3-8B --max-model-len 8192` | High-throughput |

| Free Model (via Ollama) | Size | Context | License | Use |
|---|---|---|---|---|
| **Mistral 7B** | 4GB | 32K | Apache-2.0 [1](https://blog.itgranules.com/self-host-free-mistral-ai-models-using-ollama) | `ollama run mistral` — best 7B, cheap [1] |
| **Phi-4 14B** | 9.1GB | 128K | MIT [4](https://devtoollab.com/blog/top-5-local-llm-tools-models) | Coding, structured JSON |
| **Qwen3 8B** | ~5GB | 32K | Apache-2.0 | Agentic coding |
| **Llama 3.2 3B** | 2GB | 128K | Llama lic | Laptop-friendly |

Ollama is free/MIT [2], auto GPU detection, 4-bit quantization [2][3]. Keep existing `extractor.py` heuristic as fallback; if `OLLAMA_HOST` set, call local LLM with `Instructor`/`Pydantic` schema — same interface as Gemini stub.

```python
# core/extractor.py — FREE LOCAL
import requests, json
OLLAMA = "http://localhost:11434/api/generate"
def _extract_ollama(title, body):
    r = requests.post(OLLAMA, json={"model":"mistral", "prompt": f"Extract JSON: {title}\n{body}", "format":"json"}, timeout=30)
    return ProblemExtractionResult.model_validate_json(r.json()["response"])
```

---

## 7. CRM & Pipeline — Free OSS (replaces HubSpot / Airtable / Notion Cloud)

| CRM | License | Stack | GitHub | Best for | Source |
|---|---|---|---|---|---|
| **Twenty** | AGPL-3.0 | TS/React/NestJS, GraphQL+REST | 45.5k ⭐ [1](https://www.opensourcealternatives.to/blog/best-open-source-crm) | Dev teams, Salesforce replacement | [1][3](https://techsy.io/en/blog/open-source-crm-startups) |
| **EspoCRM** | GPL-3.0 | PHP/MySQL, REST | 2.9k ⭐ [1] | **Easiest no-code**: 90% admin-panel, 400MB RAM [3] | [1][3] |
| **SuiteCRM** | AGPL-3.0 | PHP/MySQL | 5.4k ⭐ [1] | Enterprise depth, Salesforce parity | [1] |
| **Odoo Community** | LGPL-3.0 | Python | 50.5k ⭐ [1] | CRM+ERP in one | [1] |
| **Krayin** | MIT | Laravel | — | Most permissive, sell without publishing | [3] → MIT row |
| **NocoDB** | AGPL-3.0 / MIT | Node | 50k+ ⭐ | **Airtable OSS clone** (use as DB) | Airtable alt |
| **Baserow** | MIT | Django/PostgreSQL | 5k ⭐ | Airtable OSS, self-host 1 cmd | Baserow MIT |
| **Grist** | Apache-2.0 | Python/Node | 7k ⭐ | Spreadsheet + DB hybrid | Grist Apache |

**Recommendation:** For OpportunityMiner, deploy **NocoDB or Baserow** (`docker run -p 8080:3000 nocodb/nocodb`) as your pipeline table — mirrors Airtable but free/MIT — and push from `generators/crm_sync.py`:

```python
import requests
# Baserow: POST /api/database/rows/table/{id}/?user_field_names=true
requests.post(f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/",
  headers={"Authorization": f"Token {TOKEN}"},
  json={"Title": opp.title, "Score": opp.opportunity_score, "Evidence": opp.evidence_level})
```

If you want full CRM, **EspoCRM** is lowest ops (Docker <5 min, 400MB) [3]; **Twenty** is most modern (GraphQL) for TypeScript teams [3].

---

## 8. Automation — Free OSS Zapier Replacements (replaces Zapier/Make)

| Tool | License (OSI?) | Hosting | Best for | Source |
|---|---|---|---|---|
| **Activepieces** | **MIT (true OSI)** [1](https://composio.dev/content/top-n8n-alternatives) [2](https://www.usecarly.com/blog/free-open-source-n8n-alternatives/) | `docker run -p 8080:80 activepieces/activepieces` | **Closest Zapier replacement, no-code, unlimited flows** [1][2] | [1][2] |
| **Automatisch** | AGPL-3.0 [1][2] | Docker | Zapier-style simple flows, privacy-first | [1][2] |
| **Huginn** | MIT [2](https://www.usecarly.com/blog/free-open-source-n8n-alternatives/) | Ruby, `docker run huginn/huginn` | Scraping/monitoring “agents”, most mature | [2] |
| **Node-RED** | Apache-2.0 [2] | `docker run -p 1880:1880 nodered/node-red` | IoT/event wiring, 4k+ nodes | [2] |
| **Windmill** | AGPL-3.0 [1] | Docker | Code-first engineers, scripts+flows | [1] |
| **Kestra / Airflow** | Apache-2.0 [1] | Docker/K8s | Data pipelines, orchestration | [1] |
| **n8n** | **Fair-code (NOT OSI)** [2] | Docker | Powerful but resale-restricted | [2] — avoid if strict OSS |

> For **strict 100% OSI** requirement, pick **Activepieces (MIT)** — unlimited self-hosted flows, no per-task fee [1][2]. Next easiest: **Automatisch (AGPL)** for Zapier UX [2].

---

## 9. Notifications & Alerts — Free OSS Push (replaces Slack paid, email SaaS)

| Tool | License | Self-host | Push target |
|---|---|---|---|
| **ntfy** | Apache-2.0 | `docker run -p 80:80 binwiederhier/ntfy serve` | `curl -d "Score 87: Excel hell" ntfy.sh/opportunityminer` → phone push free |
| **Gotify** | MIT | Docker | WebSocket push |
| **Apprise** | MIT | `pip install apprise` | Unified API → Slack, Discord, Telegram, email, 80+ services from one call |
| **Matrix + Element** | Apache-2.0 | Docker | Slack alternative, self-hosted, E2E |
| **Zulip** | Apache-2.0 | Docker | Threaded chat, free |

**Implementation:**
```python
# generators/notifier.py — FREE via Apprise (MIT)
import apprise
apobj = apprise.Apprise()
apobj.add("tgram://bot_token/chat_id")  # Telegram Bot (free)
apobj.add("discord://webhook_id/token") # Discord webhook (free)
apobj.notify(body=f"New OP-{cluster.id} Score {score}/100", title=opp.title)
# or ntfy: requests.post("https://ntfy.sh/opportunityminer", data=msg)
```

All on `pypi.org`.

---

## 10. Updated Architecture (Free-Only)

```
Public free APIs (GH, SO, DEV.to, Lobste.rs, Reddit JSON, HN Algolia, RSS)
        ↓
Crawlee / Scrapy / Trafilatura (Apache/MIT/BSD) — clean markdown
        ↓
SearXNG (AGPL) / OpenSERP (MIT) — local SERP for competitor validation
        ↓
Ollama + Mistral/Phi-4 (MIT/Apache) — Pydantic extraction (heuristic fallback)
        ↓
sentence-transformers + BGE-M3 / MiniLM (MIT/Apache) → Qdrant/Chroma (Apache) + sqlite-vec
        ↓
Deterministic scoring.py (unchanged)
        ↓
Activepieces (MIT) / Huginn (MIT) / Apprise (MIT) → Baserow/NocoDB (MIT) + ntfy/Gotify (Apache/MIT) + daily MD/JSON
```

**Total cost: $0/month + your VPS/laptop electricity.** All components are `docker compose up` reproducible and audited on `github.com`.

---

## 11. Prioritized Rollout (Free-Only Order)

**Week 1 — Ingestion boost (no infra):**
- [ ] Add `GithubAdapter`, `StackOverflowAdapter`, `DevToAdapter` (3 files, free APIs)
- [ ] Add `AppStoreAdapter` with `google-play-scraper` + Apple RSS

**Week 2 — Vector & LLM:**
- [ ] Replace hash `VectorStore` with `sentence-transformers/all-MiniLM-L6-v2` (same 384d, 1-line change) → `chromadb` embedded
- [ ] Add `OLLAMA_HOST` branch in `extractor.py` (`ollama run mistral`)

**Week 3 — Enrichment & Cleaning:**
- [ ] `pip install trafilatura beautifulsoup4` + `httpx` in adapters
- [ ] Self-host `SearXNG` or `OpenSERP` (`docker compose add`), add `serp_enricher.py`

**Week 4 — CRM & Alerts:**
- [ ] `pip install apprise` + `ntfy` push in `report_generator.py`
- [ ] `docker run baserow/baserow` or `nocodb/nocodb` + `crm_sync.py` push

**Docker compose (all free):**
```yaml
services:
  qdrant:      { image: qdrant/qdrant, ports: ["6333:6333"] }      # Apache-2.0
  searxng:     { image: searxng/searxng, ports: ["8080:8080"] }     # AGPL-3.0
  openserp:    { image: karust/openserp, command: serve, ports: ["7000:7000"] } # MIT
  ollama:      { image: ollama/ollama, ports: ["11434:11434"] }     # MIT
  baserow:     { image: baserow/baserow, ports: ["3000:3000"] }     # MIT
  activepieces:{ image: activepieces/activepieces, ports: ["8080:80"] } # MIT
  ntfy:        { image: binwiederhier/ntfy, command: serve, ports: ["80:80"] } # Apache
```

---

## 12. License Cheat-Sheet (All OSI)

| Category | Pick if strict MIT+Apache only | If AGPL acceptable |
|---|---|---|
| Vector DB | **Chroma (Apache-2.0)**, Qdrant (Apache-2.0), Milvus (Apache-2.0) | Weaviate (BSD-3) also fine |
| Embeddings | **all-MiniLM, BGE-M3 (MIT), Qwen3 (Apache)** [2][3] | — |
| LLM | **Ollama (MIT)**, vLLM (Apache), Phi-4 (MIT) | — |
| CRM | **Baserow (MIT), Krayin (MIT), Grist (Apache)** | Twenty/Espo/Suite (AGPL) |
| Automation | **Activepieces (MIT), Huginn (MIT), Node-RED (Apache)** [1][2] | Automatisch/Windmill (AGPL) |
| Scraping | **Crawlee/BSoup/Playwright (Apache/MIT)** [1][2] | — |
| Search | **OpenSERP (MIT)** [1] | SearXNG (AGPL) [3] |

---

### Sources (free-OSS verification)

- OpenSERP MIT free self-host `docker run karust/openserp serve` no API key [1](https://openserp.org/alternatives/serpapi/) ; SearXNG vs OpenSERP roles [2](https://openserp.org/blog/searxng-vs-openserp/)
- SearXNG AGPL, 70+ engines, free no API key, `docker searxng/searxng:latest` [3](https://openclawlaunch.com/guides/openclaw-searxng)
- Vector DBs: Qdrant/Chroma/Milvus Apache-2.0, Weaviate BSD-3, pgvector PG lic, free self-host [1](https://iternal.ai/insights/best-vector-databases-2026) [2](https://klymentiev.com/blog/free-vector-database-credits) [4](https://dreaming.press/posts/best-open-source-vector-database-2026.html)
- Embeddings: BGE-M3 MIT 1024+Sparse 8K [2](https://builderai.tools/blog/best-open-source-embedding-models-2026) ; Qwen3 Apache 32K [2][3](https://www.edenai.co/post/top-free-embedding-tools-apis-and-open-source-models) ; MiniLM Apache 384d fastest [3][5](https://localaimaster.com/blog/best-ollama-embedding-models) ; FastEmbed ONNX MIT [2]
- Ollama MIT `ollama run mistral` local REST `:11434` [2](https://itsourcecode.com/ai-framework/ollama-run-local-llms-2026-complete-guide/) [3](https://www.qovery.com/blog/self-host-open-source-llm-setups) ; Mistral 7B Apache [1](https://blog.itgranules.com/self-host-free-mistral-ai-models-using-ollama) ; Phi-4 MIT [4](https://devtoollab.com/blog/top-5-local-llm-tools-models)
- Scraping: Crawlee Apache-2.0, Scrapy BSD, BSoup MIT, Playwright Apache [1](https://use-apify.com/blog/best-free-web-scraping-tools-2026) [2](https://reader.dev/blog/best-open-source-web-scraping-tools)
- CRM: Twenty AGPL 45.5k⭐, EspoCRM GPL 2.9k⭐, SuiteCRM AGPL 5.4k⭐, Odoo LGPL 50k⭐ [1](https://www.opensourcealternatives.to/blog/best-open-source-crm) [3](https://techsy.io/en/blog/open-source-crm-startups)
- Automation: Activepieces MIT true OSS unlimited flows [1](https://composio.dev/content/top-n8n-alternatives) [2](https://www.usecarly.com/blog/free-open-source-n8n-alternatives/), n8n fair-code not OSI [2], Automatisch AGPL, Huginn MIT, Node-RED Apache [2]

Want me to scaffold the free adapters (`github`, `stackoverflow`, `devto`, `appstore`) + swap `VectorStore` to `all-MiniLM-L6-v2` + `Chroma` on this branch?
