# CLAUDE.md - CEO Execution OS Development Instructions

## Project Overview

**Name:** CEO Execution OS  
**Purpose:** Personal execution system to help a CEO reduce decision paralysis, ship projects early, and delegate effectively  
**Architecture:** Python CLI + SQLite + encrypted cloud sync  
**Key Constraint:** Personal data never committed to GitHub

---

## Project Context

### The User (Théo Hermann)
- **Core challenges:**
  - Decision paralysis under pressure (physical tension, circular thinking)
  - Difficulty shipping/finishing projects (perfectionism)
  - Control issues blocking delegation
  
- **Success metric:** Projects shipped early (target: 80%+)

- **Personal patterns to optimize for:**
  - Needs forcing functions for decisions (20-min rule)
  - Benefits from completion rituals (rewire brain)
  - Requires structured handoff protocols for delegation

### System Design Principles
1. **Visual-first, concise text** - Rich CLI output, minimal reading
2. **Minimal daily maintenance** (<90 seconds)
3. **Hard caps on active work** (max 3-5 projects)
4. **Separation of thinking vs. execution** (plan weekly, execute daily)
5. **Responds to actual state** (energy, stress, paralysis signals)
6. **Self-protecting mechanisms** (circuit breaker when overwhelmed)

---

## Repository Structure

```
ceo-execution-os/
├── src/
│   ├── cli/                 # CLI commands (Typer)
│   ├── core/                # Database, models, config
│   ├── analytics/           # Pattern detection, metrics
│   ├── sync/                # Cloud sync (encrypted)
│   ├── notifications/       # Reminders, alerts
│   └── web/                 # Dashboard (future)
├── tests/                   # Pytest tests
├── config/
│   ├── settings.yaml        # Non-sensitive defaults
│   └── templates/           # Report templates
├── docs/                    # Documentation
├── scripts/                 # Setup/backup scripts
├── .github/workflows/       # CI/CD
├── .gitignore              # CRITICAL: Exclude data/
├── .env.example            # Template only
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Critical Security Rules

### NEVER Commit These Files/Folders
```
*.db                 # SQLite database
*.db-journal
.env                 # Environment variables
*.log
backups/             # Encrypted backups
data/                # Any user data
config/local.yaml    # Local config with paths
```

### Always Use Environment Variables
```python
# ✅ CORRECT
import os
from pathlib import Path

DB_PATH = os.getenv("CEO_DB_PATH", str(Path.home() / ".ceo-os" / "data.db"))
CLOUD_KEY = os.getenv("CEO_CLOUD_KEY")  # From system keyring

# ❌ NEVER
DB_PATH = "/Users/theo/ceo-os/data.db"  # Hardcoded path
API_KEY = "abc123xyz"                    # Hardcoded secret
```

### Encryption Before Cloud Sync
```python
# All data must be encrypted before leaving local machine
from cryptography.fernet import Fernet

def sync_to_cloud(db_path: Path):
    cipher = get_cipher()  # From keyring
    with open(db_path, 'rb') as f:
        encrypted = cipher.encrypt(f.read())
    upload_to_cloud(encrypted)  # Only encrypted data touches cloud
```

---

## Development Guidelines

### Code Style
```python
# Use Python 3.11+ features
from pathlib import Path
from datetime import datetime
from typing import Optional

# Type hints everywhere
def daily_checkin(
    energy: str,
    stress: int,
    mission: str
) -> bool:
    """Record daily check-in.
    
    Args:
        energy: "high", "medium", or "low"
        stress: 1-10 scale
        mission: Today's single outcome
        
    Returns:
        True if check-in successful
    """
    pass

# Use Pydantic for validation
from pydantic import BaseModel, Field, validator

class DailyCheckin(BaseModel):
    energy: str = Field(..., pattern="^(high|medium|low)$")
    stress: int = Field(..., ge=1, le=10)
    tension: bool = False
    circular_thinking: bool = False
    mission: str = Field(..., min_length=5)
    
    @property
    def paralysis_detected(self) -> bool:
        return self.tension or self.circular_thinking
```

### CLI Design (Typer + Rich)
```python
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

app = typer.Typer()
console = Console()

