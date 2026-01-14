"""
Daily execution commands.

Core of the system - fast check-in with paralysis detection.
"""

from datetime import date

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from src.core.database import get_session
from src.core.models import DailyLog
from src.core.metrics import check_circuit_breaker_conditions

app = typer.Typer(help="Daily execution commands")
console = Console()


@app.command()
def checkin():
    """Morning check-in (60 seconds).

    Detects paralysis and forces protocol if needed.
    """
    session = get_session()

    try:
        console.print("\n[bold cyan]🌅 Morning Check-in[/bold cyan]\n")

        # Check if already done today
        today = date.today()
        existing = session.query(DailyLog).filter(DailyLog.date == today).first()

        if existing:
            console.print("[yellow]Already checked in today![/yellow]")
            if existing.mission:
                console.print(f"\nMission: {existing.mission}")
                console.print(f"Status: {existing.mission_status or 'in progress'}\n")
            return

        # Energy check
        energy = Prompt.ask(
            "Energy level",
            choices=["high", "medium", "low"],
            default="medium",
        )

        # Paralysis detection (simplified to single question)
        console.print(
            "\n[bold]Paralysis Check:[/bold] Physical tension OR circular thinking?"
        )
        paralysis = Confirm.ask("Detect any paralysis signals?", default=False)

        # If paralysis detected, force immediate action
        if paralysis:
            console.print(
                Panel(
                    "[red bold]⚠️ PARALYSIS DETECTED[/red bold]\n\n"
                    "You must address this before continuing.\n\n"
                    "Options:\n"
                    "  1. Run 20-min decision protocol\n"
                    "  2. Simplify today's mission\n"
                    "  3. Get external input\n",
                    title="Paralysis Protocol Required",
                    border_style="red",
                )
            )

            action = Prompt.ask(
                "What will you do RIGHT NOW?",
                choices=["1", "2", "3"],
                default="1",
            )

            if action == "1":
                console.print(
                    "\n[yellow]→ Run: ceo daily decide[/yellow]"
                    "\n[dim]After making decision, complete check-in[/dim]\n"
                )
                # Create partial log
                log = DailyLog(
                    date=today,
                    energy=energy,
                    paralysis_signals=True,
                )
                session.add(log)
                session.commit()
                return

            elif action == "3":
                external = Prompt.ask("Who will you call?")
                console.print(f"\n[red]📞 Call {external} before continuing[/red]")
                called = Confirm.ask("Have you called them?", default=False)
                if not called:
                    console.print("[red]Cannot proceed without external input[/red]")
                    return

        # Today's mission
        console.print("\n[bold]🎯 Today's Mission[/bold]")
        console.print(
            "[dim]What is the ONE thing you will SHIP today?[/dim]\n"
        )
        mission = Prompt.ask("Mission")

        # Force definition of done
        console.print(
            "\n[yellow]What does DONE look like?[/yellow]"
        )
        done_def = Prompt.ask(
            "Done when",
            default="Delivered / Delegated / Live",
        )

        # Time commitment
        target_time = Prompt.ask("By what time?", default="17:00")

        # Save check-in
        log = DailyLog(
            date=today,
            energy=energy,
            paralysis_signals=paralysis,
            mission=mission,
            mission_done_definition=done_def,
            mission_target_time=target_time,
            mission_status=None,  # Set at EOD
        )

        session.add(log)
        session.commit()

        # Show confirmation
        console.print("\n[green bold]✓ Check-in complete[/green bold]\n")
        console.print(f"Mission: {mission}")
        console.print(f"Done when: {done_def}")
        console.print(f"Target: {target_time}\n")

        # Check circuit breaker
        should_trigger, reasons = check_circuit_breaker_conditions(session)
        if should_trigger:
            console.print(
                Panel(
                    "[red bold]🚨 CIRCUIT BREAKER CONDITIONS MET[/red bold]\n\n"
                    + "\n".join(f"  • {r}" for r in reasons)
                    + "\n\nRun: [cyan]ceo emergency activate[/cyan]",
                    title="System Override Recommended",
                    border_style="red",
                )
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Check-in cancelled[/yellow]")
        session.rollback()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


@app.command()
def complete(
    status: str = typer.Option(
        ...,
        "--status",
        "-s",
        help="Mission status",
        prompt="How did it go?",
    )
):
    """Mark today's mission complete.

    Status options: shipped, blocked, deferred
    """
    session = get_session()

    try:
        today = date.today()
        log = session.query(DailyLog).filter(DailyLog.date == today).first()

        if not log:
            console.print("[red]No check-in found for today[/red]")
            console.print("[yellow]Run: ceo daily checkin[/yellow]")
            return

        if not log.mission:
            console.print("[red]No mission set for today[/red]")
            return

        # Validate status
        valid_statuses = ["shipped", "blocked", "deferred"]
        if status.lower() not in valid_statuses:
            console.print(f"[red]Invalid status. Use: {', '.join(valid_statuses)}[/red]")
            return

        log.mission_status = status.lower()

        # If blocked, get details
        if status.lower() == "blocked":
            blocker = Prompt.ask(
                "What's blocking?",
                choices=["me_decision", "external", "other"],
                default="me_decision",
            )
            log.blocker_type = blocker

            if blocker == "me_decision":
                console.print(
                    "\n[yellow]Blocked by your own decision?[/yellow]\n"
                    "→ Run: [cyan]ceo daily decide[/cyan] (20-min protocol)\n"
                )

        # If shipped, celebrate
        if status.lower() == "shipped":
            console.print("\n[green bold]🎉 MISSION SHIPPED![/green bold]\n")
            console.print(
                "[dim]Every completion rewires your brain toward shipping.[/dim]\n"
            )

        session.commit()

        # Show updated status
        console.print(f"Mission: {log.mission}")
        console.print(f"Status: [bold]{log.mission_status}[/bold]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


@app.command()
def decide():
    """20-minute decision protocol (BLOCKING).

    Forces a decision when paralyzed.
    """
    from src.protocols.paralysis import run_decision_protocol

    console.print("\n[bold red]⚠️ 20-MINUTE DECISION PROTOCOL[/bold red]\n")
    console.print("[yellow]This will BLOCK until you make a decision.[/yellow]\n")

    proceed = Confirm.ask("Ready to commit to deciding?", default=True)
    if not proceed:
        console.print("[red]Cannot escape paralysis without deciding.[/red]")
        return

    # Run the protocol
    run_decision_protocol()


@app.command()
def show():
    """Show today's dashboard."""
    session = get_session()

    try:
        today = date.today()
        log = session.query(DailyLog).filter(DailyLog.date == today).first()

        if not log:
            console.print("[yellow]No check-in today[/yellow]")
            console.print("\nRun: [cyan]ceo daily checkin[/cyan]\n")
            return

        # Show today's status
        console.print("\n[bold cyan]Today's Dashboard[/bold cyan]\n")

        console.print(f"Energy: {log.energy or 'not set'}")
        console.print(
            f"Paralysis: {'[red]YES[/red]' if log.paralysis_signals else '[green]NO[/green]'}"
        )
        console.print(f"\nMission: {log.mission or 'not set'}")

        if log.mission_done_definition:
            console.print(f"Done when: {log.mission_done_definition}")

        if log.mission_target_time:
            console.print(f"Target: {log.mission_target_time}")

        if log.mission_status:
            status_color = (
                "green"
                if log.mission_status == "shipped"
                else "red"
                if log.mission_status == "blocked"
                else "yellow"
            )
            console.print(f"Status: [{status_color}]{log.mission_status}[/{status_color}]")

        console.print()

    finally:
        session.close()
