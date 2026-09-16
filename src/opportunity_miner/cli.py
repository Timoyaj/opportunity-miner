"""OpportunityMiner Command Line Interface (CLI)."""

import os
import sys

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime, timedelta
from pathlib import Path
import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console(highlight=False)

from .database.session import get_db, init_db
from .database.models import RawSignal, ExtractedProblem, ProblemCluster, Opportunity

from .adapters import get_adapter, ADAPTERS_MAP
from .core.prefilter import PreFilter
from .core.vector_store import VectorStore
from .core.extractor import ProblemExtractor
from .core.clusterer import IncrementalClusterer
from .core.scoring import OpportunityScorer
from .generators.solution_hypotheses import SolutionDesigner
from .generators.outreach_generator import CommercialPackager
from .generators.report_generator import ReportGenerator

console = Console()


def load_yaml_config(name: str) -> dict:
    """Load configuration from config directory."""
    path = Path(__file__).resolve().parents[3] / "config" / f"{name}.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


@click.group()
def main():
    """OpportunityMiner AI: Autonomous commercial opportunity intelligence engine."""
    init_db()


@main.command()
def health():
    """Check connectivity and credentials for all source adapters."""
    console.print(Panel.fit("[bold blue]OpportunityMiner Source Health Diagnostics[/bold blue]"))
    table = Table(title="Adapter Connectivity")
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Diagnostic Message")

    for name in ADAPTERS_MAP:
        try:
            adapter = get_adapter(name)
            is_ok, msg = adapter.health_check()
            status_str = "[green]ONLINE[/green]" if is_ok else "[red]OFFLINE[/red]"
            table.add_row(name.capitalize(), status_str, msg)
        except Exception as e:
            table.add_row(name.capitalize(), "[red]ERROR[/red]", str(e))

    console.print(table)


