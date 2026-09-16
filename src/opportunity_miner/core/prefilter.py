"""Stage 1 Pre-filtering: Content hashing deduplication and Regex Trie keyword pruning."""

import hashlib
from pathlib import Path
import re
from typing import Iterable
import yaml

from ..adapters.base import NormalizedSignal


class PreFilter:
    """Zero-cost fast lexical and content-hash pre-filtering engine."""

    def __init__(self, keywords_config_path: str | Path | None = None):
        if keywords_config_path is None:
            keywords_config_path = Path(__file__).resolve().parents[3] / "config" / "keywords.yaml"

        self.pain_keywords = []
        self.automation_keywords = []
        self.demand_keywords = []
        self.data_keywords = []

        if Path(keywords_config_path).exists():
            with open(keywords_config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.pain_keywords = data.get("pain_keywords", [])
                self.automation_keywords = data.get("automation_keywords", [])
                self.demand_keywords = data.get("demand_keywords", [])
                self.data_keywords = data.get("data_keywords", [])

        # Compile regex patterns with word boundaries
        self.pain_pattern = self._compile_pattern(self.pain_keywords)
        self.demand_pattern = self._compile_pattern(self.demand_keywords)
        self.domain_pattern = self._compile_pattern(self.automation_keywords + self.data_keywords)

    def _compile_pattern(self, words: list[str]) -> re.Pattern | None:
        if not words:
            return None
        escaped = [re.escape(w) for w in words]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute deterministic SHA-256 hash of normalized text."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def is_candidate(self, text: str) -> tuple[bool, dict[str, list[str]]]:
        """Check whether text qualifies as an opportunity candidate signal.
        Rule: Must match at least ONE (Pain or Demand) signal AND at least ONE (Domain/Automation/Data) signal.
        """
        matches = {"pain": [], "demand": [], "domain": []}

        if self.pain_pattern:
            matches["pain"] = list(set(self.pain_pattern.findall(text.lower())))
        if self.demand_pattern:
            matches["demand"] = list(set(self.demand_pattern.findall(text.lower())))
        if self.domain_pattern:
            matches["domain"] = list(set(self.domain_pattern.findall(text.lower())))

        has_pain_or_demand = bool(matches["pain"] or matches["demand"])
        has_domain = bool(matches["domain"])

        is_qualifying = has_pain_or_demand and has_domain
        return is_qualifying, matches

    def filter_signals(self, signals: Iterable[NormalizedSignal], existing_hashes: set[str] | None = None) -> list[tuple[NormalizedSignal, str, dict]]:
        """Filter raw signals.
        Returns:
            list of (signal, content_hash, match_metadata)
        """
        if existing_hashes is None:
            existing_hashes = set()
        candidates = []

        for signal in signals:
            chash = self.compute_hash(signal.body)
            if chash in existing_hashes:
                continue

            qualifies, matches = self.is_candidate(signal.body)
            if qualifies:
                existing_hashes.add(chash)
                candidates.append((signal, chash, matches))

        return candidates
