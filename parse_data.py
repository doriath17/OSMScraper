import argparse
import csv
import json
import re
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from model.Player import Player

transfer_player_headers = {
    "NAME": "Name",
    "POSITION": "Position",
    "AGE": "Age",
    "CLUB": "Club",
    "ATTACK": "Attack",
    "DEFENSE": "Defense",
    "OVERALL": "Overall",
    "MAIN_STAT": "Main Stat",
    "MARKET_VALUE": "Market Value",
    "BASE_VALUE": "Base Value"
}

TRANSFER_PLAYERS_CSV_PATH = Path('./tmp/players_data.csv')
LEAGUE_INFO_JSON_PATH = Path('./tmp/league_info.json')
LEAGUE_ROOT_PATH = Path('./tmp/leagues')
CURRENT_LEAGUE_PATH = Path('./tmp/current_league.json')


def build_players_filename(slot_index: int, team_name: str | None = None) -> str:
    return f"league_{slot_index}_players.csv"

def build_transfer_history_filename(slot_index: int, team_name: str | None = None) -> str:
    return f"league_{slot_index}_transfer_history.csv"


def normalize_slot_index(slot_index: int | None) -> int:
    if slot_index is None:
        return 1

    index = int(slot_index)
    if index < 1:
        return 1
    return index


