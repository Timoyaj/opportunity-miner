"""Deterministic opportunity scoring engine and evidence strength classifier."""

from ..database.models import ExtractedProblem, ProblemCluster
from .extractor import ProblemExtractionResult


class OpportunityScorer:
    """Calculates deterministic opportunity scores and evidence levels using mathematical rubrics."""

    @staticmethod
    def calculate_evidence_level(extraction: ProblemExtractionResult, cluster: ProblemCluster) -> int:
        """Determine evidence level from 1 to 5 based on verifiable signals."""
        if extraction.explicit_budget_stated or (extraction.actively_seeking_help and extraction.currently_paying_for_workaround):
            return 5
        if extraction.currently_paying_for_workaround or extraction.reports_financial_loss:
            return 4
        if cluster.mention_count >= 3 or extraction.current_workaround:
            return 3
        if cluster.mention_count >= 2:
            return 2
        return 1

    @staticmethod
    def calculate_score(extraction: ProblemExtractionResult, cluster: ProblemCluster, user_skills: list[str] | None = None) -> tuple[float, float, dict]:
        """Compute deterministic opportunity score out of 100.
        Returns:
            (total_score: float, confidence: float, breakdown: dict)
        """
        # 1. Pain Score (Max 25 pts)
        pain = 0.0
        if extraction.frustration_severity == "blocking":
            pain += 12.0
        elif extraction.frustration_severity == "severe":
            pain += 8.0
        elif extraction.frustration_severity == "mild":
            pain += 4.0

        if extraction.reports_financial_loss:
            pain += 8.0

        if extraction.reported_hours_lost_per_week >= 5.0:
            pain += 5.0
        elif extraction.reported_hours_lost_per_week > 0:
            pain += 2.0

        pain = min(25.0, pain)

        # 2. Frequency Score (Max 15 pts)
        freq_weights = {
            "continuous": 15.0,
            "daily": 15.0,
            "weekly": 12.0,
            "monthly": 7.0,
            "yearly": 2.0,
            "unknown": 1.0,
        }
        frequency = freq_weights.get(extraction.frequency_cadence, 1.0)

        # 3. Willingness to Pay (Max 20 pts)
        wtp = 0.0
        if extraction.explicit_budget_stated and extraction.explicit_budget_stated >= 100.0:
            wtp += 12.0
        elif extraction.actively_seeking_help:
            wtp += 8.0

        if extraction.currently_paying_for_workaround:
            wtp += 8.0

        wtp = min(20.0, wtp)

        # 4. Market Recurrence (Max 15 pts)
        if cluster.mention_count >= 10:
            recurrence = 15.0
        elif cluster.mention_count >= 5:
            recurrence = 11.0
        elif cluster.mention_count >= 2:
            recurrence = 7.0
        else:
            recurrence = 3.0

        # 5. Technical Feasibility (Max 15 pts)
        feasibility = 13.5

        # 6. User Fit (Max 10 pts)
        fit = 9.0

        total_score = round(pain + frequency + wtp + recurrence + feasibility + fit, 1)

        breakdown = {
            "pain": pain,
            "frequency": frequency,
            "willingness_to_pay": wtp,
            "market_recurrence": recurrence,
            "technical_feasibility": feasibility,
            "user_fit": fit,
        }

        # Confidence: weighted by evidence presence
        confidence = round(0.5 + (0.1 if extraction.pain_quotes else 0.0) + (0.2 if extraction.payment_quotes or extraction.explicit_budget_stated else 0.0) + (0.2 if cluster.mention_count >= 2 else 0.0), 2)
        confidence = min(1.0, confidence)

        return total_score, confidence, breakdown
