"""
CEO Execution OS - Main CLI entry point.

Simple, fast, focused on forcing behavior change.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from src.core.database import init_database, get_db_path, get_session
from src.core.metrics import (
    get_today_status,
    get_week_stats,
    get_hours_until_eod,
)

app = typer.Typer(
    name="ceo",
    help="CEO Execution OS - Anti-paralysis execution system",
    add_completion=False,
)
console = Console()


def show_status_header():
    """Show completion status on every command.

    Makes progress (or lack thereof) constantly visible.
    """
    session = get_session()
    try:
        today = get_today_status(session)
        week_stats = get_week_stats(session)

        # Today's status
        if today and today.mission:
            if today.mission_status == "shipped":
                console.print("[green]✓ Today's mission: SHIPPED[/green]")
            else:
                hours_left = get_hours_until_eod()
                console.print(
                    f"[yellow]⏱ Today's mission: {hours_left}h remaining[/yellow]"
                )
                console.print(f"[dim]Mission: {today.mission}[/dim]")
        else:
            console.print("[red]❌ No check-in today[/red]")

        # Weekly progress
        shipped = week_stats["shipped"]
        total = week_stats["total"]
        rate = week_stats["completion_rate"]
        trend = "↑" if week_stats["improving"] else "↓"

        console.print(f"This week: {shipped}/{total} shipped ({trend})")

        # Completion rate with color
        color = "green" if rate >= 80 else "yellow" if rate >= 60 else "red"
        console.print(f"[{color}]Completion rate: {rate:.0f}%[/{color}] (target: 80%)\n")

    finally:
        session.close()


@app.callback()
def callback():
    """Show status header before every command."""
    # Skip header for setup command
    import sys

    if len(sys.argv) > 1 and sys.argv[1] not in ["setup", "--help", "-h"]:
        try:
            show_status_header()
        except Exception:
            # DB might not be initialized yet
            pass


@app.command()
def setup():
    """Initialize the CEO Execution OS database."""
    console.print("\n[bold cyan]🚀 CEO Execution OS Setup[/bold cyan]\n")

    try:
        # Initialize database
        init_database()
        db_path = get_db_path()

        console.print(f"[green]✓ Database initialized at:[/green] {db_path}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run: [cyan]ceo daily checkin[/cyan]")
        console.print("  2. Use it every morning (60 seconds)")
        console.print("  3. Ship your mission by EOD\n")

        console.print("[dim]Tip: Add a calendar reminder for 8am check-in[/dim]\n")

    except Exception as e:
        console.print(f"[red]✗ Setup failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show current status and metrics."""
    show_status_header()

    session = get_session()
    try:
        from src.core.metrics import get_active_projects, get_paralysis_rate

        # Active projects
        projects = get_active_projects(session)
        console.print(f"\n[bold]Active Projects ({len(projects)}/3):[/bold]")
        if projects:
            for p in projects:
                days_left = p.days_remaining
                if days_left is not None:
                    console.print(f"  • {p.name} ({days_left} days)")
                else:
                    console.print(f"  • {p.name} (no deadline)")
        else:
            console.print("  [dim]No active projects[/dim]")

        # Paralysis rate
        paralysis = get_paralysis_rate(session, days=30)
        rate = paralysis["paralysis_rate"]
        color = "green" if rate < 20 else "yellow" if rate < 40 else "red"
        console.print(
            f"\n[bold]Paralysis Rate (30 days):[/bold] "
            f"[{color}]{rate:.0f}%[/{color}] "
            f"({paralysis['paralysis_days']}/{paralysis['total_days']} days)\n"
        )

    finally:
        session.close()


# Import subcommands
from src.cli import daily, project, emergency  # noqa: E402

# Register subcommands
app.add_typer(daily.app, name="daily")
app.add_typer(project.app, name="project")
app.add_typer(emergency.app, name="emergency")


if __name__ == "__main__":
    app()
