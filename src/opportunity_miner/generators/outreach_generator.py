"""Generates 3-stage commercial offer ladders and consultative outreach messages."""

from ..database.models import ExtractedProblem, ProblemCluster


class CommercialPackager:
    """Produces commercial action assets, offer escalation ladders, and cold outreach drafts."""

    @staticmethod
    def create_offer_ladder(problem: ExtractedProblem, cluster: ProblemCluster) -> dict:
        """Construct a 3-tier commercial escalation ladder."""
        workaround = problem.current_workaround or "manual spreadsheet updates"

        return {
            "tier_1_foot_in_the_door": {
                "name": "One-Time Custom Fix / Script",
                "price": "$250 – $500",
                "deliverable": f"Custom Python script that automates {problem.problem_statement[:60]} in one click.",
                "timeline": "48 hours",
                "sales_goal": "Establish trust, secure quick cash flow, and access the client's internal data workflow."
            },
            "tier_2_monthly_retainer": {
                "name": "Managed Workflow Retainer",
                "price": "$400 – $900 / month",
                "deliverable": f"Cloud-hosted automation running daily with error monitoring, schema repairs, and priority support.",
                "timeline": "Ongoing",
                "sales_goal": "Convert one-off service into stable monthly recurring revenue."
            },
            "tier_3_productized_saas": {
                "name": "Micro-SaaS Web Portal",
                "price": "$39 – $79 / month",
                "deliverable": f"Self-service multi-tenant web application allowing any {problem.target_customer} to solve this problem without writing code.",
                "timeline": "30-day MVP build",
                "sales_goal": "Scalable software asset decoupled from founder labor."
            }
        }

    @staticmethod
    def create_outreach_message(problem: ExtractedProblem, author: str | None = None) -> str:
        """Draft a polite, consultative outreach message that does not sound like spam."""
        recipient = author or "there"
        workaround = problem.current_workaround or "your current manual workaround"

        message = (
            f"Hi {recipient},\n\n"
            f"I came across your post about the friction you're facing with {workaround} when trying to {problem.problem_statement[:70]}.\n\n"
            f"I specialize in Python and workflow automation, and this bottleneck is usually caused by {problem.underlying_problem[:90]}.\n\n"
            f"I put together a quick 2-minute breakdown demonstrating how this can be completely automated with zero daily effort. "
            f"Would it be helpful if I shared that with you?\n\n"
            f"Best regards,\n[Your Name]"
        )
        return message

    @staticmethod
    def create_validation_plan(problem: ExtractedProblem) -> dict:
        """Create a 5-step customer validation interview plan."""
        return {
            "target_persona": problem.target_customer,
            "interview_target_count": 5,
            "qualifying_questions": [
                f"How often are you currently dealing with {problem.problem_statement[:50]}?",
                f"What tools or workarounds (like {problem.current_workaround or 'spreadsheets'}) are you currently using?",
                "How many hours per week does your team spend fixing errors or maintaining this process?",
                "Have you evaluated any commercial software for this, and why didn't it work?",
                "If an automated tool solved this reliably tomorrow, what would that be worth to your business monthly?"
            ],
            "landing_page_headline": f"Never Waste Another Hour On {problem.problem_statement[:50]}",
            "landing_page_subhead": f"Automated, error-proof data workflows designed specifically for {problem.target_customer}."
        }