@app.command()
def checkin():
    """Daily morning check-in (60-90 seconds)"""
    
    console.print("[bold cyan]🌅 Morning Check-in[/bold cyan]\n")
    
    # Quick questions with validation
    energy = typer.prompt(
        "Energy level",
        type=typer.Choice(["high", "medium", "low"])
    )
    
    stress = typer.prompt("Stress (1-10)", type=int)
    
    if stress > 7:
        console.print(
            Panel(
                "[yellow]⚠️ Stress >7 detected\n"
                "Activate check-valve protocol?\n"
                "1. 5-min reset\n"
                "2. Shrink mission\n"
                "3. Defer non-critical[/yellow]",
                title="Check-Valve"
            )
        )
    
    # Continue check-in flow...
```

### Database Patterns (SQLAlchemy)
```python
from sqlalchemy import Column, String, Integer, Date, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    
    id = Column(String, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    energy_level = Column(String)
    stress_level = Column(Integer)
    physical_tension = Column(Boolean)
    circular_thinking = Column(Boolean)
    mission = Column(String)
    mission_completed = Column(Boolean)
    
    @property
    def paralysis_detected(self) -> bool:
        return self.physical_tension or self.circular_thinking

# Usage
def record_checkin(session: Session, data: dict):
    checkin = DailyCheckin(**data)
    session.add(checkin)
    session.commit()
    
    # Pattern detection
    if checkin.paralysis_detected:
        trigger_paralysis_protocol(session, checkin)
```

### Analytics & Pattern Detection
```python
import pandas as pd
from datetime import datetime, timedelta

def analyze_paralysis_triggers(session: Session, days: int = 90):
    """Detect what triggers decision paralysis"""
    
    # Get recent check-ins
    cutoff = datetime.now() - timedelta(days=days)
    checkins = session.query(DailyCheckin).filter(
        DailyCheckin.date >= cutoff
    ).all()
    
    df = pd.DataFrame([{
        'date': c.date,
        'stress': c.stress_level,
        'energy': c.energy_level,
        'paralysis': c.paralysis_detected,
        'weekday': c.date.strftime('%A')
    } for c in checkins])
    
    # Correlate paralysis with factors
    insights = {
        "high_risk_stress": df[df.paralysis].stress.mean(),
        "high_risk_days": df[df.paralysis].weekday.value_counts().to_dict(),
        "paralysis_rate": (df.paralysis.sum() / len(df)) * 100
    }
    
    return insights

def completion_rate_trend(session: Session, weeks: int = 12):
    """Is shipping improving over time?"""
    
    reviews = session.query(WeeklyReview).order_by(
        WeeklyReview.week_start.desc()
    ).limit(weeks).all()
    
    df = pd.DataFrame([{
        'week': r.week_start,
        'completion_rate': r.completion_rate
    } for r in reviews])
    
    # Linear regression for trend
    from sklearn.linear_model import LinearRegression
    
    X = np.arange(len(df)).reshape(-1, 1)
    y = df.completion_rate.values
    
    model = LinearRegression().fit(X, y)
    trend = "improving" if model.coef_[0] > 0 else "declining"
    
    return {
        "trend": trend,
        "current_rate": df.iloc[0].completion_rate,
        "avg_rate": df.completion_rate.mean()
    }
```

### Testing Strategy
```python
import pytest
from datetime import date

def test_daily_checkin_records_paralysis():
    """Paralysis detected when tension OR circular thinking"""
    
    session = get_test_session()
    
    # Case 1: Tension only
    checkin1 = DailyCheckin(
        date=date.today(),
        physical_tension=True,
        circular_thinking=False
    )
    assert checkin1.paralysis_detected == True
    
    # Case 2: Circular thinking only
    checkin2 = DailyCheckin(
        date=date.today(),
        physical_tension=False,
        circular_thinking=True
    )
    assert checkin2.paralysis_detected == True
    
    # Case 3: Neither
    checkin3 = DailyCheckin(
        date=date.today(),
        physical_tension=False,
        circular_thinking=False
    )
    assert checkin3.paralysis_detected == False

def test_circuit_breaker_triggers_correctly():
    """Circuit breaker activates when health metrics fail"""
    
    session = get_test_session()
    
    # Create monthly review with 2 failing metrics
    review = MonthlyReview(
        month=date.today(),
        sleep_average=5.5,  # FAIL (<7)
        paralysis_episodes=8,  # FAIL (>5)
        completion_rate=75  # PASS
    )
    
    should_trigger = check_circuit_breaker_conditions(review)
    assert should_trigger == True

def test_20min_decision_protocol():
    """Decision logged with timestamp shows <25 min taken"""
    
    session = get_test_session()
    
    decision = Decision(
        decision_text="Hire candidate A",
        decision_type="reversible_low",
        time_to_decide=18,  # minutes
        paralysis_episode=True
    )
    
    session.add(decision)
    session.commit()
    
    # Verify decision followed protocol
    assert decision.time_to_decide < 25
    assert decision.decision_type == "reversible_low"
```

---

## Key Implementation Features

### 1. Paralysis Detection & Response

```python
class ParalysisProtocol:
    """20-minute decision forcing function"""
    
    def __init__(self, console: Console):
        self.console = console
        
    def activate(self):
        """Guided 20-min decision protocol"""
        
        self.console.print("\n[red bold]⚠️ Paralysis Detected[/red bold]\n")
        
        # Step 1: Externalize (2 min)
        decision = typer.prompt("What decision are you avoiding?")
        fear = typer.prompt("What's the fear behind the delay?")
        
        # Step 2: Set constraint (visual timer)
        self.console.print("\n[yellow]⏱ You have 20 minutes to decide[/yellow]")
        self.start_timer(minutes=20)
        
        # Step 3: Simplify to binary
        option_a = typer.prompt("Option A (simplest path)")
        option_b = typer.prompt("Option B (alternative)")
        
        # Step 4: Force decision
        choice = typer.prompt(
            "Which do you choose?",
            type=typer.Choice(["A", "B", "Flip coin"])
        )
        
        if choice == "Flip coin":
            import random
            choice = random.choice(["A", "B"])
            self.console.print(f"🪙 Coin flip: {choice}")
        
        # Step 5: Commit
        final_decision = option_a if choice == "A" else option_b
        rationale = typer.prompt("Why? (prevents circular revisit)")
        
        # Log decision
        self.log_decision(
            decision=final_decision,
            rationale=rationale,
            time_taken=self.timer_elapsed()
        )
        
        self.console.print(
            Panel(
                f"[green]✓ Decision made: {final_decision}[/green]\n"
                f"Time: {self.timer_elapsed()} minutes\n"
                f"Now take the FIRST ACTION immediately",
                title="Decision Logged"
            )
        )
```

### 2. Completion Tracking (North Star Metric)

```python
class CompletionTracker:
    """Track projects shipped early vs. late"""
    
    def weekly_scorecard(self, session: Session) -> dict:
        """Generate completion scorecard"""
        
        week_start = get_current_week_start()
        
        # Get this week's completed items
        completed = session.query(Project).filter(
            Project.completed_at >= week_start,
            Project.status == "completed"
        ).all()
        
        early = len([p for p in completed if p.shipped_early])
        on_time = len([p for p in completed if not p.shipped_early and p.completed_at <= p.eac_date])
        late = len([p for p in completed if p.completed_at > p.eac_date])
        
        total = len(completed)
        completion_rate = ((early + on_time) / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "early": early,
            "on_time": on_time,
            "late": late,
            "completion_rate": completion_rate,
            "target_met": completion_rate >= 80
        }
    
    def display_scorecard(self, scorecard: dict):
        """Visual completion scorecard"""
        
        from rich.table import Table
        
        table = Table(title="📦 This Week's Shipping Record")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("✓ Early", str(scorecard["early"]))
        table.add_row("✓ On-time", str(scorecard["on_time"]))
        table.add_row("⚠ Late", str(scorecard["late"]))
        table.add_row("", "")
        
        rate_color = "green" if scorecard["target_met"] else "yellow"
        table.add_row(
            "Completion Rate",
            f"[{rate_color}]{scorecard['completion_rate']:.1f}%[/{rate_color}]"
        )
        
        console.print(table)
        
        if not scorecard["target_met"]:
            console.print(
                "\n[yellow]⚠️ Below 80% target - what are you holding onto?[/yellow]"
            )
```

### 3. Delegation Handoff Protocol

```python
class DelegationManager:
    """Structured delegation with control release tracking"""
    
    def create_delegation(self, session: Session):
        """Guide user through proper handoff"""
        
        console.print("[bold]🤲 Delegation Handoff Protocol[/bold]\n")
        
        # Basic info
        task = typer.prompt("Task to delegate")
        person = typer.prompt("Delegate to")
        control_impulse = typer.prompt(
            "Control impulse (1-10, 10=very high)",
            type=int
        )
        
        # Handoff checklist
        console.print("\n[cyan]Complete these for successful handoff:[/cyan]")
        
        checklist = {
            "context_meeting": "15-min context-setting meeting scheduled?",
            "success_criteria": "Success criteria written (not just in head)?",
            "decision_authority": "Decision authority clarified?",
            "first_checkin": "First check-in date set?",
            "availability_stated": "'I'm available for questions' said?"
        }
        
        handoff_quality = {}
        for key, question in checklist.items():
            handoff_quality[key] = typer.confirm(question)
        
        handoff_completed = all(handoff_quality.values())
        
        if not handoff_completed:
            console.print(
                "\n[yellow]⚠️ Incomplete handoff increases takeback risk[/yellow]"
            )
        
        # Create delegation record
        delegation = Delegation(
            task=task,
            delegated_to=person,
            control_impulse=control_impulse,
            handoff_completed=handoff_completed,
            delegated_date=date.today()
        )
        
        session.add(delegation)
        session.commit()
        
        # Set reminder for check-in
        if handoff_completed:
            console.print(
                f"\n[green]✓ Delegation created[/green]\n"
                f"Remember: Stay out between check-ins!\n"
                f"Different ≠ Wrong. Their way might be better."
            )
```

### 4. Circuit Breaker Logic

```python
class CircuitBreaker:
    """Automatic system override when overwhelmed"""
    
    def check_should_trigger(self, session: Session) -> tuple[bool, list[str]]:
        """Check if circuit breaker conditions met"""
        
        reasons = []
        
        # Get recent data
        month_review = session.query(MonthlyReview).order_by(
            MonthlyReview.month.desc()
        ).first()
        
        recent_weeks = session.query(WeeklyReview).order_by(
            WeeklyReview.week_start.desc()
        ).limit(2).all()
        
        # Check each trigger condition
        if month_review:
            if month_review.paralysis_episodes > 5:
                reasons.append("5+ paralysis episodes this month")
            
            if month_review.physical_tension_days > 10:
                reasons.append("Physical tension >10 days")
            
            # Check 2+ failing health metrics
            failing = 0
            if month_review.sleep_average < 7:
                failing += 1
            if month_review.paralysis_episodes > 5:
                failing += 1
            if month_review.completion_rate < 60:
                failing += 1
                
            if failing >= 2:
                reasons.append("2+ health metrics failing")
        
        if len(recent_weeks) >= 2:
            if all(w.completion_rate < 60 for w in recent_weeks):
                reasons.append("Completion <60% for 2 weeks")
        
        should_trigger = len(reasons) > 0
        return should_trigger, reasons
    
    def activate(self, session: Session, reasons: list[str]):
        """Enter simplified mode"""
        
        console.print("\n[red bold]🛑 CIRCUIT BREAKER ACTIVATED[/red bold]\n")
        
        for reason in reasons:
            console.print(f"  • {reason}")
        
        console.print(
            "\n[yellow]Entering Simplified Mode:[/yellow]\n"
            "1. Pick ONE project to ship this week\n"
            "2. Everything else: delegate, defer, or kill\n"
            "3. Call external support: [contact]\n"
            "4. 25-min decision sprint scheduled\n"
        )
        
        # Guide simplified mode setup
        primary_project = typer.prompt(
            "Which ONE project will you ship this week?"
        )
        
        # Log circuit breaker event
        event = CircuitBreakerEvent(
            trigger_date=date.today(),
            trigger_reasons=reasons,
            simplified_project=primary_project,
            external_support_engaged=False
        )
        
        session.add(event)
        session.commit()
        
        # Set reminders
        self.schedule_support_reminder(hours=48)
        self.pause_normal_operations()
```

---

## Development Workflow

### Initial Setup
```bash
# Clone repo
git clone https://github.com/theomann/ceo-execution-os.git
cd ceo-execution-os

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup script
./scripts/setup.sh

# Initialize database
ceo setup init

# Configure cloud sync (optional)
ceo sync setup
```

### Daily Development
```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/

# Format code
black src/

# Run CLI locally
python -m src.cli.main daily checkin
```

### Before Committing
```bash
# Verify no sensitive data
git status
# Should NOT see: *.db, .env, backups/, data/

# Run all checks
./scripts/pre-commit.sh

# Commit
git add src/ tests/ docs/
git commit -m "feat: Add paralysis detection"
git push origin main
```

---

## Critical Reminders for Claude Code

1. **NEVER commit user data** - All personal info stays in encrypted cloud storage
2. **Use environment variables** - No hardcoded paths or secrets
3. **Test before pushing** - All tests must pass
4. **Type hints everywhere** - Helps with maintainability
5. **Rich CLI output** - Visual, helpful, fast (<5s response)
6. **Pattern detection is key** - Help user understand their behavior
7. **Optimize for speed** - Daily check-in must be <90 seconds
8. **Fail gracefully** - If cloud sync fails, local DB is source of truth
9. **Privacy first** - User should trust this completely
10. **North Star metric** - Everything serves "projects shipped early"

---

## Questions to Ask When Implementing

Before implementing any feature:
1. Does this help Théo ship projects early?
2. Does this reduce decision paralysis?
3. Is this under 90 seconds for daily use?
4. Could this data be sensitive? (If yes → encrypt)
5. Will this work offline?
6. How does this fail? (Design failure modes)
7. Can we measure if this is working?

---

## Support & Maintenance

### Common Issues

**Issue: Database locked**
```python
# Use WAL mode for better concurrency
engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"timeout": 30},
    poolclass=NullPool
)

