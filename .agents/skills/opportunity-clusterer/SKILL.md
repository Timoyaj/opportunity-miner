---
name: opportunity-clusterer
description: Groups related problems into persistent semantic clusters using running centroid vectors and trend velocity tracking.
---

# Opportunity Clusterer Skill

Manages the incremental centroid clustering engine.

## Mechanism:
- Computes cosine similarity of incoming problems against existing cluster centroids.
- If similarity >= 0.82, assigns problem to the cluster and updates its running centroid vector.
- Preserves consistent cluster IDs across daily runs to prevent ID drift and broken references.
