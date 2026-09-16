"""Generates technical solution specifications and MVP architectures."""

from ..database.models import ExtractedProblem, ProblemCluster


class SolutionDesigner:
    """Creates technical solution hypotheses and MVP scopes."""

    @staticmethod
    def design_solution(problem: ExtractedProblem, cluster: ProblemCluster) -> dict:
        """Construct a structured technical solution specification."""
        statement = problem.problem_statement.lower()

        # Categorize primary architecture
        category = "AUTOMATION_SERVICE"
        if "dashboard" in statement or "report" in statement or "kpi" in statement or "visualiz" in statement:
            category = "DASHBOARD"
        elif "api" in statement or "sync" in statement or "integration" in statement or "webhook" in statement:
            category = "API_INTEGRATION"
        elif "clean" in statement or "excel" in statement or "csv" in statement or "spreadsheet" in statement:
            category = "DATA_PIPELINE"
        elif "ai" in statement or "llm" in statement or "summariz" in statement or "extract" in statement:
            category = "AI_APPLICATION"

        tech_stack = ["Python 3.11+", "pandas", "Pydantic", "FastAPI"]
        if category == "DASHBOARD":
            tech_stack += ["Streamlit", "Plotly", "DuckDB"]
        elif category == "API_INTEGRATION":
            tech_stack += ["httpx", "Celery / Redis", "SQLAlchemy"]
        elif category == "AI_APPLICATION":
            tech_stack += ["Instructor / LangChain", "ChromaDB / SQLite-vec"]

        core_features = [
            f"Automated ingestion connector replacing '{problem.current_workaround or 'manual process'}'",
            "Validation & schema integrity checks with automated error reporting",
            "Execution scheduler with webhook and email failure alerts",
        ]

        optional_features = [
            "Self-service web dashboard for non-technical team members",
            "Audit logging and historical data export to CSV/Parquet",
            "Role-based access control and multi-tenant billing connector",
        ]

        mvp_scope = {
            "core_features": core_features,
            "optional_features": optional_features,
            "estimated_build_time_hours": 16,
            "architecture_summary": f"Lightweight Python service orchestrating data normalization and syncing automatically.",
        }

        return {
            "category": category,
            "technology_stack": tech_stack,
            "mvp_scope": mvp_scope,
            "target_customer": problem.target_customer,
            "proposed_workflow": f"Replace {problem.current_workaround or 'manual recurring work'} with a verified automated pipeline that executes on schedule with zero human intervention.",
        }