@main.command()
@click.option("--sources", "-s", default="all", help="Comma-separated sources or 'all' (hackernews, reddit, upwork, indiehackers, producthunt)")
@click.option("--limit", "-l", default=30, help="Maximum signals to collect per source query.")
@click.option("--query", "-q", default=None, help="Target search query or domain (e.g. 'excel automation').")
@click.option("--days", "-d", default=7, type=int, help="Scan signals from the past N days (default: 7).")
def scan(sources: str, limit: int, query: str | None, days: int):
    """Execute complete ingestion, extraction, clustering, and scoring pipeline."""
    query_desc = f" for '{query}'" if query else ""
    console.print(Panel.fit(f"[bold green]Starting OpportunityMiner Intelligence Scan{query_desc} (Past {days} Days)[/bold green]"))

    sources_cfg = load_yaml_config("sources")
    src_configs = sources_cfg.get("sources", {})

    target_sources = list(ADAPTERS_MAP.keys()) if sources == "all" else [s.strip().lower() for s in sources.split(",")]

    since = datetime.utcnow() - timedelta(days=days) if days else None

    prefilter = PreFilter()
    vector_store = VectorStore()
    extractor = ProblemExtractor()
    clusterer = IncrementalClusterer(vector_store)
    scorer = OpportunityScorer()

    with get_db() as db:
        existing_hashes = {r[0] for r in db.query(RawSignal.content_hash).all()}
        all_signals = []

        # 1. Collect from sources
        for src_name in target_sources:
            if src_name not in ADAPTERS_MAP:
                console.print(f"[yellow]Skipping unknown source: {src_name}[/yellow]")
                continue

            cfg = src_configs.get(src_name, {})
            if not cfg.get("enabled", True):
                console.print(f"[dim]Source {src_name} is disabled in config.[/dim]")
                continue

            try:
                adapter = get_adapter(src_name)
                if query:
                    if src_name == "reddit":
                        if "excel" in query.lower():
                            queries = ["excel", "vba", "smallbusiness"]
                        else:
                            queries = [query.replace(" ", "")]
                    elif src_name == "hackernews":
                        queries = [query, f"{query} tool", "excel automation"]
                    elif src_name == "upwork":
                        queries = [query, "excel automation"]
                    else:
                        queries = [query]
                else:
                    queries = cfg.get("queries") or cfg.get("subreddits") or cfg.get("rss_queries") or ["automate", "manual"]

                console.print(f"[*] Ingesting from [bold cyan]{src_name}[/bold cyan]...")
                collected = adapter.collect(queries=queries, limit=limit, since=since)
                console.print(f"  |-- Ingested [bold]{len(collected)}[/bold] signals from {src_name}")
                all_signals.extend(collected)
            except Exception as e:
                console.print(f"  [red]Failed collecting from {src_name}: {e}[/red]")

        # 2. Stage 1 Pre-Filtering
        console.print("\n[*] Running Stage 1 Lexical & Hash Pre-Filter...")
        candidates = prefilter.filter_signals(all_signals, existing_hashes=existing_hashes)
        console.print(f"  |-- Filtered [bold]{len(all_signals)}[/bold] raw signals down to [bold green]{len(candidates)}[/bold green] candidates.")


        # 3. Extraction, Vector Pruning, Clustering, and Scoring
        new_problems_count = 0
        new_opps_count = 0

        for signal, chash, matches in candidates:
            # Store RawSignal
            raw_sig = RawSignal(
                id=f"{signal.source}_{signal.source_id}",
                source=signal.source,
                source_url=signal.source_url,
                author=signal.author,
                title=signal.title,
                body=signal.body,
                published_at=signal.published_at,
                content_hash=chash,
                raw_metadata_json=yaml.dump(signal.metadata)
            )
            db.merge(raw_sig)
            db.flush()

            # Problem Extraction
            extraction = extractor.extract(signal.title, signal.body, signal.source)
            if not extraction or not extraction.is_commercial_problem:
                continue

            # Vector generation
            vec = vector_store.embed_text(f"{extraction.problem_statement} {extraction.underlying_problem}")

            # Check negative feedback blacklist
            if vector_store.is_blacklisted(vec):
                console.print(f"  [yellow]Pruned topic similar to user-rejected blacklist:[/yellow] {extraction.problem_statement[:50]}...")
                continue

            prob_id = f"PR-{chash[:8].upper()}"
            extracted_prob = ExtractedProblem(
                id=prob_id,
                signal_id=raw_sig.id,
                problem_statement=extraction.problem_statement,
                underlying_problem=extraction.underlying_problem,
                target_customer=extraction.target_customer,
                current_workaround=extraction.current_workaround,
                pain_evidence=extraction.pain_quotes,
                frequency_evidence=extraction.frequency_cadence,
                wtp_evidence=extraction.payment_quotes,
                embedding=vector_store.vector_to_bytes(vec),
            )
            db.merge(extracted_prob)
            db.flush()
            new_problems_count += 1

            # Cluster problem
            cluster = clusterer.cluster_problem(extracted_prob, db)

            # Score Opportunity
            score, confidence, breakdown = scorer.calculate_score(extraction, cluster)
            evidence_lvl = scorer.calculate_evidence_level(extraction, cluster)

            # Generate commercial assets
            solution = SolutionDesigner.design_solution(extracted_prob, cluster)
            ladder = CommercialPackager.create_offer_ladder(extracted_prob, cluster)
            outreach = CommercialPackager.create_outreach_message(extracted_prob, signal.author)
            val_plan = CommercialPackager.create_validation_plan(extracted_prob)

            opp_id = f"OP-{cluster.id.replace('CL-', '')}"
            existing_opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()

            if not existing_opp:
                opp = Opportunity(
                    id=opp_id,
                    cluster_id=cluster.id,
                    title=cluster.title.replace("Workflow: ", ""),
                    category=solution["category"],
                    opportunity_score=score,
                    confidence_score=confidence,
                    evidence_level=evidence_lvl,
                    technical_feasibility=breakdown["technical_feasibility"],
                    user_expertise_fit=breakdown["user_fit"],
                    score_breakdown=breakdown,
                    solution_hypothesis=solution,
                    commercial_packaging={
                        "offer_ladder": ladder,
                        "outreach_message": outreach,
                        "validation_plan": val_plan,
                    },
                    status="NEW"
                )
                db.add(opp)
                new_opps_count += 1
            else:
                # Update existing score
                existing_opp.opportunity_score = max(existing_opp.opportunity_score, score)
                existing_opp.evidence_level = max(existing_opp.evidence_level, evidence_lvl)
                existing_opp.score_breakdown = breakdown

            db.commit()

        console.print(f"\n[bold green]Scan Complete![/bold green]")
        console.print(f"Extracted [bold]{new_problems_count}[/bold] problems and updated [bold]{new_opps_count}[/bold] commercial opportunities.")


@main.command()
@click.option("--format", "-f", default="md,json", help="Report formats: md, json, or md,json")
def report(format: str):
    """Generate the latest daily executive opportunity briefing."""
    generator = ReportGenerator()
    statuses = {}
    for name in ADAPTERS_MAP:
        try:
            adapter = get_adapter(name)
            statuses[name] = adapter.health_check()
        except Exception as e:
            statuses[name] = (False, str(e))

    with get_db() as db:
        md_path, json_path = generator.generate_daily_report(db, statuses)
        console.print(Panel.fit(f"[bold green]Daily Intelligence Briefing Generated![/bold green]\nMarkdown: [cyan]{md_path}[/cyan]\nJSON: [cyan]{json_path}[/cyan]"))


@main.command()
@click.option("--port", "-p", default=8501, help="Port to run Streamlit app on.")
def ui(port: int):
    """Launch the interactive OpportunityMiner Streamlit CRM dashboard."""
    app_path = Path(__file__).resolve().parents[0] / "ui" / "app.py"
    console.print(f"[bold green]Launching Streamlit Dashboard on port {port}...[/bold green]")
    os.system(f"streamlit run {app_path} --server.port {port}")


if __name__ == "__main__":
    main()
