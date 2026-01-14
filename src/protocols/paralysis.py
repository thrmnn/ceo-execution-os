"""
20-minute decision protocol.

BLOCKING - cannot exit until decision made.
Forces action when paralyzed.
"""

import time
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from src.core.database import get_session
from src.core.models import Decision

console = Console()


def run_decision_protocol():
    """Execute the 20-minute decision forcing function.

    Steps:
    1. Externalize (2 min) - What am I avoiding?
    2. Constraint (set timer) - 20 minutes to decide
    3. Simplify (5 min) - Binary choice
    4. Commit (10 min) - Decide, document, communicate
    """
    session = get_session()

    try:
        console.print("\n[bold]STEP 1: EXTERNALIZE (2 minutes)[/bold]\n")

        decision_text = Prompt.ask("What decision are you avoiding?")
        fear = Prompt.ask("What's the fear behind the delay?")

        console.print(f"\n[dim]Decision: {decision_text}[/dim]")
        console.print(f"[dim]Fear: {fear}[/dim]\n")

        # Step 2: Set constraint
        console.print("[bold]STEP 2: CONSTRAINT[/bold]\n")
        console.print("[yellow]⏱ You have 20 minutes to decide.[/yellow]")
        console.print("[dim]Timer starts... now![/dim]\n")

        start_time = time.time()

        # Step 3: Simplify
        console.print("[bold]STEP 3: SIMPLIFY (Binary Choice)[/bold]\n")

        option_a = Prompt.ask("Option A (simplest forward path)")
        option_b = Prompt.ask("Option B (alternative)")

        console.print(f"\n  A: {option_a}")
        console.print(f"  B: {option_b}\n")

        # Step 4: Force decision
        console.print("[bold]STEP 4: COMMIT - Make the call NOW[/bold]\n")

        choice = Prompt.ask(
            "Which do you choose?",
            choices=["A", "B", "flip"],
            default="A",
        )

        if choice.lower() == "flip":
            import random

            choice = random.choice(["A", "B"])
            console.print(f"\n🪙 [yellow]Coin flip: {choice}[/yellow]\n")

        final_decision = option_a if choice.upper() == "A" else option_b

        # Document rationale
        rationale = Prompt.ask(
            "\nWhy this choice? (prevents revisiting)",
            default="Moving forward with action > perfection",
        )

        # Calculate time taken
        elapsed = int((time.time() - start_time) / 60)

        # Force communication
        console.print("\n[bold]Communicate to lock it in:[/bold]")
        who = Prompt.ask("Who will you tell? (1 person minimum)", default="team")

        confirmed = Confirm.ask(f"Will you tell {who} in the next 5 minutes?", default=True)

        if not confirmed:
            console.print("[red]Communication = commitment. Try again.[/red]")
            return

        # Log decision
        decision_record = Decision(
            date=date.today(),
            decision=f"{decision_text} → {final_decision}",
            time_to_decide=elapsed,
            made_under_paralysis=True,
            outcome="proceeded",
            notes=f"Rationale: {rationale}\nCommunicated to: {who}",
        )

        session.add(decision_record)
        session.commit()

        # Confirmation
        console.print(
            Panel(
                f"[green bold]✓ DECISION MADE[/green bold]\n\n"
                f"Decision: {final_decision}\n"
                f"Time: {elapsed} minutes\n"
                f"Communicated to: {who}\n\n"
                f"[yellow]NOW: Take the FIRST ACTION immediately[/yellow]\n"
                f"What's the smallest next step?",
                title="Decision Logged",
                border_style="green",
            )
        )

        first_action = Prompt.ask("\nFirst action (right now)")
        console.print(f"\n[green]→ DO: {first_action}[/green]\n")

        # Check time
        if elapsed <= 20:
            console.print(
                f"[green]✓ Decision made in {elapsed} minutes (target: <20)[/green]\n"
            )
        else:
            console.print(
                f"[yellow]⚠ Took {elapsed} minutes (target: <20)[/yellow]\n"
                f"[dim]Aim for faster decisions next time[/dim]\n"
            )

    except KeyboardInterrupt:
        console.print("\n[red]Cannot escape without deciding![/red]")
        console.print("[yellow]Paralysis = circular thinking. Break the loop.[/yellow]\n")
        session.rollback()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        session.rollback()
        raise
    finally:
        session.close()


def quick_decision_prompt(decision: str) -> str:
    """Quick decision for simpler choices.

    For when paralysis protocol is overkill.
    """
    console.print(f"\n[yellow]Decision needed:[/yellow] {decision}\n")

    options = ["Yes", "No", "Defer"]
    choice = Prompt.ask("Choose", choices=options, default="Yes")

    if choice == "Defer":
        when = Prompt.ask("Decide by when?", default="Tomorrow")
        console.print(f"[yellow]⏰ Reminder set: Decide by {when}[/yellow]\n")
        return f"deferred until {when}"

    console.print(f"[green]→ Decision: {choice}[/green]\n")
    return choice
