---
name: problem-deduplicator
description: Removes exact and semantic duplicate signals using SHA-256 content hashing and local dense embeddings.
---

# Problem Deduplicator Skill

Eliminates repetitive data across multiple tiers:
- **Exact duplicates**: Same URL or identical body text SHA-256 hash.
- **Semantic duplicates**: Problems with cosine similarity > 0.92 within 48 hours are merged as additional evidence rather than creating duplicate records.
