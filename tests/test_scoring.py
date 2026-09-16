"""Unit tests for the deterministic opportunity scoring engine."""

from datetime import datetime
from opportunity_miner.core.scoring import OpportunityScorer
from opportunity_miner.core.extractor import ProblemExtractionResult
from opportunity_miner.database.models import ProblemCluster


def test_scoring_high_value_opportunity():
    extraction = ProblemExtractionResult(
        is_commercial_problem=True,
        problem_statement="Automate multi-store Shopify inventory sync with warehouse",
        underlying_problem="Lack of real-time two-way synchronization",
        target_customer="E-commerce Operator",
        current_workaround="Manual exports twice daily",
        frustration_severity="blocking",
        reports_financial_loss=True,
        reported_hours_lost_per_week=6.0,
        frequency_cadence="daily",
        explicit_budget_stated=500.0,
        currently_paying_for_workaround=True,
        actively_seeking_help=True,
        pain_quotes=["Losing thousands every week due to inventory stockouts."],
        payment_quotes=["Willing to pay $500 for a working script."],
        confidence_rating=0.95
    )

    cluster = ProblemCluster(
        id="CL-TEST1",
        title="Shopify Inventory Sync",
        description="Syncing inventory",
        mention_count=6,
        unique_sources=2,
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        trend_velocity=4.0
    )

    total_score, confidence, breakdown = OpportunityScorer.calculate_score(extraction, cluster)
    evidence_level = OpportunityScorer.calculate_evidence_level(extraction, cluster)

    # Pain: 12 (blocking) + 8 (financial loss) + 5 (hours >= 5) = 25 (max capped)
    assert breakdown["pain"] == 25.0
    # Frequency: 15 (daily)
    assert breakdown["frequency"] == 15.0
    # WTP: 12 (budget >= 100) + 8 (actively seeking) + 8 (paying) = 28 -> capped at 20.0
    assert breakdown["willingness_to_pay"] == 20.0
    # Recurrence: 11 (mentions >= 5)
    assert breakdown["market_recurrence"] == 11.0

    assert total_score >= 80.0
    assert evidence_level == 5
    assert confidence >= 0.8
