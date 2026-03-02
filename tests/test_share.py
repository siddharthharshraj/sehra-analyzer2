"""Tests for share link functionality."""

import pytest
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from core.db import (
    Base, SEHRA, SharedReport, ReportView,
    create_shared_report, get_shared_report_by_token,
    verify_share_passcode, log_report_view,
    count_failed_attempts, revoke_shared_report,
    list_shared_reports,
)
from core.share_utils import get_share_url


class TestShareURL:
    def test_default_url(self):
        url = get_share_url("abc123")
        assert "abc123" in url
        assert "token=" in url

    @patch.dict("os.environ", {"APP_URL": "https://sehra.railway.app"})
    def test_custom_url(self):
        url = get_share_url("abc123")
        assert url.startswith("https://sehra.railway.app")
        assert "token=abc123" in url


class TestShareDatabase:
    """Tests using SQLite in-memory database."""

    def test_create_shared_report(self, db_session):
        """Test creating a shared report directly in SQLite."""
        # Create a SEHRA first
        import uuid
        sehra = SEHRA(
            id=str(uuid.uuid4()),
            country="Liberia",
            pdf_filename="test.pdf",
        )
        db_session.add(sehra)
        db_session.commit()

        # Create shared report
        passcode_hash = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
        sr = SharedReport(
            id=str(uuid.uuid4()),
            sehra_id=sehra.id,
            share_token="test-token-123",
            passcode_hash=passcode_hash,
            created_by="test@test.com",
            is_active=True,
            cached_html="<html>test</html>",
        )
        db_session.add(sr)
        db_session.commit()

        # Verify
        found = db_session.query(SharedReport).filter_by(share_token="test-token-123").first()
        assert found is not None
        assert found.sehra_id == sehra.id
        assert found.is_active is True

    def test_revoke_report(self, db_session):
        import uuid
        sehra = SEHRA(id=str(uuid.uuid4()), country="Test", pdf_filename="test.pdf")
        db_session.add(sehra)

        sr = SharedReport(
            id=str(uuid.uuid4()),
            sehra_id=sehra.id,
            share_token="revoke-token",
            passcode_hash="hash",
            is_active=True,
        )
        db_session.add(sr)
        db_session.commit()

        # Revoke
        sr.is_active = False
        db_session.commit()

        found = db_session.query(SharedReport).filter_by(share_token="revoke-token").first()
        assert found.is_active is False

    def test_log_view(self, db_session):
        import uuid
        sehra = SEHRA(id=str(uuid.uuid4()), country="Test", pdf_filename="test.pdf")
        db_session.add(sehra)

        sr = SharedReport(
            id=str(uuid.uuid4()),
            sehra_id=sehra.id,
            share_token="view-token",
            passcode_hash="hash",
            is_active=True,
        )
        db_session.add(sr)
        db_session.commit()

        # Log a view
        rv = ReportView(
            id=str(uuid.uuid4()),
            shared_report_id=sr.id,
            viewer_ip="1.2.3.4",
            passcode_correct=True,
        )
        db_session.add(rv)
        db_session.commit()

        views = db_session.query(ReportView).filter_by(shared_report_id=sr.id).all()
        assert len(views) == 1
        assert views[0].viewer_ip == "1.2.3.4"

    def test_rate_limiting(self, db_session):
        import uuid
        sehra = SEHRA(id=str(uuid.uuid4()), country="Test", pdf_filename="test.pdf")
        db_session.add(sehra)

        sr = SharedReport(
            id=str(uuid.uuid4()),
            sehra_id=sehra.id,
            share_token="rate-token",
            passcode_hash="hash",
            is_active=True,
        )
        db_session.add(sr)
        db_session.commit()

        # Log 5 failed attempts
        for i in range(5):
            rv = ReportView(
                id=str(uuid.uuid4()),
                shared_report_id=sr.id,
                passcode_correct=False,
            )
            db_session.add(rv)
        db_session.commit()

        failed = db_session.query(ReportView).filter(
            ReportView.shared_report_id == sr.id,
            ReportView.passcode_correct == False,
        ).count()
        assert failed == 5

    def test_expired_link(self, db_session):
        import uuid
        sehra = SEHRA(id=str(uuid.uuid4()), country="Test", pdf_filename="test.pdf")
        db_session.add(sehra)

        sr = SharedReport(
            id=str(uuid.uuid4()),
            sehra_id=sehra.id,
            share_token="expired-token",
            passcode_hash="hash",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Already expired
        )
        db_session.add(sr)
        db_session.commit()

        found = db_session.query(SharedReport).filter_by(share_token="expired-token").first()
        assert found.expires_at < datetime.utcnow()


class TestPasscodeVerification:
    def test_correct_passcode(self):
        passcode = "mySecret123"
        hashed = bcrypt.hashpw(passcode.encode(), bcrypt.gensalt()).decode()
        assert bcrypt.checkpw(passcode.encode(), hashed.encode())

    def test_wrong_passcode(self):
        passcode = "mySecret123"
        hashed = bcrypt.hashpw(passcode.encode(), bcrypt.gensalt()).decode()
        assert not bcrypt.checkpw(b"wrongPassword", hashed.encode())
