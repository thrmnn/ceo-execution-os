"""
Tests for metrics calculations.
"""

from datetime import date, timedelta

import pytest

from src.core.metrics import (
    can_add_project,
    check_circuit_breaker_conditions,
    get_active_projects,
    get_paralysis_rate,
    get_today_status,
    get_week_stats,
)
from src.core.models import DailyLog, Project


def test_get_today_status_empty(test_db_session):
    """Test getting today's status when no check-in exists."""
    status = get_today_status(test_db_session)
    assert status is None


def test_get_today_status_exists(test_db_session):
    """Test getting today's status when check-in exists."""
    log = DailyLog(
        date=date.today(),
        energy="high",
        mission="Test mission",
    )
    test_db_session.add(log)
    test_db_session.commit()

    status = get_today_status(test_db_session)
    assert status is not None
    assert status.mission == "Test mission"


def test_week_stats_empty(test_db_session):
    """Test week stats with no data."""
    stats = get_week_stats(test_db_session)

    assert stats["shipped"] == 0
    assert stats["total"] == 0
    assert stats["completion_rate"] == 0


def test_week_stats_with_data(test_db_session):
    """Test week stats with sample data."""
    from src.core.metrics import get_week_start

    # Create logs for this week starting from Monday
    week_start = get_week_start()

    for i in range(5):
        log_date = week_start + timedelta(days=i)
        status = "shipped" if i < 3 else "blocked"

        log = DailyLog(
            date=log_date,
            mission=f"Mission {i}",
            mission_status=status,
        )
        test_db_session.add(log)

    test_db_session.commit()

    stats = get_week_stats(test_db_session)

    assert stats["total"] == 5
    assert stats["shipped"] == 3
    assert stats["completion_rate"] == 60.0


def test_paralysis_rate_calculation(test_db_session):
    """Test paralysis rate calculation."""
    # Create logs with paralysis signals
    for i in range(10):
        log = DailyLog(
            date=date.today() - timedelta(days=i),
            paralysis_signals=(i < 3),  # 3 out of 10 have paralysis
        )
        test_db_session.add(log)

    test_db_session.commit()

    stats = get_paralysis_rate(test_db_session, days=30)

    assert stats["paralysis_days"] == 3
    assert stats["total_days"] == 10
    assert stats["paralysis_rate"] == 30.0


def test_get_active_projects(test_db_session):
    """Test getting active projects."""
    # Create mix of projects
    active1 = Project(name="Active 1", status="active")
    active2 = Project(name="Active 2", status="active")
    shipped = Project(name="Shipped", status="shipped")
    killed = Project(name="Killed", status="killed")

    test_db_session.add_all([active1, active2, shipped, killed])
    test_db_session.commit()

    active = get_active_projects(test_db_session)

    assert len(active) == 2
    assert all(p.status == "active" for p in active)


def test_can_add_project_below_cap(test_db_session):
    """Test can add project when below cap."""
    # Add 2 active projects
    for i in range(2):
        p = Project(name=f"Project {i}", status="active")
        test_db_session.add(p)

    test_db_session.commit()

    assert can_add_project(test_db_session) is True


def test_can_add_project_at_cap(test_db_session):
    """Test cannot add project when at cap."""
    # Add 3 active projects (at cap)
    for i in range(3):
        p = Project(name=f"Project {i}", status="active")
        test_db_session.add(p)

    test_db_session.commit()

    assert can_add_project(test_db_session) is False


def test_circuit_breaker_paralysis_trigger(test_db_session):
    """Test circuit breaker triggers on high paralysis rate."""
    # Create 6 days with paralysis in last 30 days
    for i in range(6):
        log = DailyLog(
            date=date.today() - timedelta(days=i),
            paralysis_signals=True,
        )
        test_db_session.add(log)

    test_db_session.commit()

    should_trigger, reasons = check_circuit_breaker_conditions(test_db_session)

    assert should_trigger is True
    assert len(reasons) > 0
    assert any("paralysis" in r.lower() for r in reasons)


def test_circuit_breaker_completion_rate_trigger(test_db_session):
    """Test circuit breaker triggers on low completion rate."""
    # Create 2 weeks of low completion
    today = date.today()

    # This week: 1/5 completed (20%)
    for i in range(5):
        log = DailyLog(
            date=today - timedelta(days=i),
            mission=f"Mission {i}",
            mission_status="shipped" if i == 0 else "blocked",
        )
        test_db_session.add(log)

    # Last week: 1/5 completed (20%)
    for i in range(7, 12):
        log = DailyLog(
            date=today - timedelta(days=i),
            mission=f"Mission {i}",
            mission_status="shipped" if i == 7 else "blocked",
        )
        test_db_session.add(log)

    test_db_session.commit()

    should_trigger, reasons = check_circuit_breaker_conditions(test_db_session)

    assert should_trigger is True
    assert any("completion" in r.lower() for r in reasons)


def test_circuit_breaker_no_trigger_healthy(test_db_session):
    """Test circuit breaker doesn't trigger when healthy."""
    # Create healthy data
    for i in range(5):
        log = DailyLog(
            date=date.today() - timedelta(days=i),
            paralysis_signals=False,
            mission=f"Mission {i}",
            mission_status="shipped",
        )
        test_db_session.add(log)

    test_db_session.commit()

    should_trigger, reasons = check_circuit_breaker_conditions(test_db_session)

    assert should_trigger is False
    assert len(reasons) == 0
