import json
from pathlib import Path

from rich.console import Console
from rich.prompt import IntPrompt, FloatPrompt, Prompt
from rich.panel import Panel
from rich.table import Table

from Player import get_selling_price

console = Console()
CURRENT_LEAGUE_PATH = Path("./tmp/current_league.json")
LEAGUE_ROOT_PATH = Path("./tmp/leagues")


def get_saved_matchday() -> int | None:
    if not CURRENT_LEAGUE_PATH.exists():
        return None

    try:
        with open(CURRENT_LEAGUE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

    league_index = data.get("current_league")
    if league_index is None:
        return None

    league_dir = LEAGUE_ROOT_PATH / f"league_{league_index}"
    info_path = league_dir / "league_info.json"
    if not info_path.exists():
        return None

    try:
        with open(info_path, "r", encoding="utf-8") as file:
            info = json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

    matchday = info.get("matchday")
    return int(matchday) if isinstance(matchday, (int, float)) else None


def prompt_interactive():
    console.print(Panel.fit("[bold cyan]OSM Selling Price Calculator[/bold cyan]", border_style="cyan"))

    pos = Prompt.ask("Position", default="ST").strip().upper()

    while True:
        age = IntPrompt.ask("Age", default=25)
        if 15 <= age <= 45:
            break
        console.print("[red]Age must be between 15 and 45.[/red]")

    while True:
        main_stat = IntPrompt.ask("Main stat", default=82)
        if 0 <= main_stat <= 200:
            break
        console.print("[red]Main stat must be between 0 and 200.[/red]")

    while True:
        base_value = FloatPrompt.ask("Base value in millions", default=12.5)
        if base_value > 0:
            break
        console.print("[red]Base value must be positive.[/red]")

    while True:
        market_value = FloatPrompt.ask("Market value in millions", default=10.0)
        if market_value >= 0:
            break
        console.print("[red]Market value cannot be negative.[/red]")

    while True: 
        matchday = IntPrompt.ask("Matchday", default=get_saved_matchday() or 0)
        if matchday >= 0:
            break
        console.print("[red]Matchday must be a positive integer.[/red]")

    return pos, age, main_stat, base_value, market_value, matchday


def main():
    pos, age, main_stat, base_value, market_value, matchday = prompt_interactive()
    price_info = get_selling_price(pos, age, main_stat, base_value, matchday)
    recommended_price = price_info["price"]

    table = Table(show_header=False, box=None)
    table.add_column("Label", style="bold cyan")
    table.add_column("Value")
    table.add_row("Player", f"[{pos}]")
    table.add_row("Age", str(age))
    table.add_row("Main stat", str(main_stat))
    table.add_row("Base value", f"{base_value:.1f}M")
    table.add_row("Market value", f"{market_value:.1f}M")
    table.add_row("Matchday", str(matchday))
    table.add_row("Recommended sell", f"{recommended_price:.1f}M")

    console.print()
    console.print(Panel.fit(table, title="[bold green]Player summary[/bold green]", border_style="green"))


if __name__ == "__main__":
    main()