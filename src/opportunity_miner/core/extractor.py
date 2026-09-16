"""Problem extractor using Pydantic structured output with intelligent offline heuristic fallback."""

import json
import logging
import os
import re
from typing import Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProblemExtractionResult(BaseModel):
    """Pydantic schema for structured problem extraction."""
    is_commercial_problem: bool = Field(
        description="True if author is expressing a genuine business, technical, or workflow problem."
    )
    problem_statement: str = Field(
        description="Concise 1-2 sentence description of what the user is trying to accomplish."
    )
    underlying_problem: str = Field(
        description="Root cause or structural bottleneck behind the symptom."
    )
    target_customer: str = Field(
        description="Role, persona, or business type of the person experiencing this."
    )
    current_workaround: str | None = Field(
        default=None, description="Existing tools, spreadsheets, or manual processes."
    )

    # Deterministic Scoring Evidence Rubric Flags
    frustration_severity: Literal["none", "mild", "severe", "blocking"] = Field(
        default="mild", description="Degree of pain expressed in text."
    )
    reports_financial_loss: bool = Field(
        default=False, description="Mentions money lost, missed sales, or direct cash waste."
    )
    reported_hours_lost_per_week: float = Field(
        default=0.0, description="Estimated hours lost per week."
    )
    frequency_cadence: Literal["unknown", "yearly", "monthly", "weekly", "daily", "continuous"] = Field(
        default="unknown", description="Cadence of the problem occurrence."
    )
    explicit_budget_stated: float | None = Field(
        default=None, description="Dollar amount or hourly rate explicitly stated."
    )
    currently_paying_for_workaround: bool = Field(
        default=False, description="Pays for an inadequate tool/service currently."
    )
    actively_seeking_help: bool = Field(
        default=False, description="Explicitly asking to buy software, hire, or find a tool."
    )

    # Exact Verbatim Quotes
    pain_quotes: list[str] = Field(default_factory=list)
    payment_quotes: list[str] = Field(default_factory=list)
    confidence_rating: float = Field(default=0.8, ge=0.0, le=1.0)


