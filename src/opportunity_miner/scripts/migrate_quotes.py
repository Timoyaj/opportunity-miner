"""Migration script to clean scraped text and re-extract verbatim quotes for all DB records."""

import re
from opportunity_miner.database.session import get_db
from opportunity_miner.database.models import RawSignal, ExtractedProblem, ProblemCluster, Opportunity
from opportunity_miner.core.scraper import clean_scraped_text, extract_verbatim_quotes


def run_migration():
    with get_db() as db:
        signals = db.query(RawSignal).all()
        for sig in signals:
            sig.title = clean_scraped_text(sig.title)
            sig.body = clean_scraped_text(sig.body)

        problems = db.query(ExtractedProblem).all()
        for p in problems:
            p.problem_statement = clean_scraped_text(p.problem_statement)
            p.underlying_problem = clean_scraped_text(p.underlying_problem)
            sig_body = p.signal.body if p.signal and p.signal.body else ""
            full_text = f"{p.problem_statement}\n{sig_body}".strip()

            quotes = extract_verbatim_quotes(full_text, max_quotes=3)
            if not quotes and p.problem_statement:
                quotes = [p.problem_statement]
            p.pain_evidence = quotes

            wtp = []
            for s in re.split(r"(?<=[.!?\n])\s+", full_text):
                s_clean = s.strip()
                if len(s_clean) > 10 and any(k in s_clean.lower() for k in ["$", "cost", "pay", "budget", "hire", "subscription", "pricing", "rate"]):
                    wtp.append(s_clean[:180])
                    if len(wtp) >= 2:
                        break
            p.wtp_evidence = wtp

        # Also clean cluster titles and descriptions
        clusters = db.query(ProblemCluster).all()
        for cl in clusters:
            cl.title = clean_scraped_text(cl.title)
            cl.description = clean_scraped_text(cl.description)

        # Also clean opportunity titles
        opps = db.query(Opportunity).all()
        for opp in opps:
            opp.title = clean_scraped_text(opp.title)

        db.commit()
        print(f"Successfully migrated {len(signals)} signals and {len(problems)} extracted problems with clean quotes.")


if __name__ == "__main__":
    run_migration()
