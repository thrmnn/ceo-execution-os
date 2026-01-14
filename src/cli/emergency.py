"""
Emergency / Circuit Breaker CLI commands.

For when things are overwhelming.
"""

import typer
from rich.console import Console

from src.protocols.circuit import (
    activate_circuit_breaker,
    check_and_warn,
    deactivate_circuit_breaker,
    is_circuit_breaker_active,
)
from src.core.metrics import check_circuit_breaker_conditions
from src.core.database import get_session

app = typer.Typer(help="Emergency & circuit breaker commands")
console = Console()


@app.command()
def check():
    """Check if circuit breaker conditions are met."""
    console.print("\n[bold cyan]Circuit Breaker Check[/bold cyan]\n")

    if is_circuit_breaker_active():
        console.print("[yellow]Circuit breaker is ACTIVE[/yellow]")
        console.print("Run: [cyan]ceo emergency status[/cyan] for details\n")
        return

    # Check conditions
    check_and_warn()


@app.command()
def activate():
    """Manually activate circuit breaker (simplified mode)."""
    if is_circuit_breaker_active():
        console.print("[yellow]Circuit breaker already active[/yellow]\n")
        return

    session = get_session()

    try:
        # Check if conditions are met
        should_trigger, reasons = check_circuit_breaker_conditions(session)

        if not reasons:
            # Manual activation
            console.print("[yellow]No automatic triggers, but you can activate manually.[/yellow]\n")
            reason = typer.prompt("Why activate? (e.g., 'Feeling overwhelmed')")
            reasons = [f"Manual: {reason}"]

        activate_circuit_breaker(reasons)

    finally:
        session.close()


@app.command()
def deactivate():
    """Deactivate circuit breaker (resume normal operations)."""
    deactivate_circuit_breaker()


@app.command()
def status():
    """Show circuit breaker status."""
    if not is_circuit_breaker_active():
        console.print("[green]Circuit breaker: INACTIVE[/green]")
        console.print("[dim]Normal operations[/dim]\n")
        return

    console.print("[yellow bold]Circuit breaker: ACTIVE[/yellow bold]\n")

    # Read config
    from pathlib import Path

    flag_file = Path.home() / ".ceo-os" / ".circuit_breaker_active"

    if flag_file.exists():
        config = flag_file.read_text()
        console.print("[bold]Simplified Mode Active:[/bold]")
        console.print(config)
        console.print()

    console.print("[dim]Run: ceo emergency deactivate (when ready)[/dim]\n")
