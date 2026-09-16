"""SQLAlchemy 3NF Relational Database Models for OpportunityMiner."""

from datetime import datetime
from typing import Any
import json

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Integer,
    ForeignKey,
    LargeBinary,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RawSignal(Base):
    """Raw ingested post, comment, or job listing."""
    __tablename__ = "raw_signals"

    id = Column(String(64), primary_key=True)  # sha256(source + source_id)
    source = Column(String(32), nullable=False, index=True)  # reddit, hackernews, upwork, etc.
    source_url = Column(String(512), unique=True, nullable=False)
    author = Column(String(128), nullable=True)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)  # sha256(body)
    raw_metadata_json = Column(Text, default="{}")

    # Relationships
    problems = relationship("ExtractedProblem", back_populates="signal", cascade="all, delete-orphan")

    @property
    def raw_metadata(self) -> dict[str, Any]:
        try:
            return json.loads(self.raw_metadata_json) if self.raw_metadata_json else {}
        except Exception:
            return {}

    @raw_metadata.setter
    def raw_metadata(self, val: dict[str, Any]):
        self.raw_metadata_json = json.dumps(val)


class ExtractedProblem(Base):
    """Structured, atomic problem extracted from a raw signal."""
    __tablename__ = "extracted_problems"

    id = Column(String(32), primary_key=True)  # PR-XXXX
    signal_id = Column(String(64), ForeignKey("raw_signals.id"), nullable=False)
    problem_statement = Column(Text, nullable=False)
    underlying_problem = Column(Text, nullable=False)
    target_customer = Column(String(128), nullable=False)
    current_workaround = Column(Text, nullable=True)

    # Evidence rubrics (JSON serialized lists/dicts)
    pain_evidence_json = Column(Text, default="[]")
    frequency_evidence = Column(String(32), default="unknown")
    wtp_evidence_json = Column(Text, default="[]")

    embedding = Column(LargeBinary, nullable=True)  # Vector embedding bytes
    cluster_id = Column(String(32), ForeignKey("problem_clusters.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    signal = relationship("RawSignal", back_populates="problems")
    cluster = relationship("ProblemCluster", back_populates="problems")

    @property
    def pain_evidence(self) -> list:
        try:
            return json.loads(self.pain_evidence_json) if self.pain_evidence_json else []
        except Exception:
            return []

    @pain_evidence.setter
    def pain_evidence(self, val: list):
        self.pain_evidence_json = json.dumps(val)

    @property
    def wtp_evidence(self) -> list:
        try:
            return json.loads(self.wtp_evidence_json) if self.wtp_evidence_json else []
        except Exception:
            return []

    @wtp_evidence.setter
    def wtp_evidence(self, val: list):
        self.wtp_evidence_json = json.dumps(val)


class ProblemCluster(Base):
    """Semantic cluster of recurring problems with running centroid vector."""
    __tablename__ = "problem_clusters"

    id = Column(String(32), primary_key=True)  # CL-XXXX
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    centroid_embedding = Column(LargeBinary, nullable=True)
    mention_count = Column(Integer, default=1, nullable=False)
    unique_sources = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trend_velocity = Column(Float, default=1.0)  # mentions per week

    # Relationships
    problems = relationship("ExtractedProblem", back_populates="cluster")
    opportunity = relationship("Opportunity", back_populates="cluster", uselist=False)


class Opportunity(Base):
    """Commercialized opportunity record derived from a problem cluster."""
    __tablename__ = "opportunities"

    id = Column(String(32), primary_key=True)  # OP-XXXX
    cluster_id = Column(String(32), ForeignKey("problem_clusters.id"), unique=True, nullable=False)
    title = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False)  # AUTOMATION_SERVICE, DASHBOARD, etc.
    
    opportunity_score = Column(Float, index=True, nullable=False, default=0.0)
    confidence_score = Column(Float, default=0.0)
    evidence_level = Column(Integer, default=1)  # 1 to 5
    technical_feasibility = Column(Float, default=0.0)
    user_expertise_fit = Column(Float, default=0.0)
    
    score_breakdown_json = Column(Text, default="{}")
    solution_hypothesis_json = Column(Text, default="{}")
    commercial_packaging_json = Column(Text, default="{}")
    
    status = Column(String(32), default="NEW", index=True, nullable=False)
    # NEW, INVESTIGATING, VALIDATING, PROTOTYPING, CLIENT_CONTACTED, PAID_PROJECT, BUILDING, PRODUCTIZING, LAUNCHED, REJECTED, ARCHIVED
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cluster = relationship("ProblemCluster", back_populates="opportunity")
    competitors = relationship("Competitor", back_populates="opportunity", cascade="all, delete-orphan")
    validation_plans = relationship("ValidationPlan", back_populates="opportunity", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="opportunity", cascade="all, delete-orphan")

    @property
    def score_breakdown(self) -> dict:
        try:
            return json.loads(self.score_breakdown_json) if self.score_breakdown_json else {}
        except Exception:
            return {}

    @score_breakdown.setter
    def score_breakdown(self, val: dict):
        self.score_breakdown_json = json.dumps(val)

    @property
    def solution_hypothesis(self) -> dict:
        try:
            return json.loads(self.solution_hypothesis_json) if self.solution_hypothesis_json else {}
        except Exception:
            return {}

    @solution_hypothesis.setter
    def solution_hypothesis(self, val: dict):
        self.solution_hypothesis_json = json.dumps(val)

    @property
    def commercial_packaging(self) -> dict:
        try:
            return json.loads(self.commercial_packaging_json) if self.commercial_packaging_json else {}
        except Exception:
            return {}

    @commercial_packaging.setter
    def commercial_packaging(self, val: dict):
        self.commercial_packaging_json = json.dumps(val)


class Competitor(Base):
    """Existing competitor, tool, or alternative in the problem domain."""
    __tablename__ = "competitors"

    id = Column(String(32), primary_key=True)
    opportunity_id = Column(String(32), ForeignKey("opportunities.id"), nullable=False)
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=True)
    pricing_summary = Column(String(256), nullable=True)
    reported_weakness = Column(Text, nullable=True)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="competitors")


class ValidationPlan(Base):
    """Discovery validation steps and customer interview plan."""
    __tablename__ = "validation_plans"

    id = Column(String(32), primary_key=True)
    opportunity_id = Column(String(32), ForeignKey("opportunities.id"), nullable=False)
    target_interviewees = Column(Text, nullable=False)
    qualifying_questions_json = Column(Text, default="[]")
    landing_page_pitch = Column(Text, nullable=True)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="validation_plans")

    @property
    def qualifying_questions(self) -> list:
        try:
            return json.loads(self.qualifying_questions_json) if self.qualifying_questions_json else []
        except Exception:
            return []

    @qualifying_questions.setter
    def qualifying_questions(self, val: list):
        self.qualifying_questions_json = json.dumps(val)


class UserFeedback(Base):
    """Explicit feedback action recorded by the user in Streamlit CRM."""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(32), ForeignKey("opportunities.id"), nullable=False)
    action = Column(String(32), nullable=False)  # USEFUL, REJECTED, TOO_DIFFICULT, NOT_MY_NICHE, CONTACTED, etc.
    notes = Column(Text, nullable=True)
    feedback_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="feedbacks")


# Compound indexes for fast querying
Index("idx_raw_signals_source_pub", RawSignal.source, RawSignal.published_at)
Index("idx_opp_score_status", Opportunity.opportunity_score, Opportunity.status)
