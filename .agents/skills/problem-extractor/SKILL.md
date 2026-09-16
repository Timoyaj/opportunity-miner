---
name: problem-extractor
description: Extracts atomic problem statements, underlying bottlenecks, target personas, workarounds, and evidence rubrics using strict Pydantic schemas.
---

# Problem Extractor Skill

Extracts structured problems from raw signals.

## Core Directives:
1. **Never conflate symptoms with root problems**: "Hates Monday reporting" is a symptom; "Manual recurring report consolidation across disparate CSVs" is the problem.
2. **Extract exact quotes**: Preserve verbatim evidence for pain and payment readiness.
3. **Structured schema**: Always conform to `ProblemExtractionResult`.
