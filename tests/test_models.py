"""
Tests for database models.
"""

from datetime import date

import pytest

from src.core.models import DailyLog, Decision, Project


def test_daily_log_creation(test_db_session):
    """Test creating a daily log entry."""
    log = DailyLog(
        date=date.today(),
        energy="high",
        paralysis_signals=False,
        mission="Ship feature X",
        mission_status="shipped",
    )

    test_db_session.add(log)
    test_db_session.commit()

    # Retrieve and verify
    retrieved = test_db_session.query(DailyLog).filter_by(date=date.today()).first()

    assert retrieved is not None
    assert retrieved.energy == "high"
    assert retrieved.mission == "Ship feature X"
    assert retrieved.is_complete is True


def test_daily_log_paralysis_detection(test_db_session):
    """Test paralysis signal detection."""
    log1 = DailyLog(
        date=date.today(),
        paralysis_signals=True,
    )

    assert log1.paralysis_signals is True


def test_daily_log_blocked_by_me(test_db_session):
    """Test detection of self-blocking."""
    log = DailyLog(
        date=date.today(),
        mission_status="blocked",
        blocker_type="me_decision",
    )

    assert log.blocked_by_me is True

    log2 = DailyLog(
        date=date.today(),
        mission_status="blocked",
        blocker_type="external",
    )

    assert log2.blocked_by_me is False


def test_project_creation(test_db_session):
    """Test creating a project."""
    project = Project(
        name="Launch MVP",
        target_date=date(2024, 12, 31),
        status="active",
    )

    test_db_session.add(project)
    test_db_session.commit()

    retrieved = test_db_session.query(Project).filter_by(name="Launch MVP").first()

    assert retrieved is not None
    assert retrieved.is_active is True
    assert retrieved.days_remaining is not None


def test_project_days_remaining(test_db_session):
    """Test days remaining calculation."""
    future_date = date(2025, 12, 31)

    project = Project(
        name="Test Project",
        target_date=future_date,
    )

    # Days remaining should be positive for future dates
    assert project.days_remaining is not None


def test_decision_creation(test_db_session):
    """Test creating a decision record."""
    decision = Decision(
        date=date.today(),
        decision="Hire candidate A",
        time_to_decide=15,
        made_under_paralysis=True,
        outcome="proceeded",
    )

    test_db_session.add(decision)
    test_db_session.commit()

    retrieved = test_db_session.query(Decision).first()

    assert retrieved is not None
    assert retrieved.under_20_minutes is True
    assert retrieved.made_under_paralysis is True


def test_decision_timing(test_db_session):
    """Test decision timing validation."""
    fast = Decision(date=date.today(), decision="Quick choice", time_to_decide=10)
    slow = Decision(date=date.today(), decision="Slow choice", time_to_decide=45)

    assert fast.under_20_minutes is True
    assert slow.under_20_minutes is False


def test_decision_needs_followup(test_db_session):
    """Test decision follow-up detection."""
    blocked = Decision(
        date=date.today(),
        decision="Test",
        outcome="blocked",
    )

    revisited = Decision(
        date=date.today(),
        decision="Test",
        outcome="revisited",
    )

    proceeded = Decision(
        date=date.today(),
        decision="Test",
        outcome="proceeded",
    )

    assert blocked.needs_followup is True
    assert revisited.needs_followup is True
    assert proceeded.needs_followup is False
