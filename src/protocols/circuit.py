"""
Circuit breaker protocol.

Automatic system override when overwhelmed.
Disables normal operations, forces simplification to ONE project.
"""

import os
from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from src.core.database import get_session
from src.core.metrics import (
    check_circuit_breaker_conditions,
    get_active_projects,
)

console = Console()

CIRCUIT_BREAKER_FLAG = Path.home() / ".ceo-os" / ".circuit_breaker_active"


def is_circuit_breaker_active() -> bool:
    """Check if circuit breaker is currently active."""
    return CIRCUIT_BREAKER_FLAG.exists()


def activate_circuit_breaker(reasons: List[str]):
    """Enter simplified mode.

    - Disables most commands
    - Forces focus on ONE project
    - Requires external accountability
    """
    console.print(
        Panel(
            "[red bold]🚨 CIRCUIT BREAKER ACTIVATED[/red bold]\n\n"
            "[yellow]Trigger conditions:[/yellow]\n"
            + "\n".join(f"  • {r}" for r in reasons)
            + "\n\n[bold]System Override Active[/bold]\n"
            "Normal operations suspended.\n"
            "Entering Simplified Mode.",
            title="Circuit Breaker",
            border_style="red",
        )
    )

    session = get_session()

    try:
        # Force selection of ONE project
        console.print("\n[yellow bold]STEP 1: Pick ONE Project[/yellow bold]\n")
        console.print("Everything else gets deferred or delegated.\n")

        active = get_active_projects(session)

        if not active:
            console.print("[yellow]No active projects. Good - start fresh.[/yellow]\n")
            primary = Prompt.ask("What ONE thing will you ship this week?")
        else:
            console.print("[bold]Active projects:[/bold]")
            for i, p in enumerate(active, 1):
                console.print(f"  {i}. {p.name}")

            console.print()
            choice = Prompt.ask(
                "Which ONE will you focus on? (number)",
                choices=[str(i) for i in range(1, len(active) + 1)],
            )
            primary = active[int(choice) - 1].name

        console.print(f"\n[green]→ Primary focus:[/green] {primary}\n")

        # Force external accountability
        console.print("[yellow bold]STEP 2: External Accountability[/yellow bold]\n")
        console.print("You MUST engage external support to exit this mode.\n")

        # Get external contact
        external_name = os.getenv("CEO_EXTERNAL_CONTACT_NAME")
        external_phone = os.getenv("CEO_EXTERNAL_CONTACT_PHONE")

        if not external_name:
            external_name = Prompt.ask("External accountability person (name)")
            external_phone = Prompt.ask("Their phone number")

        console.print(
            Panel(
                f"[red bold]REQUIRED ACTION[/red bold]\n\n"
                f"Call {external_name} at {external_phone}\n\n"
                "Tell them:\n"
                f'  1. "I\'m activating circuit breaker"\n'
                f'  2. "I\'m focusing on: {primary}"\n'
                f'  3. "Check in with me in 48 hours"\n',
                title="External Support",
                border_style="yellow",
            )
        )

        called = Confirm.ask(
            "\nHave you called them and set up the check-in?",
            default=False,
        )

        if not called:
            console.print(
                "[red]Cannot activate circuit breaker without external accountability.[/red]\n"
                "[yellow]Make the call, then run this command again.[/yellow]\n"
            )
            return

        # Activate circuit breaker
        CIRCUIT_BREAKER_FLAG.parent.mkdir(parents=True, exist_ok=True)
        CIRCUIT_BREAKER_FLAG.write_text(
            f"primary_project={primary}\n"
            f"external_contact={external_name}\n"
            f"activated_at={Prompt.ask('Date', default='today')}\n"
        )

        console.print(
            Panel(
                "[green bold]✓ CIRCUIT BREAKER ACTIVE[/green bold]\n\n"
                f"Focus: {primary}\n"
                f"External support: {external_name}\n\n"
                "[yellow]Simplified mode:[/yellow]\n"
                "  • Daily check-in only\n"
                "  • ONE project focus\n"
                "  • No new commitments\n\n"
                "Deactivate when:\n"
                "  • Shipped 3+ things in 2 weeks\n"
                "  • Made 5+ decisions without spiral\n"
                "  • External support validates recovery\n",
                title="System Override Active",
                border_style="yellow",
            )
        )

    finally:
        session.close()


def deactivate_circuit_breaker():
    """Exit simplified mode (with validation)."""
    if not is_circuit_breaker_active():
        console.print("[yellow]Circuit breaker not active[/yellow]\n")
        return

    console.print(
        Panel(
            "[yellow bold]Deactivate Circuit Breaker?[/yellow bold]\n\n"
            "Before deactivating, confirm:\n"
            "  • Have you shipped 3+ things in 2 weeks?\n"
            "  • Have you made 5+ decisions without paralysis?\n"
            "  • Has your external contact validated recovery?\n",
            title="Recovery Check",
            border_style="yellow",
        )
    )

    validated = Confirm.ask(
        "\nHas your external contact validated you're ready?",
        default=False,
    )

    if not validated:
        console.print(
            "[red]Get external validation before deactivating.[/red]\n"
            "[yellow]They can see patterns you might miss.[/yellow]\n"
        )
        return

    confirm = Confirm.ask("Deactivate circuit breaker?", default=False)

    if confirm:
        CIRCUIT_BREAKER_FLAG.unlink()
        console.print(
            "\n[green]✓ Circuit breaker deactivated[/green]\n"
            "[yellow]Resuming normal operations.[/yellow]\n"
            "[dim]Remember: Use the system proactively to avoid future triggers.[/dim]\n"
        )
    else:
        console.print("[yellow]Staying in simplified mode[/yellow]\n")


def check_and_warn():
    """Check if should trigger circuit breaker and warn user."""
    session = get_session()

    try:
        should_trigger, reasons = check_circuit_breaker_conditions(session)

        if should_trigger:
            console.print(
                Panel(
                    "[yellow bold]⚠️ CIRCUIT BREAKER CONDITIONS MET[/yellow bold]\n\n"
                    + "\n".join(f"  • {r}" for r in reasons)
                    + "\n\n[bold]Recommendation:[/bold]\n"
                    "Run: [cyan]ceo emergency activate[/cyan]\n\n"
                    "This will:\n"
                    "  • Simplify to ONE project\n"
                    "  • Engage external support\n"
                    "  • Prevent burnout\n",
                    title="Circuit Breaker Warning",
                    border_style="yellow",
                )
            )
            return True

        return False

    finally:
        session.close()
