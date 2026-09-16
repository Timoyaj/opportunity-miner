"""Generates daily intelligence briefing reports in Markdown and JSON formats."""

from datetime import datetime
import json
from pathlib import Path
from sqlalchemy.orm import Session

from ..database.models import Opportunity, RawSignal, ProblemCluster, ExtractedProblem


class ReportGenerator:
    """Produces daily Markdown and JSON executive briefing reports."""

    def __init__(self, output_dir: str | Path = "reports"):
        self.output_dir = Path(output_dir)

    def generate_daily_report(self, db: Session, source_statuses: dict[str, tuple[bool, str]]) -> tuple[Path, Path]:
        """Generate both Markdown and JSON reports for today."""
        today = datetime.utcnow()
        date_str = today.strftime("%Y-%m-%d")
        year_str = today.strftime("%Y")
        month_str = today.strftime("%m")

        target_dir = self.output_dir / year_str / month_str
        target_dir.mkdir(parents=True, exist_ok=True)

        md_path = target_dir / f"{date_str}.md"
        json_path = target_dir / f"{date_str}.json"

        # Fetch stats
        total_signals = db.query(RawSignal).count()
        total_problems = db.query(ExtractedProblem).count()
        total_clusters = db.query(ProblemCluster).count()
        top_opportunities = db.query(Opportunity).order_by(Opportunity.opportunity_score.desc()).limit(20).all()

        # Build JSON data
        report_data = {
            "report_date": date_str,
            "generated_at": today.isoformat(),
            "source_coverage": {src: {"available": status[0], "message": status[1]} for src, status in source_statuses.items()},
            "metrics": {
                "total_raw_signals": total_signals,
                "total_extracted_problems": total_problems,
                "total_problem_clusters": total_clusters,
                "high_value_opportunities": len(top_opportunities),
            },
            "top_opportunities": [
                {
                    "id": opp.id,
                    "title": opp.title,
                    "category": opp.category,
                    "score": opp.opportunity_score,
                    "confidence": opp.confidence_score,
                    "evidence_level": opp.evidence_level,
                    "status": opp.status,
                    "score_breakdown": opp.score_breakdown,
                    "solution_hypothesis": opp.solution_hypothesis,
                    "commercial_packaging": opp.commercial_packaging,
                }
                for opp in top_opportunities
            ]
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # Build Markdown report
        md_lines = [
            f"# OpportunityMiner Daily Intelligence Briefing: {date_str}\n",
            "## 1. Executive Summary & Funnel Performance\n",
            f"* **Total Raw Signals Ingested:** {total_signals}",
            f"* **Verified Extracted Problems:** {total_problems}",
            f"* **Active Problem Clusters:** {total_clusters}",
            f"* **Top Commercial Opportunities Identified:** {len(top_opportunities)}\n",
            "### Source Coverage & Health Status\n",
            "| Source | Status | Diagnostic Notes |",
            "| :--- | :--- | :--- |",
        ]

        for src, status in source_statuses.items():
            status_badge = "✅ COMPLETE" if status[0] else "⚠️ UNAVAILABLE / PARTIAL"
            md_lines.append(f"| **{src.capitalize()}** | {status_badge} | {status[1]} |")

        md_lines.append("\n---\n")
        md_lines.append("## 2. Top Ranked Commercial Opportunities\n")

        if not top_opportunities:
            md_lines.append("> *No opportunities currently meet the quality threshold. Run additional source ingestion to collect fresh signals.*\n")

        for rank, opp in enumerate(top_opportunities, start=1):
            bd = opp.score_breakdown
            sol = opp.solution_hypothesis
            pkg = opp.commercial_packaging
            ladder = pkg.get("offer_ladder", {})

            md_lines.append(f"### #{rank} [{opp.id}] {opp.title}")
            md_lines.append(f"* **Category:** `{opp.category}` | **Status:** `{opp.status}`")
            md_lines.append(f"* **Opportunity Score:** **{opp.opportunity_score}/100** | **Confidence:** {opp.confidence_score} | **Evidence Level:** Level {opp.evidence_level}\n")
            
            md_lines.append("#### Deterministic Score Breakdown")
            md_lines.append(f"- **Pain Intensity:** {bd.get('pain', 0.0)} / 25.0")
            md_lines.append(f"- **Frequency Cadence:** {bd.get('frequency', 0.0)} / 15.0")
            md_lines.append(f"- **Willingness to Pay:** {bd.get('willingness_to_pay', 0.0)} / 20.0")
            md_lines.append(f"- **Market Recurrence:** {bd.get('market_recurrence', 0.0)} / 15.0")
            md_lines.append(f"- **Technical Feasibility:** {bd.get('technical_feasibility', 0.0)} / 15.0")
            md_lines.append(f"- **Founder Skill Fit:** {bd.get('user_fit', 0.0)} / 10.0\n")

            if opp.cluster and opp.cluster.problems:
                first_problem = opp.cluster.problems[0]
                pain_quotes = first_problem.pain_evidence
                if pain_quotes:
                    md_lines.append("#### Verbatim Evidence Quotes")
                    for q in pain_quotes[:2]:
                        md_lines.append(f"> *\"{q}\"*")
                    if first_problem.signal:
                        md_lines.append(f"> — *Source: [{first_problem.signal.source}]({first_problem.signal.source_url})*\n")

            if ladder:
                md_lines.append("#### 3-Stage Commercial Offer Ladder")
                t1 = ladder.get("tier_1_foot_in_the_door", {})
                t2 = ladder.get("tier_2_monthly_retainer", {})
                t3 = ladder.get("tier_3_productized_saas", {})
                md_lines.append(f"1. **Stage 1 ({t1.get('name', 'Script')}):** `{t1.get('price')}` — {t1.get('deliverable')}")
                md_lines.append(f"2. **Stage 2 ({t2.get('name', 'Retainer')}):** `{t2.get('price')}` — {t2.get('deliverable')}")
                md_lines.append(f"3. **Stage 3 ({t3.get('name', 'SaaS')}):** `{t3.get('price')}` — {t3.get('deliverable')}\n")

            outreach = pkg.get("outreach_message")
            if outreach:
                md_lines.append("#### Consultative Outreach Template")
                md_lines.append("```text")
                md_lines.append(outreach)
                md_lines.append("```\n")

            md_lines.append("---\n")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        return md_path, json_path