class ProblemExtractor:
    """Extracts structured commercial problems using LLM or rule-based heuristics."""

    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

    def extract(self, title: str, body: str, source: str) -> ProblemExtractionResult | None:
        """Extract structured problem from text."""
        # Check if LLM API is available
        if self.gemini_api_key:
            try:
                return self._extract_gemini(title, body, source)
            except Exception as e:
                logger.warning(f"Gemini API extraction failed, using heuristic fallback: {e}")
        elif self.openai_api_key:
            try:
                return self._extract_openai(title, body, source)
            except Exception as e:
                logger.warning(f"OpenAI API extraction failed, using heuristic fallback: {e}")

        # Reliable, fast heuristic extractor
        return self._extract_heuristic(title, body, source)

    def _extract_heuristic(self, title: str, body: str, source: str) -> ProblemExtractionResult:
        """Rule-based NLP heuristic extractor that extracts rubrics, quotes, and underlying problems."""
        full_text = f"{title}\n{body}".strip()
        lower_text = full_text.lower()

        # 1. Budget extraction
        budget_match = re.search(r"\$\s*([0-9,]+(?:\.[0-9]{2})?)", full_text)
        budget = float(budget_match.group(1).replace(",", "")) if budget_match else None

        # 2. Hours lost
        hours_match = re.search(r"(\d+)\s*(?:hours|hrs)\s*(?:a|per|\/)\s*(?:week|day|month)", lower_text)
        hours_lost = float(hours_match.group(1)) if hours_match else 0.0

        # 3. Frequency cadence
        cadence = "unknown"
        if any(w in lower_text for w in ["every day", "daily", "each day"]):
            cadence = "daily"
        elif any(w in lower_text for w in ["every week", "weekly", "each week", "every monday", "every friday"]):
            cadence = "weekly"
        elif any(w in lower_text for w in ["every month", "monthly", "end of month"]):
            cadence = "monthly"
        elif any(w in lower_text for w in ["continuous", "constantly", "real-time"]):
            cadence = "continuous"

        # 4. Pain severity
        severity = "mild"
        if any(w in lower_text for w in ["blocking", "broken", "critical", "cannot work", "can't proceed", "shut down"]):
            severity = "blocking"
        elif any(w in lower_text for w in ["nightmare", "disaster", "terrible", "hate", "drowning", "impossible", "waste hours"]):
            severity = "severe"

        # 5. Financial loss
        financial_loss = any(w in lower_text for w in ["lost revenue", "costing us", "lost money", "expensive error", "lost client"])

        # 6. Actively seeking
        seeking = any(w in lower_text for w in [
            "looking for", "need a tool", "need software", "is there an app", "willing to pay",
            "hire someone", "recommend a", "would pay", "budget is"
        ])

        # 7. Paying for workaround
        paying = any(w in lower_text for w in [
            "paying for", "subscription", "our current tool", "too expensive for what it does", "switched from"
        ])

        # Extract pain quotes
        pain_quotes = []
        sentences = re.split(r"[.!?\n]+", full_text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 15:
                s_low = s_clean.lower()
                if any(k in s_low for k in ["tedious", "manual", "takes hours", "frustrating", "waste", "struggle", "error"]):
                    pain_quotes.append(s_clean[:150])
                if len(pain_quotes) >= 3:
                    break

        # Payment quotes
        payment_quotes = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 10:
                s_low = s_clean.lower()
                if any(k in s_low for k in ["$", "pay", "budget", "hire", "cost", "subscription"]):
                    payment_quotes.append(s_clean[:150])
                if len(payment_quotes) >= 2:
                    break

        # Workaround identification
        workaround = None
        if "excel" in lower_text or "spreadsheet" in lower_text or "sheets" in lower_text:
            workaround = "Manual Excel / Spreadsheet tracking"
        elif "copy paste" in lower_text or "copying" in lower_text:
            workaround = "Manual copy-pasting across systems"
        elif "zapier" in lower_text or "make.com" in lower_text:
            workaround = "Fragile Zapier / No-code integration"

        # Target customer persona
        customer = "Business Operator / Freelancer"
        if "ecommerce" in lower_text or "shopify" in lower_text or "store" in lower_text:
            customer = "E-commerce Store Owner"
        elif "agency" in lower_text or "client" in lower_text:
            customer = "Agency Owner / Service Provider"
        elif "saas" in lower_text or "startup" in lower_text:
            customer = "B2B SaaS Founder"
        elif "analyst" in lower_text or "reporting" in lower_text:
            customer = "Operations & Data Reporting Lead"

        problem_stmt = title if len(title) > 20 else f"Manual operational bottleneck: {title}"
        underlying = f"Lack of automated data pipeline or integration connecting existing workflows."

        return ProblemExtractionResult(
            is_commercial_problem=True,
            problem_statement=problem_stmt[:250],
            underlying_problem=underlying,
            target_customer=customer,
            current_workaround=workaround or "Manual recurring operational tasks",
            frustration_severity=severity,
            reports_financial_loss=financial_loss,
            reported_hours_lost_per_week=hours_lost,
            frequency_cadence=cadence,
            explicit_budget_stated=budget,
            currently_paying_for_workaround=paying,
            actively_seeking_help=seeking,
            pain_quotes=pain_quotes,
            payment_quotes=payment_quotes,
            confidence_rating=0.85
        )

    def _extract_gemini(self, title: str, body: str, source: str) -> ProblemExtractionResult:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = (
            "You are an expert commercial opportunity analyst. Analyze this post and extract the commercial problem "
            "as strict JSON adhering to the required schema.\n\n"
            f"Title: {title}\nBody: {body}\nSource: {source}\n\n"
            "Return JSON matching: is_commercial_problem, problem_statement, underlying_problem, target_customer, "
            "current_workaround, frustration_severity ('none'|'mild'|'severe'|'blocking'), reports_financial_loss (bool), "
            "reported_hours_lost_per_week (float), frequency_cadence ('unknown'|'yearly'|'monthly'|'weekly'|'daily'|'continuous'), "
            "explicit_budget_stated (float or null), currently_paying_for_workaround (bool), actively_seeking_help (bool), "
            "pain_quotes (list of exact quotes), payment_quotes (list of exact quotes), confidence_rating (0.0 to 1.0)."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return ProblemExtractionResult(**parsed)
        raise RuntimeError(f"Gemini API returned {resp.status_code}")

    def _extract_openai(self, title: str, body: str, source: str) -> ProblemExtractionResult:
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        prompt = f"Analyze this post and extract the problem.\nTitle: {title}\nBody: {body}\nSource: {source}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a problem extraction engine. Respond only with JSON conforming to the ProblemExtractionResult schema."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            return ProblemExtractionResult(**parsed)
        raise RuntimeError(f"OpenAI API returned {resp.status_code}")
