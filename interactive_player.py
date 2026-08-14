import json
from pathlib import Path

from rich.console import Console
from rich.prompt import IntPrompt, FloatPrompt, Prompt
from rich.panel import Panel
from rich.table import Table

from model.Player import Player

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



    # while True: 
    #     budget = IntPrompt.ask("Budget")

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
    # 1. Recupero dell'input (inclusi i budget se gestiti dal prompt)
    pos, age, main_stat, base_value, market_value, matchday = prompt_interactive()
    
    # Esempio: definisci o recupera i budget correnti della sessione
    budget = 30.0
    op_budget = 10.0

    # 2. Istanziazione rapida di un Player temporaneo per calcolare prezzo e metriche
    player = Player(
        name="Interactive Player",
        position=str(pos),
        age=age,
        nationality="",
        club="",
        attack=main_stat,
        defense=main_stat,
        overall=main_stat,
        main_stat=main_stat,
        market_value=market_value,
        base_value=base_value
    )

    # 3. Calcolo ottimizzato del prezzo e dei dettagli
    sp_info = player.selling_price(
        budget=budget, 
        operative_budget=op_budget, 
        matchday=matchday
    )
    
    recommended_price = sp_info["price"]
    details = sp_info["details"]

    # 4. Costruzione della tabella Rich
    table = Table(show_header=False, box=None)
    table.add_column("Label", style="bold cyan")
    table.add_column("Value")

    # Dati Giocatore (conversione esplicita a str per evitare warning su PlayerPosition)
    table.add_row("Player Position", pos)
    table.add_row("Age", str(age))
    table.add_row("Main stat", str(main_stat))
    table.add_row("Base value", f"{base_value:.1f}M")
    table.add_row("Market value", f"{market_value:.1f}M")
    table.add_row("Matchday", str(matchday))
    
    # Separatore visivo prima dei risultati
    table.add_section()

    # Dettagli dell'Algoritmo di Vendita
    table.add_row("Recommended Sell", f"[bold yellow]{recommended_price:.1f}M[/bold yellow]")
    table.add_row("Est. Profit", f"+{details['profit']:.1f}M")
    table.add_row("Sale Prob. (P_sale)", f"{details['p_sale'] * 100:.1f}%")
    table.add_row("ROCE", f"{details['roce']:.2f}")
    table.add_row("Algorithmic Score", f"[bold green]{details['final_score']:.3f}[/bold green]")

    console.print()
    console.print(Panel.fit(table, title="[bold green]Player summary[/bold green]", border_style="green"))

if __name__ == "__main__":
    main()