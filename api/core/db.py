"""PostgreSQL database layer for SEHRA Analyzer."""

import os
import json
import uuid
import logging
from datetime import datetime, date, timedelta
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Date, Text, JSON, ForeignKey, Enum as SAEnum,
    Index, text as sa_text, inspect, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger("sehra.db")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sehra:sehra_pass@localhost:5432/sehra_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# --- ORM Models ---

class SEHRA(Base):
    __tablename__ = "sehras"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    country = Column(String, nullable=False)
    province = Column(String, default="")
    district = Column(String, default="")
    assessment_date = Column(Date, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="draft")  # draft, reviewed, published
    pdf_filename = Column(String, nullable=False)
    raw_extracted_data = Column(JSON, default=dict)
    executive_summary = Column(Text, default="")
    recommendations = Column(Text, default="")

    components = relationship("ComponentAnalysis", back_populates="sehra", cascade="all, delete-orphan")
    shared_reports = relationship("SharedReport", back_populates="sehra", cascade="all, delete-orphan")


class ComponentAnalysis(Base):
    __tablename__ = "component_analyses"
    __table_args__ = (
        Index("ix_component_analyses_sehra_id", "sehra_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sehra_id = Column(String, ForeignKey("sehras.id", ondelete="CASCADE"), nullable=False)
    component = Column(String, nullable=False)  # context, policy, service_delivery, human_resources, supply_chain, barriers
    enabler_count = Column(Integer, default=0)
    barrier_count = Column(Integer, default=0)
    items = Column(JSON, default=list)  # [{question, item_id, yes_no, remark, score, is_reverse}]
    numeric_data = Column(JSON, default=list)  # Extracted numeric/demographic data

    sehra = relationship("SEHRA", back_populates="components")
    qualitative_entries = relationship("QualitativeEntry", back_populates="component_analysis", cascade="all, delete-orphan")
    report_sections = relationship("ReportSection", back_populates="component_analysis", cascade="all, delete-orphan")


class QualitativeEntry(Base):
    __tablename__ = "qualitative_entries"
    __table_args__ = (
        Index("ix_qualitative_entries_component_analysis_id", "component_analysis_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_analysis_id = Column(String, ForeignKey("component_analyses.id", ondelete="CASCADE"), nullable=False)
    remark_text = Column(Text, nullable=False)
    item_id = Column(String, default="")
    theme = Column(String, nullable=False)
    classification = Column(String, nullable=False)  # enabler, barrier, strength, weakness
    confidence = Column(Float, default=0.0)
    edited_by_human = Column(Boolean, default=False)

    component_analysis = relationship("ComponentAnalysis", back_populates="qualitative_entries")


class ReportSection(Base):
    __tablename__ = "report_sections"
    __table_args__ = (
        Index("ix_report_sections_component_analysis_id", "component_analysis_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_analysis_id = Column(String, ForeignKey("component_analyses.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String, nullable=False)  # enabler_summary, barrier_summary, action_points
    content = Column(Text, default="")
    edited_by_human = Column(Boolean, default=False)

    component_analysis = relationship("ComponentAnalysis", back_populates="report_sections")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="analyst")  # analyst, admin


class SharedReport(Base):
    __tablename__ = "shared_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sehra_id = Column(String, ForeignKey("sehras.id", ondelete="CASCADE"), nullable=False)
    share_token = Column(String, unique=True, nullable=False)
    passcode_hash = Column(String, nullable=False)
    created_by = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    cached_html = Column(Text, default="")

    sehra = relationship("SEHRA", back_populates="shared_reports")
    views = relationship("ReportView", back_populates="shared_report", cascade="all, delete-orphan")


class ReportView(Base):
    __tablename__ = "report_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shared_report_id = Column(String, ForeignKey("shared_reports.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    viewer_ip = Column(String, default="")
    viewer_user_agent = Column(String, default="")
    passcode_correct = Column(Boolean, default=False)

    shared_report = relationship("SharedReport", back_populates="views")


class CodebookOverride(Base):
    """Store codebook overrides in DB so edits persist across deploys."""
    __tablename__ = "codebook_overrides"

    id = Column(String, primary_key=True, default="current")
    data = Column(JSON, nullable=False)  # Full codebook JSON
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FormDraft(Base):
    """Save partial form progress for resume later."""
    __tablename__ = "form_drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user = Column(String, nullable=False)
    section_progress = Column(Integer, default=0)  # Which step they're on
    responses = Column(JSON, default=dict)  # All answers so far
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class CopilotConversation(Base):
    """Server-side copilot conversation storage per user."""
    __tablename__ = "copilot_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user = Column(String, nullable=False, index=True)
    title = Column(String, default="New conversation")
    sehra_id = Column(String, nullable=True)
    sehra_label = Column(String, nullable=True)
    messages = Column(JSON, default=list)  # List of message dicts
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AICorrection(Base):
    """Track user corrections to AI-generated analysis for learning."""
    __tablename__ = "ai_corrections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user = Column(String, nullable=False)
    sehra_id = Column(String, nullable=True)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    context = Column(String, default="")  # e.g. "copilot_message", "report_section", "classification"
    message_id = Column(String, nullable=True)  # ID of the copilot message if applicable
    created_at = Column(DateTime, default=datetime.utcnow)


class AIFeedback(Base):
    """Track thumbs up/down on AI responses."""
    __tablename__ = "ai_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user = Column(String, nullable=False)
    message_id = Column(String, nullable=False)  # copilot message ID
    conversation_id = Column(String, nullable=True)
    rating = Column(String, nullable=False)  # "up" or "down"
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class CopilotAuditLog(Base):
    """Audit trail for copilot tool actions."""
    __tablename__ = "copilot_audit_log"
    __table_args__ = (
        Index("ix_copilot_audit_log_sehra_id", "sehra_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sehra_id = Column(String, ForeignKey("sehras.id", ondelete="CASCADE"), nullable=True)
    user = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    args = Column(JSON, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    status = Column(String, default="applied")  # applied | rolled_back
    created_at = Column(DateTime, default=func.now())


# --- Database Operations ---

def init_db():
    """Create all tables and run migrations."""
    Base.metadata.create_all(engine)
    _run_migrations()
    logger.info("Database initialized")


def _run_migrations():
    """Add new columns to existing tables if they don't exist."""
    with engine.connect() as conn:
        inspector = inspect(engine)

        # Add executive_summary and recommendations to sehras
        sehras_cols = {c["name"] for c in inspector.get_columns("sehras")}
        if "executive_summary" not in sehras_cols:
            conn.execute(sa_text("ALTER TABLE sehras ADD COLUMN executive_summary TEXT DEFAULT ''"))
            logger.info("Migration: added executive_summary to sehras")
        if "recommendations" not in sehras_cols:
            conn.execute(sa_text("ALTER TABLE sehras ADD COLUMN recommendations TEXT DEFAULT ''"))
            logger.info("Migration: added recommendations to sehras")

        # Add numeric_data to component_analyses
        ca_cols = {c["name"] for c in inspector.get_columns("component_analyses")}
        if "numeric_data" not in ca_cols:
            conn.execute(sa_text("ALTER TABLE component_analyses ADD COLUMN numeric_data JSON DEFAULT '[]'"))
            logger.info("Migration: added numeric_data to component_analyses")

        conn.commit()


@contextmanager
def get_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_sehra(country: str, district: str, province: str,
                 assessment_date: date | None, pdf_filename: str,
                 raw_data: dict) -> str:
    """Create a new SEHRA record. Returns the ID."""
    with get_session() as session:
        sehra = SEHRA(
            country=country,
            province=province,
            district=district,
            assessment_date=assessment_date,
            pdf_filename=pdf_filename,
            raw_extracted_data=raw_data,
        )
        session.add(sehra)
        session.flush()
        logger.info("Created SEHRA: %s (%s, %s)", sehra.id, country, district)
        return sehra.id


def save_component_analysis(sehra_id: str, component: str,
                            enabler_count: int, barrier_count: int,
                            items: list) -> str:
    """Save quantitative analysis for a component. Returns ID."""
    with get_session() as session:
        ca = ComponentAnalysis(
            sehra_id=sehra_id,
            component=component,
            enabler_count=enabler_count,
            barrier_count=barrier_count,
            items=items,
        )
        session.add(ca)
        session.flush()
        return ca.id


def save_qualitative_entries(component_analysis_id: str, entries: list[dict]):
    """Save qualitative classification entries for a component.

    Each entry: {remark_text, item_id, theme, classification, confidence}
    """
    with get_session() as session:
        for entry in entries:
            qe = QualitativeEntry(
                component_analysis_id=component_analysis_id,
                remark_text=entry["remark_text"],
                item_id=entry.get("item_id", ""),
                theme=entry["theme"],
                classification=entry["classification"],
                confidence=entry.get("confidence", 0.0),
            )
            session.add(qe)


def save_report_section(component_analysis_id: str, section_type: str, content: str):
    """Save a report section (summary or action points)."""
    with get_session() as session:
        rs = ReportSection(
            component_analysis_id=component_analysis_id,
            section_type=section_type,
            content=content,
        )
        session.add(rs)


def save_executive_summary(sehra_id: str, executive_summary: str, recommendations: str):
    """Save executive summary and recommendations for a SEHRA."""
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if sehra:
            sehra.executive_summary = executive_summary
            sehra.recommendations = recommendations
            logger.info("Saved executive summary for SEHRA %s", sehra_id)


def get_executive_summary(sehra_id: str) -> dict:
    """Get executive summary and recommendations for a SEHRA."""
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if sehra:
            return {
                "executive_summary": sehra.executive_summary or "",
                "recommendations": sehra.recommendations or "",
            }
        return {"executive_summary": "", "recommendations": ""}


def _sehra_to_dict(sehra) -> dict:
    """Convert a SEHRA ORM object to a dict (reusable helper)."""
    return {
        "id": sehra.id,
        "country": sehra.country,
        "province": sehra.province,
        "district": sehra.district,
        "assessment_date": sehra.assessment_date.isoformat() if sehra.assessment_date else None,
        "upload_date": sehra.upload_date.isoformat() if sehra.upload_date else None,
        "status": sehra.status,
        "pdf_filename": sehra.pdf_filename,
        "raw_extracted_data": sehra.raw_extracted_data,
        "executive_summary": sehra.executive_summary or "",
        "recommendations": sehra.recommendations or "",
    }


def get_sehra(sehra_id: str) -> dict | None:
    """Get a SEHRA by ID (basic fields only)."""
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if not sehra:
            return None
        return _sehra_to_dict(sehra)


def get_sehra_with_relations(sehra_id: str) -> dict | None:
    """Get a SEHRA with all related data in a single eager-loaded query.

    Loads SEHRA -> ComponentAnalysis -> QualitativeEntry/ReportSection
    in one round-trip using joinedload, avoiding N+1 queries.
    """
    with get_session() as session:
        sehra = (
            session.query(SEHRA)
            .options(
                joinedload(SEHRA.components)
                .joinedload(ComponentAnalysis.qualitative_entries),
                joinedload(SEHRA.components)
                .joinedload(ComponentAnalysis.report_sections),
            )
            .filter(SEHRA.id == sehra_id)
            .first()
        )
        if not sehra:
            return None
        result = _sehra_to_dict(sehra)
        result["components"] = []
        for ca in sehra.components:
            result["components"].append({
                "id": ca.id,
                "component": ca.component,
                "enabler_count": ca.enabler_count,
                "barrier_count": ca.barrier_count,
                "items": ca.items or [],
                "qualitative_entries": [
                    {
                        "id": e.id,
                        "remark_text": e.remark_text,
                        "item_id": e.item_id,
                        "theme": e.theme,
                        "classification": e.classification,
                        "confidence": e.confidence,
                        "edited_by_human": e.edited_by_human,
                    }
                    for e in ca.qualitative_entries
                ],
                "report_sections": {
                    s.section_type: {
                        "id": s.id,
                        "content": s.content,
                        "edited_by_human": s.edited_by_human,
                    }
                    for s in ca.report_sections
                },
            })
        return result


def list_sehras() -> list[dict]:
    """List all SEHRAs (summary only)."""
    with get_session() as session:
        sehras = session.query(SEHRA).order_by(SEHRA.upload_date.desc()).all()
        return [
            {
                "id": s.id,
                "country": s.country,
                "district": s.district,
                "province": s.province,
                "assessment_date": s.assessment_date.isoformat() if s.assessment_date else None,
                "upload_date": s.upload_date.isoformat() if s.upload_date else None,
                "status": s.status,
                "pdf_filename": s.pdf_filename,
            }
            for s in sehras
        ]


def get_component_analyses(sehra_id: str) -> list[dict]:
    """Get all component analyses for a SEHRA using eager loading."""
    with get_session() as session:
        cas = (
            session.query(ComponentAnalysis)
            .options(
                joinedload(ComponentAnalysis.qualitative_entries),
                joinedload(ComponentAnalysis.report_sections),
            )
            .filter(ComponentAnalysis.sehra_id == sehra_id)
            .all()
        )
        results = []
        for ca in cas:
            results.append({
                "id": ca.id,
                "component": ca.component,
                "enabler_count": ca.enabler_count,
                "barrier_count": ca.barrier_count,
                "items": ca.items or [],
                "qualitative_entries": [
                    {
                        "id": e.id,
                        "remark_text": e.remark_text,
                        "item_id": e.item_id,
                        "theme": e.theme,
                        "classification": e.classification,
                        "confidence": e.confidence,
                        "edited_by_human": e.edited_by_human,
                    }
                    for e in ca.qualitative_entries
                ],
                "report_sections": {
                    s.section_type: {"id": s.id, "content": s.content, "edited_by_human": s.edited_by_human}
                    for s in ca.report_sections
                },
            })
        return results


def get_qualitative_entry(entry_id: str) -> dict | None:
    """Get a single qualitative entry by ID."""
    with get_session() as session:
        entry = session.query(QualitativeEntry).filter(QualitativeEntry.id == entry_id).first()
        if not entry:
            return None
        return {
            "id": entry.id,
            "remark_text": entry.remark_text,
            "item_id": entry.item_id,
            "theme": entry.theme,
            "classification": entry.classification,
            "confidence": entry.confidence,
            "edited_by_human": entry.edited_by_human,
        }


def get_report_section(section_id: str) -> dict | None:
    """Get a single report section by ID."""
    with get_session() as session:
        section = session.query(ReportSection).filter(ReportSection.id == section_id).first()
        if not section:
            return None
        return {
            "id": section.id,
            "section_type": section.section_type,
            "content": section.content,
            "edited_by_human": section.edited_by_human,
        }


def update_qualitative_entry(entry_id: str, theme: str = None,
                             classification: str = None):
    """Update a qualitative entry (human review edit)."""
    with get_session() as session:
        entry = session.query(QualitativeEntry).filter(QualitativeEntry.id == entry_id).first()
        if entry:
            if theme is not None:
                entry.theme = theme
            if classification is not None:
                entry.classification = classification
            entry.edited_by_human = True


def update_report_section(section_id: str, content: str):
    """Update a report section (human review edit)."""
    with get_session() as session:
        section = session.query(ReportSection).filter(ReportSection.id == section_id).first()
        if section:
            section.content = content
            section.edited_by_human = True


def update_sehra_fields(sehra_id: str, **kwargs) -> bool:
    """Partially update SEHRA fields. Returns True if found."""
    allowed = {"executive_summary", "recommendations", "status"}
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if not sehra:
            return False
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(sehra, key, value)
        return True


def update_sehra_status(sehra_id: str, status: str):
    """Update SEHRA status (draft/reviewed/published)."""
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if sehra:
            sehra.status = status


def delete_sehra(sehra_id: str):
    """Delete a SEHRA and all related data."""
    with get_session() as session:
        sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
        if sehra:
            session.delete(sehra)


def batch_approve_entries(sehra_id: str, confidence_threshold: float):
    """Mark all entries above confidence threshold as reviewed for a SEHRA."""
    with get_session() as session:
        cas = (
            session.query(ComponentAnalysis)
            .filter(ComponentAnalysis.sehra_id == sehra_id)
            .all()
        )
        count = 0
        for ca in cas:
            entries = (
                session.query(QualitativeEntry)
                .filter(
                    QualitativeEntry.component_analysis_id == ca.id,
                    QualitativeEntry.confidence >= confidence_threshold,
                    QualitativeEntry.edited_by_human == False,
                )
                .all()
            )
            for entry in entries:
                entry.edited_by_human = True
                count += 1
        logger.info("Batch approved %d entries above %.0f%% confidence", count, confidence_threshold * 100)
        return count


# --- Share Operations ---

def create_shared_report(sehra_id: str, passcode_hash: str, created_by: str,
                         expires_days: int | None, cached_html: str) -> str:
    """Create a shared report link. Returns the share token."""
    import secrets
    token = secrets.token_urlsafe(32)

    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    with get_session() as session:
        sr = SharedReport(
            sehra_id=sehra_id,
            share_token=token,
            passcode_hash=passcode_hash,
            created_by=created_by,
            expires_at=expires_at,
            cached_html=cached_html,
        )
        session.add(sr)
        session.flush()
        logger.info("Created shared report: token=%s..., sehra=%s", token[:8], sehra_id)
        return token


def get_shared_report_by_token(token: str) -> dict | None:
    """Look up a shared report by its token."""
    with get_session() as session:
        sr = session.query(SharedReport).filter(SharedReport.share_token == token).first()
        if not sr:
            return None
        return {
            "id": sr.id,
            "sehra_id": sr.sehra_id,
            "share_token": sr.share_token,
            "passcode_hash": sr.passcode_hash,
            "created_by": sr.created_by,
            "created_at": sr.created_at.isoformat() if sr.created_at else None,
            "expires_at": sr.expires_at.isoformat() if sr.expires_at else None,
            "is_active": sr.is_active,
            "cached_html": sr.cached_html,
        }


def verify_share_passcode(token: str, passcode: str) -> bool:
    """Verify passcode for a shared report."""
    import bcrypt
    sr = get_shared_report_by_token(token)
    if not sr:
        return False
    try:
        return bcrypt.checkpw(
            passcode.encode("utf-8"),
            sr["passcode_hash"].encode("utf-8"),
        )
    except Exception:
        return False


def log_report_view(shared_report_id: str, viewer_ip: str = "",
                    viewer_user_agent: str = "", passcode_correct: bool = False):
    """Log a report view attempt."""
    with get_session() as session:
        rv = ReportView(
            shared_report_id=shared_report_id,
            viewer_ip=viewer_ip,
            viewer_user_agent=viewer_user_agent,
            passcode_correct=passcode_correct,
        )
        session.add(rv)


def get_report_views(shared_report_id: str) -> list[dict]:
    """Get all views for a shared report."""
    with get_session() as session:
        views = (
            session.query(ReportView)
            .filter(ReportView.shared_report_id == shared_report_id)
            .order_by(ReportView.viewed_at.desc())
            .all()
        )
        return [
            {
                "id": v.id,
                "viewed_at": v.viewed_at.isoformat() if v.viewed_at else None,
                "viewer_ip": v.viewer_ip,
                "viewer_user_agent": v.viewer_user_agent,
                "passcode_correct": v.passcode_correct,
            }
            for v in views
        ]


def count_failed_attempts(shared_report_id: str, minutes: int = 60) -> int:
    """Count failed passcode attempts in the last N minutes."""
    with get_session() as session:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return (
            session.query(ReportView)
            .filter(
                ReportView.shared_report_id == shared_report_id,
                ReportView.passcode_correct == False,
                ReportView.viewed_at >= cutoff,
            )
            .count()
        )


def revoke_shared_report(token: str):
    """Revoke (deactivate) a shared report."""
    with get_session() as session:
        sr = session.query(SharedReport).filter(SharedReport.share_token == token).first()
        if sr:
            sr.is_active = False
            logger.info("Revoked shared report: token=%s...", token[:8])


def list_shared_reports(sehra_id: str) -> list[dict]:
    """List all shared reports for a SEHRA."""
    with get_session() as session:
        srs = (
            session.query(SharedReport)
            .filter(SharedReport.sehra_id == sehra_id)
            .order_by(SharedReport.created_at.desc())
            .all()
        )
        results = []
        for sr in srs:
            view_count = session.query(ReportView).filter(
                ReportView.shared_report_id == sr.id,
                ReportView.passcode_correct == True,
            ).count()
            results.append({
                "id": sr.id,
                "share_token": sr.share_token,
                "created_by": sr.created_by,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
                "expires_at": sr.expires_at.isoformat() if sr.expires_at else None,
                "is_active": sr.is_active,
                "view_count": view_count,
            })
        return results


# --- Form Draft Operations ---

def save_form_draft(user: str, section_progress: int, responses: dict) -> str:
    """Save or update a form draft. Returns the draft ID."""
    with get_session() as session:
        # Check for existing draft by user
        draft = session.query(FormDraft).filter(FormDraft.user == user).first()
        if draft:
            draft.section_progress = section_progress
            draft.responses = responses
            draft.updated_at = datetime.utcnow()
            return draft.id
        else:
            draft = FormDraft(
                user=user,
                section_progress=section_progress,
                responses=responses,
            )
            session.add(draft)
            session.flush()
            return draft.id


def get_form_draft(user: str) -> dict | None:
    """Get the current form draft for a user."""
    with get_session() as session:
        draft = session.query(FormDraft).filter(FormDraft.user == user).first()
        if not draft:
            return None
        return {
            "id": draft.id,
            "user": draft.user,
            "section_progress": draft.section_progress,
            "responses": draft.responses or {},
            "created_at": draft.created_at.isoformat() if draft.created_at else None,
            "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
        }


def delete_form_draft(user: str):
    """Delete a user's form draft after successful submission."""
    with get_session() as session:
        draft = session.query(FormDraft).filter(FormDraft.user == user).first()
        if draft:
            session.delete(draft)


# --- Codebook Override Operations ---

def save_codebook_override(codebook_data: dict):
    """Save codebook to DB so edits persist across deploys."""
    with get_session() as session:
        override = session.query(CodebookOverride).filter(
            CodebookOverride.id == "current"
        ).first()
        if override:
            override.data = codebook_data
            override.updated_at = datetime.utcnow()
        else:
            override = CodebookOverride(id="current", data=codebook_data)
            session.add(override)


def get_codebook_override() -> dict | None:
    """Get the DB-stored codebook override, if any."""
    with get_session() as session:
        override = session.query(CodebookOverride).filter(
            CodebookOverride.id == "current"
        ).first()
        if override and override.data:
            return override.data
        return None

# --- Conversation Operations ---

def list_conversations(user: str) -> list[dict]:
    """List all conversations for a user, ordered by updatedAt desc.

    Returns summary only (no full messages).
    """
    with get_session() as session:
        convos = (
            session.query(CopilotConversation)
            .filter(CopilotConversation.user == user)
            .order_by(CopilotConversation.updated_at.desc())
            .all()
        )
        return [
            {
                "id": c.id,
                "title": c.title,
                "sehra_id": c.sehra_id,
                "sehra_label": c.sehra_label,
                "message_count": len(c.messages) if c.messages else 0,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in convos
        ]


def get_conversation(conversation_id: str, user: str) -> dict | None:
    """Get full conversation with messages, verify user owns it."""
    with get_session() as session:
        convo = (
            session.query(CopilotConversation)
            .filter(
                CopilotConversation.id == conversation_id,
                CopilotConversation.user == user,
            )
            .first()
        )
        if not convo:
            return None
        return {
            "id": convo.id,
            "title": convo.title,
            "sehra_id": convo.sehra_id,
            "sehra_label": convo.sehra_label,
            "messages": convo.messages or [],
            "created_at": convo.created_at.isoformat() if convo.created_at else None,
            "updated_at": convo.updated_at.isoformat() if convo.updated_at else None,
        }


def save_conversation(conversation_id: str, user: str, title: str,
                       messages: list, sehra_id: str | None,
                       sehra_label: str | None) -> str:
    """Upsert a conversation. Returns the conversation ID."""
    with get_session() as session:
        convo = (
            session.query(CopilotConversation)
            .filter(
                CopilotConversation.id == conversation_id,
                CopilotConversation.user == user,
            )
            .first()
        )
        if convo:
            convo.title = title
            convo.messages = messages
            convo.sehra_id = sehra_id
            convo.sehra_label = sehra_label
            convo.updated_at = datetime.utcnow()
            return convo.id
        else:
            convo = CopilotConversation(
                id=conversation_id,
                user=user,
                title=title,
                messages=messages,
                sehra_id=sehra_id,
                sehra_label=sehra_label,
            )
            session.add(convo)
            session.flush()
            return convo.id


def delete_conversation(conversation_id: str, user: str) -> bool:
    """Delete a conversation if user owns it. Returns success."""
    with get_session() as session:
        convo = (
            session.query(CopilotConversation)
            .filter(
                CopilotConversation.id == conversation_id,
                CopilotConversation.user == user,
            )
            .first()
        )
        if not convo:
            return False
        session.delete(convo)
        return True


# --- AI Correction / Feedback Operations ---

def save_ai_correction(user: str, original_text: str, corrected_text: str,
                        context: str, sehra_id: str | None,
                        message_id: str | None) -> str:
    """Save an AI correction. Returns the correction ID."""
    with get_session() as session:
        correction = AICorrection(
            user=user,
            original_text=original_text,
            corrected_text=corrected_text,
            context=context,
            sehra_id=sehra_id,
            message_id=message_id,
        )
        session.add(correction)
        session.flush()
        return correction.id


def save_ai_feedback(user: str, message_id: str, conversation_id: str | None,
                      rating: str, comment: str) -> str:
    """Save AI feedback (thumbs up/down). Returns the feedback ID."""
    with get_session() as session:
        feedback = AIFeedback(
            user=user,
            message_id=message_id,
            conversation_id=conversation_id,
            rating=rating,
            comment=comment,
        )
        session.add(feedback)
        session.flush()
        return feedback.id


def get_ai_corrections(user: str | None = None, sehra_id: str | None = None,
                        limit: int = 50) -> list[dict]:
    """Get corrections, optionally filtered by user/sehra."""
    with get_session() as session:
        query = session.query(AICorrection)
        if user:
            query = query.filter(AICorrection.user == user)
        if sehra_id:
            query = query.filter(AICorrection.sehra_id == sehra_id)
        corrections = (
            query.order_by(AICorrection.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": c.id,
                "user": c.user,
                "sehra_id": c.sehra_id,
                "original_text": c.original_text,
                "corrected_text": c.corrected_text,
                "context": c.context,
                "message_id": c.message_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in corrections
        ]


def get_corrections_for_context(sehra_id: str | None = None,
                                 limit: int = 10) -> list[dict]:
    """Get recent corrections to inject into copilot context for learning."""
    with get_session() as session:
        query = session.query(AICorrection)
        if sehra_id:
            query = query.filter(AICorrection.sehra_id == sehra_id)
        corrections = (
            query.order_by(AICorrection.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "original_text": c.original_text,
                "corrected_text": c.corrected_text,
                "context": c.context,
            }
            for c in corrections
        ]


# --- Copilot Audit Log Operations ---

def log_copilot_action(sehra_id: str | None, user: str, tool_name: str,
                       args: dict, old_value: dict | None,
                       new_value: dict | None) -> str:
    """Log a copilot tool action to the audit trail. Returns the audit log ID."""
    with get_session() as session:
        entry = CopilotAuditLog(
            sehra_id=sehra_id,
            user=user,
            tool_name=tool_name,
            args=args,
            old_value=old_value,
            new_value=new_value,
            status="applied",
        )
        session.add(entry)
        session.flush()
        logger.info("Audit log: user=%s tool=%s sehra=%s", user, tool_name, sehra_id)
        return entry.id


def get_audit_log(sehra_id: str | None = None, user: str | None = None,
                  limit: int = 50) -> list[dict]:
    """Get audit log entries, optionally filtered by sehra_id and/or user."""
    with get_session() as session:
        query = session.query(CopilotAuditLog)
        if sehra_id:
            query = query.filter(CopilotAuditLog.sehra_id == sehra_id)
        if user:
            query = query.filter(CopilotAuditLog.user == user)
        entries = (
            query.order_by(CopilotAuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": e.id,
                "sehra_id": e.sehra_id,
                "user": e.user,
                "tool_name": e.tool_name,
                "args": e.args,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]


def rollback_action(audit_id: str) -> dict:
    """Rollback a copilot action by restoring old_value and marking as rolled_back.

    Returns a dict with success status and details.
    """
    with get_session() as session:
        entry = session.query(CopilotAuditLog).filter(
            CopilotAuditLog.id == audit_id
        ).first()
        if not entry:
            return {"success": False, "error": "Audit entry not found"}
        if entry.status == "rolled_back":
            return {"success": False, "error": "Action already rolled back"}
        if entry.old_value is None:
            return {"success": False, "error": "No old value to restore (read-only action)"}

        tool = entry.tool_name
        old = entry.old_value

        try:
            if tool == "edit_entry":
                entry_id = entry.args.get("entry_id")
                if entry_id:
                    qe = session.query(QualitativeEntry).filter(
                        QualitativeEntry.id == entry_id
                    ).first()
                    if qe:
                        if "theme" in old:
                            qe.theme = old["theme"]
                        if "classification" in old:
                            qe.classification = old["classification"]

            elif tool == "edit_report_section":
                section_id = entry.args.get("section_id")
                if section_id:
                    rs = session.query(ReportSection).filter(
                        ReportSection.id == section_id
                    ).first()
                    if rs and "content" in old:
                        rs.content = old["content"]

            elif tool == "edit_executive_summary":
                sehra_id = entry.args.get("sehra_id") or entry.sehra_id
                if sehra_id:
                    sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
                    if sehra:
                        if "executive_summary" in old:
                            sehra.executive_summary = old["executive_summary"]
                        if "recommendations" in old:
                            sehra.recommendations = old["recommendations"]

            elif tool == "change_status":
                sehra_id = entry.args.get("sehra_id") or entry.sehra_id
                if sehra_id:
                    sehra = session.query(SEHRA).filter(SEHRA.id == sehra_id).first()
                    if sehra and "status" in old:
                        sehra.status = old["status"]

            else:
                return {"success": False, "error": f"Rollback not supported for tool '{tool}'"}

            entry.status = "rolled_back"
            logger.info("Rolled back audit entry %s (tool=%s)", audit_id, tool)
            return {"success": True, "audit_id": audit_id, "tool_name": tool}

        except Exception as e:
            logger.exception("Rollback failed for audit entry %s", audit_id)
            return {"success": False, "error": f"Rollback failed: {str(e)}"}
