"""
Simple metrics calculations from daily logs.

No ML, no complex analytics - just SQL aggregations.
Calculates weekly/monthly metrics on demand.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.models import DailyLog, Decision, Project


def get_week_start(target_date: Optional[date] = None) -> date:
    """Get Monday of the current week."""
    if target_date is None:
        target_date = date.today()

    # Get Monday (weekday 0)
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    return week_start


def get_today_status(session: Session) -> Optional[DailyLog]:
    """Get today's check-in status."""
    today = date.today()
    return session.query(DailyLog).filter(DailyLog.date == today).first()


def get_week_stats(session: Session, weeks_ago: int = 0) -> Dict:
    """Calculate weekly completion statistics.

    Args:
        session: Database session
        weeks_ago: 0 for current week, 1 for last week, etc.

    Returns:
        Dict with shipped, total, completion_rate, improving
    """
    # Get week boundaries
    target_week_start = get_week_start() - timedelta(weeks=weeks_ago)
    week_end = target_week_start + timedelta(days=6)

    # Get logs for this week
    logs = (
        session.query(DailyLog)
        .filter(DailyLog.date >= target_week_start, DailyLog.date <= week_end)
        .all()
    )

    # Count statuses
    total = len([log for log in logs if log.mission is not None])
    shipped = len([log for log in logs if log.mission_status == "shipped"])

    completion_rate = (shipped / total * 100) if total > 0 else 0

    # Compare to previous week
    prev_week_stats = (
        get_week_stats(session, weeks_ago + 1) if weeks_ago < 12 else None
    )
    improving = (
        completion_rate > prev_week_stats["completion_rate"]
        if prev_week_stats
        else False
    )

    return {
        "shipped": shipped,
        "total": total,
        "completion_rate": completion_rate,
        "improving": improving,
        "week_start": target_week_start,
    }


def get_paralysis_rate(session: Session, days: int = 30) -> Dict:
    """Calculate paralysis rate over last N days."""
    cutoff = date.today() - timedelta(days=days)

    logs = (
        session.query(DailyLog)
        .filter(DailyLog.date >= cutoff)
        .order_by(DailyLog.date.desc())
        .all()
    )

    total_days = len(logs)
    paralysis_days = len([log for log in logs if log.paralysis_signals])

    rate = (paralysis_days / total_days * 100) if total_days > 0 else 0

    return {
        "paralysis_days": paralysis_days,
        "total_days": total_days,
        "paralysis_rate": rate,
        "recent_episodes": paralysis_days,  # For circuit breaker
    }


def get_active_projects(session: Session) -> List[Project]:
    """Get all active projects."""
    return session.query(Project).filter(Project.status == "active").all()


def can_add_project(session: Session) -> bool:
    """Check if can add new project (hard cap at 3)."""
    active_count = session.query(Project).filter(Project.status == "active").count()
    return active_count < 3


def get_decision_stats(session: Session, days: int = 30) -> Dict:
    """Calculate decision timing statistics."""
    cutoff = date.today() - timedelta(days=days)

    decisions = (
        session.query(Decision).filter(Decision.date >= cutoff).all()
    )

    if not decisions:
        return {
            "total_decisions": 0,
            "avg_time": 0,
            "under_20min_rate": 0,
            "paralysis_decisions": 0,
        }

    # Filter decisions with time data
    timed = [d for d in decisions if d.time_to_decide is not None]
    under_20 = [d for d in timed if d.under_20_minutes]
    paralysis = [d for d in decisions if d.made_under_paralysis]

    avg_time = (
        sum(d.time_to_decide for d in timed) / len(timed) if timed else 0
    )
    under_20_rate = (len(under_20) / len(timed) * 100) if timed else 0

    return {
        "total_decisions": len(decisions),
        "avg_time": avg_time,
        "under_20min_rate": under_20_rate,
        "paralysis_decisions": len(paralysis),
    }


def check_circuit_breaker_conditions(session: Session) -> Tuple[bool, List[str]]:
    """Check if circuit breaker should trigger.

    Conditions:
    - 5+ paralysis episodes in last 30 days
    - Completion rate <60% for 2 consecutive weeks
    - 3+ active projects all blocked

    Returns:
        (should_trigger, reasons)
    """
    reasons = []

    # Check paralysis rate
    paralysis_stats = get_paralysis_rate(session, days=30)
    if paralysis_stats["recent_episodes"] >= 5:
        reasons.append(f"5+ paralysis episodes ({paralysis_stats['recent_episodes']})")

    # Check completion rate for last 2 weeks
    this_week = get_week_stats(session, weeks_ago=0)
    last_week = get_week_stats(session, weeks_ago=1)

    if this_week["completion_rate"] < 60 and last_week["completion_rate"] < 60:
        reasons.append(
            f"Completion <60% for 2 weeks "
            f"({this_week['completion_rate']:.0f}%, {last_week['completion_rate']:.0f}%)"
        )

    # Check if all projects blocked
    active_projects = get_active_projects(session)
    if len(active_projects) >= 3:
        # Check if today's mission is blocked
        today = get_today_status(session)
        if today and today.mission_status == "blocked":
            reasons.append("All projects stalled (mission blocked)")

    should_trigger = len(reasons) > 0
    return should_trigger, reasons


def get_hours_until_eod() -> int:
    """Calculate hours until end of day (17:00)."""
    now = date.today()
    # Simple: assume EOD is 17:00
    # This is a simplification - in real implementation would check actual time
    return 8  # Placeholder