# Enable WAL
with engine.connect() as conn:
    conn.execute("PRAGMA journal_mode=WAL")
```

**Issue: Cloud sync fails**
```python
# Always fallback to local
try:
    sync_to_cloud()
except SyncError as e:
    log_error(e)
    console.print("[yellow]Sync failed, using local data[/yellow]")
    # Continue normal operation
```

**Issue: Slow pattern analysis**
```python
# Cache insights, update weekly
def get_insights(force_refresh=False):
    cache = get_cached_insights()
    
    if cache and not force_refresh:
        if cache.generated_at > datetime.now() - timedelta(days=7):
            return cache
    
    # Regenerate
    new_insights = analyze_patterns()
    cache_insights(new_insights)
    return new_insights
```

---

## Success Criteria for Implementation

The system is working well when:
- ✅ Théo completes daily check-in >90% of days
- ✅ Check-in takes <90 seconds
- ✅ Paralysis detection triggers protocol automatically
- ✅ Completion rate trending upward
- ✅ Zero data loss incidents
- ✅ Théo reports: "This makes hard weeks easier"

The system is NOT working if:
- ❌ Daily check-in feels like a chore
- ❌ Patterns/insights aren't helpful
- ❌ Circuit breaker never triggers (not catching problems)
- ❌ Completion rate stays flat or declines
- ❌ Théo stops using it

---

## Version 1.0 Definition of Done

Ready to ship when:
1. All daily commands functional (<5s response)
2. Weekly review generates insights automatically
3. Monthly metrics tracked and visualized
4. Paralysis protocol triggers appropriately
5. Circuit breaker logic validated
6. Cloud sync working with encryption
7. Test coverage >80%
8. Documentation complete
9. Zero hardcoded paths/secrets
10. Théo uses it daily for 2 weeks successfully

---

## Future Enhancements (Post-V1)

- Mobile app for on-the-go check-ins
- Web dashboard with charts
- Slack/email integration for notifications
- Team view for delegation tracking
- AI coaching ("Based on your patterns, consider...")
- Voice interface for hands-free check-ins
- API for integration with other tools
- Shared accountability features (peer CEOs)

But V1 MUST be rock-solid on core functionality first.