def get_current_league_index() -> int:
    if not CURRENT_LEAGUE_PATH.exists():
        return 1

    try:
        with open(CURRENT_LEAGUE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return normalize_slot_index(data.get('current_league', 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 1


def save_current_league_index(slot_index: int) -> Path:
    CURRENT_LEAGUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_index = normalize_slot_index(slot_index)
    with open(CURRENT_LEAGUE_PATH, 'w', encoding='utf-8') as file:
        json.dump({'current_league': int(normalized_index)}, file, indent=4)
    return CURRENT_LEAGUE_PATH


def get_league_paths(slot_index: int | None = None):
    league_index = normalize_slot_index(slot_index) if slot_index is not None else get_current_league_index()
    league_dir = LEAGUE_ROOT_PATH / f'league_{league_index}'
    league_dir.mkdir(parents=True, exist_ok=True)

    team_name = None
    league_info_path = league_dir / 'league_info.json'
    if league_info_path.exists():
        try:
            with open(league_info_path, 'r', encoding='utf-8') as file:
                team_name = json.load(file).get('team_name')
        except (json.JSONDecodeError, OSError, TypeError):
            team_name = None

    players_csv_path = league_dir / build_players_filename(league_index, team_name)
    transfer_history_csv_path = league_dir / build_transfer_history_filename(league_index, team_name)
    return league_index, league_dir, players_csv_path, transfer_history_csv_path, league_info_path


def load_transfer_players(slot_index: int | None = None) -> list[Player]:
    _, _, csv_file, _, _ = get_league_paths(slot_index)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    players = []

    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            club_value = (row.get(transfer_player_headers["CLUB"]) or row.get("Nationality") or "").strip()
            if not club_value and "Club" not in row:
                club_value = (row.get("Nationality") or "").strip()

            attack = int(row.get(transfer_player_headers["ATTACK"], 0) or 0)
            defense = int(row.get(transfer_player_headers["DEFENSE"], 0) or 0)
            overall = int(row.get(transfer_player_headers["OVERALL"], 0) or 0)
            main_stat = int(row.get(transfer_player_headers["MAIN_STAT"], overall) or overall)

            player = Player(
                name=row[transfer_player_headers["NAME"]],
                position=row[transfer_player_headers["POSITION"]],
                age=int(row[transfer_player_headers["AGE"]]),
                nationality="",
                club=club_value,
                attack=attack,
                defense=defense,
                overall=overall,
                main_stat=main_stat,
                market_value=float(row.get(transfer_player_headers["MARKET_VALUE"], 0.0) or 0.0),
                base_value=float(row.get(transfer_player_headers["BASE_VALUE"], 0.0) or 0.0)
            )
            players.append(player)

    return players


def load_league_info(slot_index: int | None = None) -> dict:
    _, _, _, _, league_info_path  = get_league_paths(slot_index)
    if not league_info_path.exists():
        raise FileNotFoundError(f"League info file not found: {league_info_path}")

    with open(league_info_path, "r", encoding="utf-8") as file:
        loaded_data = json.load(file)
    return loaded_data

def filter_players(
    players: list[Player], 
    budget: float, 
    op_budget: float, 
    matchday: int = 1, 
) -> list[Player]:
    """
    Filtra e ordina una lista di giocatori selezionando i migliori candidati 
    in base allo score di vendita generato dall'algoritmo.
    
    :param players: Lista degli oggetti Player da valutare.
    :param budget: Budget totale disponibile.
    :param op_budget: Budget operativo riservato al mercato rapido.
    :param matchday: Giornata di campionato corrente.
    :param free_slots: Numero massimo di giocatori da restituire (slot rosa liberi).
    :return: Lista dei primi 'free_slots' giocatori con lo score più alto.
    """
    valid_candidates = []

    for player in players:
        # Vincolo di acquistabilità: il costo di acquisto (market_value) 
        # non deve superare il budget operativo o totale disponibile
        if player.market_value <= op_budget and player.market_value <= budget:
            # Calcoliamo il prezzo di vendita ottimale e lo score
            sp_info = player.selling_price(
                budget=budget, 
                operative_budget=op_budget, 
                matchday=matchday
            )
            
            # Salviamo la tupla (player, score) per l'ordinamento
            valid_candidates.append((player, sp_info["score"]))

    # Ordiniamo i giocatori in ordine decrescente di score (dal migliore al peggiore)
    valid_candidates.sort(key=lambda item: item[1], reverse=True)

    return [player for player, score in valid_candidates]

def build_analysis_table(players: list[Player], matchday: int, budget: float, op_budget: float, limit: int | None = None, verbose: bool = False) -> Table:
    visible_players = players if limit is None else players[:limit]
    table = Table(
        title=f"Top transfer targets by score for matchday {matchday}",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        show_lines=False,
        expand=True,
    )

    anagraphic_style = "bold white"
    price_style = "bright_cyan"
    factors_style = "bright_magenta"

    table.add_column("Name", style=anagraphic_style, min_width=15)
    table.add_column("Pos", style=anagraphic_style, justify="center", width=6)
    table.add_column("Age", style=anagraphic_style, justify="center", width=5)
    table.add_column("Club", style=anagraphic_style, min_width=15)
    table.add_column("Main", style=anagraphic_style, justify="center", width=6)
    table.add_column("Base", style=price_style, justify="right", width=7)
    table.add_column("Market", style=price_style, justify="right", width=7)
    table.add_column("Sell", style=price_style, justify="right", width=7)
    table.add_column("Max Value", style=price_style, justify="right", width=7)
    table.add_column("Profit", style=price_style, justify="right", width=7)

    if verbose:
        table.add_column("Z", style=factors_style, justify="right", width=7)
        table.add_column("Prob", style=factors_style, justify="right", width=7)
        table.add_column("Est.", style=factors_style, justify="right", width=7)
        table.add_column("ROCE", style=factors_style, justify="right", width=7)
        table.add_column("Score", style=factors_style, justify="right", width=7)

    for player in visible_players:
        sp_result = player.selling_price(
            budget=budget, 
            operative_budget=op_budget, 
            matchday=matchday
        )

        # 2. Estrazione del prezzo e dei dettagli parziali già calcolati per quel prezzo ottimale
        sell_price = sp_result["price"]
        details = sp_result["details"]

        profit_value = details["profit"]
        estimated_value = details["ev"]
        prob_sale = details["p_sale"]
        roce = details["roce"]
        score = details["final_score"]
        z_score = details["z_score"]

        # sell_price = player.selling_price(matchday=matchday)["price"]
        # profit = player.profit(matchday=matchday)
        # z_score = player.z_score(matchday=matchday)
        # prob_sale = player.prob_sale(matchday=matchday)
        # estimated_value = player.exstimated_value(matchday=matchday)
        # roce = player.roce(matchday=matchday)
        # score = player.score(matchday=matchday, budget=budget, operative_budget=op_budget)
        profit_text = f"[red]{profit_value:.1f}M[/red]" if profit_value < 0 else f"[green]{profit_value:.1f}M[/green]"

        if verbose:
            table.add_row(
                player.name,
                player.position,
                str(player.age),
                player.club,
                str(player.main_stat),
                f"{player.base_value:.1f}M",
                f"{player.market_value:.1f}M",
                f"{sell_price:.1f}M",
                f"{player.max_price()}M",
                profit_text,
                f"{z_score:.2f}",
                f"{prob_sale:.0%}",
                f"{estimated_value:.1f}M",
                f"{roce:.2f}",
                f"{score:.1f}",
            )
        else:
            table.add_row(
                player.name,
                player.position,
                str(player.age),
                player.club,
                str(player.main_stat),
                f"{player.base_value:.1f}M",
                f"{player.market_value:.1f}M",
                f"{sell_price:.1f}M",
                f"{player.max_price()}M",
                profit_text,
            )

    return table


def get_saved_leagues() -> list[dict]:
    if not LEAGUE_ROOT_PATH.exists():
        return []

    saved = []
    for league_dir in sorted(LEAGUE_ROOT_PATH.glob("league_*"), key=lambda p: p.name):
        if not league_dir.is_dir():
            continue

        league_name = league_dir.name
        try:
            league_number = int(league_name.replace("league_", ""))
        except ValueError:
            continue

        if league_number < 1:
            continue

        info_path = league_dir / "league_info.json"
        if not info_path.exists():
            continue

        try:
            with open(info_path, "r", encoding="utf-8") as file:
                info = json.load(file)
        except json.JSONDecodeError:
            info = {}

        raw_index = info.get("league_index", league_number)
        league_index = max(1, int(raw_index))
        saved.append(
            {
                "index": league_index,
                "team_name": info.get("team_name", "Unknown team"),
                "league_country": info.get("league_country", "Unknown country"),
                "matchday": info.get("matchday", 0),
                "budget": info.get("budget", 0.0),
                "scraped_at": info.get("scraped_at", info.get("scraped_at_local", "Never")),
                "scraped_at_local": info.get("scraped_at_local", info.get("scraped_at", "Never")),
                "path": league_dir,
            }
        )

    return saved


def show_saved_leagues():
    console = Console()
    leagues = get_saved_leagues()

    if not leagues:
        console.print("[yellow]No saved leagues found in ./tmp/leagues.[/yellow]")
        return

    table = Table(title="Saved leagues", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Index", justify="center", width=8)
    table.add_column("Team", style="bold white", min_width=20)
    table.add_column("Country", min_width=18)
    table.add_column("Matchday", justify="center", width=10)
    table.add_column("Budget", justify="right", width=12)
    table.add_column("Scraped (local)", min_width=20)

    for league in leagues:
        index_label = str(league["index"])
        team_name = league["team_name"]
        if team_name and team_name != "Unknown team":
            index_label = f"{index_label} - {team_name}"

        table.add_row(
            index_label,
            team_name,
            league["league_country"],
            str(league["matchday"]),
            f"{league['budget']:.1f}M",
            str(league["scraped_at_local"]),
        )

    console.print(table)


def operative_budget(budget: float, security_deposit: float = 0.0, planned_expenses: float = 0.0, free_slots: int = 1) -> float:
    """Calculate the operative budget available for player transfers, considering free slots."""
    return max(0.0, budget - security_deposit - planned_expenses) / max(1, free_slots)

def run_analysis(league_index: int, limit: int | None = None, security_deposit: float = 0.0, planned_expenses: float = 0.0, free_slots: int = 1, verbose: bool = False, matchday_arg: int | None = None, budget_arg: float | None = None):
    console = Console()
    normalized_index = normalize_slot_index(league_index)

    _, _, players_csv_path, _, league_info_path = get_league_paths(normalized_index)

    try:
        players = load_transfer_players(normalized_index)
        league_info = load_league_info(normalized_index)
    except FileNotFoundError as exc:
        console.print(f"[yellow]No saved data found for league slot #{normalized_index}.[/yellow]")
        console.print(f"[cyan]{exc}[/cyan]")
        console.print(f"[cyan]Expected files:[/cyan] {players_csv_path} [cyan]and[/cyan] {league_info_path}")
        console.print("[cyan]Scrape this league first, then run analysis again.[/cyan]")
        return
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        console.print(f"[red]Saved data for league slot #{normalized_index} is invalid or incomplete.[/red]")
        console.print(f"[cyan]{exc}[/cyan]")
        console.print("[cyan]Re-scrape the league or delete the stale files under ./tmp/leagues to continue.[/cyan]")
        return

    matchday_stored = league_info.get("matchday", 0)
    matchday = matchday_arg if matchday_arg is not None else matchday_stored
    budget_stored = league_info.get("budget", 0.0)
    budget = budget_arg if budget_arg is not None else budget_stored

    op_budget = operative_budget(budget, security_deposit=security_deposit, planned_expenses=planned_expenses, free_slots=free_slots)

    console.print(f"[cyan]Using matchday {matchday} and budget {budget:.1f}M (operative budget: {op_budget:.1f}M) for analysis.[/cyan]")
    filtered_players = filter_players(players, budget=budget, op_budget=op_budget, matchday=matchday)

    team_name = league_info.get("team_name", "Unknown team")
    league_country = league_info.get("league_country", "Unknown country")

    scraped_at_local = league_info.get("scraped_at_local", league_info.get("scraped_at", "Never"))
    console.print(
        Panel.fit(
            f"[bold]Team[/bold]: {team_name}\n"
            f"[bold]League[/bold]: {league_country}\n"
            f"[bold]Matchday[/bold]: {matchday}\n"
            f"[bold]Budget[/bold]: {budget}M\n"
            f"[bold]Free slots[/bold]: {free_slots}\n"
            f"[bold]Last scraped[/bold]: {scraped_at_local}\n"
            f"[bold]Players loaded[/bold]: {len(players)}\n"
            f"[bold]Visible after filters[/bold]: {len(filtered_players)}",
            title="League snapshot",
            border_style="green",
        )
    )

    if not filtered_players:
        console.print("[yellow]No players match the current budget and matchday.[/yellow]")
        return

    console.print(build_analysis_table(filtered_players, matchday=matchday, budget=budget, op_budget=op_budget, limit=limit, verbose=verbose))

    console.print("")
    top_player = filtered_players[0]
    # 1. Una sola chiamata a selling_price passando i parametri richiesti
    sp_result = top_player.selling_price(
        budget=budget, 
        operative_budget=op_budget, 
        matchday=matchday
    )

    # 2. Estrazione del prezzo e dei dettagli parziali già calcolati per quel prezzo ottimale
    sell_price = sp_result["price"]
    details = sp_result["details"]

    profit_value = details["profit"]
    estimated_value = details["ev"]
    prob_sale = details["p_sale"]
    roce = details["roce"]
    score = details["final_score"]
    profit_style = "red" if profit_value < 0 else "green"
    console.print(
        Panel.fit(
            f"[bold]{top_player.name}[/bold] | {top_player.position} | {top_player.club}\n"
            f"Profit: [{profit_style}]{profit_value:.1f}M[/{profit_style}] | "
            f"Base: {top_player.base_value:.1f}M | Market: {top_player.market_value:.1f}M | Sell: {sell_price:.1f}M\n"
            f"Estimated value: {estimated_value:.1f}M | Prob. sale: {prob_sale:.0%} | Z-score: {details["z_score"]:.2f}\n"
            f"ROCE: {roce:.2f} | Score: {score:.1f}",
            title="Best current pick",
            border_style="cyan",
        )
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run analysis for a specific saved league slot.")
    parser.add_argument("--league-index", type=int, default=1, help="League slot index to analyze (1-based).")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of rows to show.")
    parser.add_argument("--free-slots", type=int, default=1, help="Number of free transfer slots to factor into the score.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output to see an in depth analysis.")
    parser.add_argument("--matchday", type=int, default=None, help="Optional Matchday specifier")
    parser.add_argument("--budget", type=float, default=None, help="Optional Budget specifier")

    args = parser.parse_args()
    
    run_analysis(league_index=args.league_index, limit=args.limit, free_slots=args.free_slots, verbose=args.verbose, matchday_arg=args.matchday, budget_arg=args.budget)

# example usage:
# clear; python parse_data.py --league-index 2 --free-slots 1 --verbose --limit 10 --matchday 3