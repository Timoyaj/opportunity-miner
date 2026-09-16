"""Database engine, session management, and table initializer."""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

_engine = None
_SessionFactory = None


def get_config_db_url() -> str:
    """Retrieve database URL from environment or settings.yaml."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    # Check settings.yaml
    config_path = Path(__file__).resolve().parents[3] / "config" / "settings.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "database" in data and "url" in data["database"]:
                    return data["database"]["url"]
        except Exception:
            pass

    return "sqlite:///data/opportunity_miner.db"


def get_engine():
    """Retrieve or create SQLAlchemy Engine."""
    global _engine
    if _engine is None:
        db_url = get_config_db_url()
        
        # Ensure directory exists for sqlite
        if db_url.startswith("sqlite:///"):
            rel_path = db_url.replace("sqlite:///", "")
            # If relative, resolve relative to project root
            if not os.path.isabs(rel_path):
                project_root = Path(__file__).resolve().parents[3]
                abs_path = project_root / rel_path
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                db_url = f"sqlite:///{abs_path}"

        _engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
    return _engine


def get_session_factory():
    """Retrieve or create session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionFactory


def init_db():
    """Create all tables in the database if they don't already exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    init_db()
    SessionFactory = get_session_factory()
    session: Session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
