"""
Simplified database models for CEO Execution OS.

Only 3 tables:
- daily_logs: Daily check-ins and mission tracking
- projects: Active projects (max 3)
- decisions: Decision log with timing
"""

from datetime import date, datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def generate_uuid() -> str:
    """Generate UUID for primary keys."""
    return str(uuid.uuid4())


class DailyLog(Base):
    """Daily check-in and mission tracking.

    Replaces: DailyCheckin, WeeklyReview, MonthlyReview tables.
    All metrics calculated from this single source of truth.
    """

    __tablename__ = "daily_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(Date, unique=True, nullable=False, index=True)

    # Morning check-in (60 seconds)
    energy = Column(String(10))  # high/medium/low
    paralysis_signals = Column(Boolean, default=False)  # ANY tension/circular thinking
    mission = Column(Text)  # Today's ONE thing
    mission_done_definition = Column(Text)  # What does DONE look like?
    mission_target_time = Column(String(5))  # HH:MM when it should be done

    # End of day
    mission_status = Column(String(20))  # shipped/blocked/deferred/none
    blocker_type = Column(String(20))  # me_decision/external/none
    decision_made = Column(Text)  # What decision broke the block (if any)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    @property
    def is_complete(self) -> bool:
        """Check if mission was completed."""
        return self.mission_status == "shipped"

    @property
    def blocked_by_me(self) -> bool:
        """Check if blocked by own decision paralysis."""
        return self.mission_status == "blocked" and self.blocker_type == "me_decision"


class Project(Base):
    """Active projects with hard cap at 3.

    Simplified from original spec - only essential fields.
    """

    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    target_date = Column(Date)  # When you want to ship
    status = Column(String(20), default="active", index=True)  # active/shipped/killed

    # Completion tracking
    shipped_early = Column(Boolean, default=None)  # None until shipped

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    @property
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status == "active"

    @property
    def days_remaining(self) -> Optional[int]:
        """Days until target date."""
        if not self.target_date:
            return None
        delta = self.target_date - date.today()
        return delta.days


class Decision(Base):
    """Decision log with timing (for 20-min protocol tracking).

    Tracks all decisions to detect paralysis patterns.
    """

    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    date = Column(Date, nullable=False, index=True)
    decision = Column(Text, nullable=False)

    # Timing
    time_to_decide = Column(Integer)  # minutes
    made_under_paralysis = Column(Boolean, default=False)

    # Follow-up
    outcome = Column(String(20))  # proceeded/blocked/revisited
    notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    @property
    def under_20_minutes(self) -> bool:
        """Check if decision met 20-minute rule."""
        return self.time_to_decide is not None and self.time_to_decide <= 20

    @property
    def needs_followup(self) -> bool:
        """Check if decision needs follow-up."""
        return self.outcome in ["blocked", "revisited"]
