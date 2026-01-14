"""
Project management with HARD CAP at 3 active projects.

Forces prioritization and prevents WIP buildup.
"""

from datetime import date, datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.core.database import get_session
from src.core.metrics import can_add_project, get_active_projects
from src.core.models import Project

app = typer.Typer(help="Project management commands")
console = Console()


@app.command()
def add(name: str = typer.Argument(..., help="Project name")):
    """Add a new project (HARD CAP: 3 active max)."""
    session = get_session()

    try:
        # Check hard cap
        if not can_add_project(session):
            active = get_active_projects(session)

            console.print(
                Panel(
                    "[red bold]❌ CANNOT ADD PROJECT[/red bold]\n\n"
                    f"Already at 3 active projects (hard cap).\n\n"
                    "[bold]Your active projects:[/bold]\n"
                    + "\n".join(f"  • {p.name}" for p in active)
                    + "\n\n[yellow]To add a new project, first:[/yellow]\n"
                    "  1. Ship one: [cyan]ceo project complete <id>[/cyan]\n"
                    "  2. Kill one: [cyan]ceo project kill <id>[/cyan]\n"
                    "  3. Delegate one (mark as shipped)\n",
                    title="Hard Cap Reached",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        # Get target date
        has_deadline = Confirm.ask("Set target ship date?", default=True)
        target = None

        if has_deadline:
            date_str = Prompt.ask("Target date (YYYY-MM-DD)")
            try:
                target = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format[/red]")
                raise typer.Exit(1)

        # Create project
        project = Project(
            name=name,
            target_date=target,
            status="active",
        )

        session.add(project)
        session.commit()

        console.print(f"\n[green]✓ Project added:[/green] {name}")
        if target:
            days_until = (target - date.today()).days
            console.print(f"[dim]Target: {target} ({days_until} days)[/dim]")

        console.print(
            f"\n[yellow]Active projects: {len(get_active_projects(session))}/3[/yellow]\n"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


@app.command()
def list(show_all: bool = typer.Option(False, "--all", help="Show all projects")):
    """List projects."""
    session = get_session()

    try:
        if show_all:
            projects = session.query(Project).order_by(Project.created_at.desc()).all()
        else:
            projects = get_active_projects(session)

        if not projects:
            console.print("[yellow]No projects found[/yellow]\n")
            return

        # Create table
        table = Table(title="Projects" if show_all else "Active Projects (Max 3)")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Status")
        table.add_column("Target Date")
        table.add_column("Days Left")

        for p in projects:
            status_style = {
                "active": "yellow",
                "shipped": "green",
                "killed": "red",
            }.get(p.status, "white")

            days_left = p.days_remaining
            days_str = (
                f"{days_left}d"
                if days_left is not None
                else "-"
            )

            if days_left is not None and days_left < 0:
                days_str = f"[red]{days_left}d (overdue)[/red]"

            table.add_row(
                p.id[:8],
                p.name,
                f"[{status_style}]{p.status}[/{status_style}]",
                str(p.target_date) if p.target_date else "-",
                days_str,
            )

        console.print(table)
        console.print()

        # Show cap status for active projects
        if not show_all:
            active_count = len(projects)
            color = "red" if active_count >= 3 else "yellow" if active_count == 2 else "green"
            console.print(
                f"[{color}]Active: {active_count}/3[/{color}] "
                f"({'at cap' if active_count >= 3 else f'{3-active_count} slots left'})\n"
            )

    finally:
        session.close()


@app.command()
def complete(project_id: str = typer.Argument(..., help="Project ID (first 8 chars)")):
    """Mark project as shipped."""
    session = get_session()

    try:
        # Find project by ID prefix
        project = (
            session.query(Project)
            .filter(Project.id.like(f"{project_id}%"))
            .first()
        )

        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        if project.status != "active":
            console.print(
                f"[yellow]Project already {project.status}[/yellow]"
            )
            return

        # Check if shipped early
        shipped_early = False
        if project.target_date:
            shipped_early = date.today() <= project.target_date

        project.status = "shipped"
        project.completed_at = datetime.now()
        project.shipped_early = shipped_early

        session.commit()

        # Celebrate
        console.print(
            Panel(
                f"[green bold]🎉 PROJECT SHIPPED![/green bold]\n\n"
                f"Project: {project.name}\n"
                + (
                    f"[green]✓ SHIPPED EARLY[/green] (by {abs((project.target_date - date.today()).days)} days)\n"
                    if shipped_early and project.target_date
                    else ""
                )
                + "\n[dim]Every completion rewires your brain toward shipping.[/dim]",
                title="Completion",
                border_style="green",
            )
        )

        active_count = len(get_active_projects(session))
        console.print(
            f"\n[yellow]Active projects: {active_count}/3[/yellow] "
            f"({3-active_count} slots available)\n"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


@app.command()
def kill(project_id: str = typer.Argument(..., help="Project ID")):
    """Kill a project (stop pursuing)."""
    session = get_session()

    try:
        project = (
            session.query(Project)
            .filter(Project.id.like(f"{project_id}%"))
            .first()
        )

        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(f"\n[yellow]Kill project:[/yellow] {project.name}")

        reason = Prompt.ask("Why kill this project?", default="No longer strategic")

        confirm = Confirm.ask(
            "Are you sure? This frees up a project slot",
            default=False,
        )

        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

        project.status = "killed"
        project.completed_at = datetime.now()

        session.commit()

        console.print(f"\n[red]✓ Project killed:[/red] {project.name}")
        console.print(f"[dim]Reason: {reason}[/dim]")

        active_count = len(get_active_projects(session))
        console.print(
            f"\n[green]Active projects: {active_count}/3[/green] "
            f"(slot freed up)\n"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


@app.command()
def status(project_id: str = typer.Argument(..., help="Project ID")):
    """Show project details."""
    session = get_session()

    try:
        project = (
            session.query(Project)
            .filter(Project.id.like(f"{project_id}%"))
            .first()
        )

        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]{project.name}[/bold cyan]\n")
        console.print(f"ID: {project.id}")
        console.print(f"Status: {project.status}")

        if project.target_date:
            days = project.days_remaining
            if days is not None:
                if days < 0:
                    console.print(f"Target: {project.target_date} [red](overdue by {abs(days)}d)[/red]")
                else:
                    console.print(f"Target: {project.target_date} ({days}d remaining)")
            else:
                console.print(f"Target: {project.target_date}")

        if project.completed_at:
            console.print(f"Completed: {project.completed_at.date()}")
            if project.shipped_early is not None:
                result = "[green]EARLY[/green]" if project.shipped_early else "[yellow]ON TIME or LATE[/yellow]"
                console.print(f"Result: {result}")

        console.print()

    finally:
        session.close()
