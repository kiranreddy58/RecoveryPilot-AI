from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import get_settings, IS_VERCEL

settings = get_settings()

engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models so they register with Base.metadata
    from app.models import (
        RecoveryEvent, RecoveryCase, CaseAuditEvent,
        Diagnosis, Strategy, RecoveryAction, GuardianDecision, Escalation,
        PromiseToPay, Subscription, Invoice, BatchRun,
    )
    Base.metadata.create_all(bind=engine)

    # SQLite dynamic column migration check
    if settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check case_audit_events table
            try:
                result = conn.execute(text("PRAGMA table_info(case_audit_events)"))
                existing_cols = {row[1] for row in result.fetchall()}
                if "previous_event_hash" not in existing_cols:
                    conn.execute(text("ALTER TABLE case_audit_events ADD COLUMN previous_event_hash VARCHAR(64)"))
                if "current_event_hash" not in existing_cols:
                    conn.execute(text("ALTER TABLE case_audit_events ADD COLUMN current_event_hash VARCHAR(64)"))
                conn.commit()
            except Exception:
                pass

    # Auto-seed demo data on Vercel cold starts
    if IS_VERCEL:
        try:
            from app.core.seed import seed_demo_data
            db = SessionLocal()
            try:
                seed_demo_data(db)
            finally:
                db.close()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Seed failed (non-fatal): {e}")

# Run on import to ensure test clients always have current schema
try:
    init_db()
except Exception:
    pass
