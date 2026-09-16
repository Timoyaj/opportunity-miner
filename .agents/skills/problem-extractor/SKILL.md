---
name: problem-extractor
description: Extracts atomic problem statements, underlying bottlenecks, target personas, workarounds, and verbatim evidence rubrics using strict Pydantic schemas and intelligent text cleaners.
---

# Problem Extractor Skill

Transforms raw unstructured signals into high-fidelity structured problem records with guaranteed verbatim evidence quotes.

## Core Directives:

1. **Clean Scraped Input**:
   - Run all titles and bodies through `clean_scraped_text` to eliminate HTML tags, entities (`&#39;` -> `'`), and scraper artifacts before schema parsing.

2. **Guaranteed Verbatim Quote Extraction**:
   - **Verbatim Pain Quotes (`pain_evidence`)**: Extract 1 to 3 direct sentences verbatim from the author detailing the friction, repetitive task, error, or operational failure.
   - **Zero-Loss Fallback**: If no explicit pain keyword is found, extract the primary question or intent sentence directly from the user's text. Never leave verbatim quotes empty if authentic user text exists.
   - **Verbatim Commercial Quotes (`wtp_evidence`)**: Extract explicit statements regarding budget, hourly rate, tool subscription spend, or willingness to pay.

3. **Separation of Symptoms from Root Causes**:
   - Do not mistake surface complaints for root problems. E.g., *"Hates Monday reporting"* is a symptom; *"Manual consolidation of weekly inventory across 15 disparate vendor CSVs"* is the structural bottleneck.

4. **Structured Schema Conformance**:
   - Enforce validation against `ProblemExtractionResult` schema.
