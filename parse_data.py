import csv
import json
import re
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from Player import Player

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
    return league_index, league_dir, players_csv_path, league_info_path


def load_transfer_players(slot_index: int | None = None) -> list[Player]:
    _, _, csv_file, _ = get_league_paths(slot_index)
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
    _, _, _, league_info_path = get_league_paths(slot_index)
    if not league_info_path.exists():
        raise FileNotFoundError(f"League info file not found: {league_info_path}")

    with open(league_info_path, "r", encoding="utf-8") as file:
        loaded_data = json.load(file)
    return loaded_data

def filter_players(players: list[Player], current_budget: float = 0.0, matchday: int = 1) -> list[Player]:
    if current_budget > 0.0:
        # delete too expensive players
        players = [player for player in players if player.selling_price(matchday=matchday)["price"] <= current_budget]
    return sorted(players, key=lambda p: p.profit(matchday=matchday), reverse=True)

def analyze_player(player: Player, matchday: int = 1):
    selling_price_info = player.selling_price(matchday=matchday)
    print(f"[{player.name}, {player.position}]: Profit = {player.profit(matchday=matchday):.2f}, Base Value = {player.base_value:.2f}, Selling Price = {selling_price_info['price']:.2f}")
    print(f"  Breakdown: Base Ratio = {selling_price_info['breakdown']['base_ratio']}, Age Modifier = {selling_price_info['breakdown']['age_modifier']}, OVR Modifier = {selling_price_info['breakdown']['ovr_modifier']}, Position Modifier = {selling_price_info['breakdown']['pos_modifier']}")

def build_analysis_table(players: list[Player], matchday: int, limit: int = 10) -> Table:
    table = Table(
        title=f"Top transfer targets for matchday {matchday}",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        show_lines=False,
        expand=True,
    )

    table.add_column("Name", style="bold white", min_width=18)
    table.add_column("Pos", justify="center", width=6)
    table.add_column("Age", justify="center", width=5)
    table.add_column("Club", min_width=18)
    table.add_column("Main", justify="center", width=6)
    table.add_column("Base", justify="right", width=8)
    table.add_column("Market", justify="right", width=10)
    table.add_column("Sell", justify="right", width=8)
    table.add_column("Profit", justify="right", width=10)

    for player in players[:limit]:
        sell_price = player.selling_price(matchday=matchday)["price"]
        profit = player.profit(matchday=matchday)
        profit_text = f"[red]{profit:.1f}M[/red]" if profit < 0 else f"[green]{profit:.1f}M[/green]"
        table.add_row(
            player.name,
            player.position,
            str(player.age),
            player.club,
            str(player.main_stat),
            f"{player.base_value:.1f}M",
            f"{player.market_value:.1f}M",
            f"{sell_price:.1f}M",
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


def run_analysis(limit: int = 10):
    console = Console()

    try:
        players = load_transfer_players()
        league_info = load_league_info()
    except FileNotFoundError as exc:
        console.print("[yellow]No saved data found for the current league.[/yellow]")
        console.print(f"[cyan]{exc}[/cyan]")
        console.print("[cyan]Scrape a league first, or switch to an existing saved league before running analysis.[/cyan]")
        return
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        console.print("[red]The saved league data is invalid or incomplete.[/red]")
        console.print(f"[cyan]{exc}[/cyan]")
        console.print("[cyan]Re-scrape the league or delete the stale files under ./tmp/leagues to continue.[/cyan]")
        return

    matchday = league_info.get("matchday", 0)
    budget = league_info.get("budget", 0.0)

    filtered_players = filter_players(players, current_budget=budget, matchday=matchday)

    team_name = league_info.get("team_name", "Unknown team")
    league_country = league_info.get("league_country", "Unknown country")

    scraped_at_local = league_info.get("scraped_at_local", league_info.get("scraped_at", "Never"))
    console.print(
        Panel.fit(
            f"[bold]Team[/bold]: {team_name}\n"
            f"[bold]League[/bold]: {league_country}\n"
            f"[bold]Matchday[/bold]: {matchday}\n"
            f"[bold]Budget[/bold]: {budget}M\n"
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

    console.print(build_analysis_table(filtered_players, matchday=matchday, limit=limit))

    console.print("")
    top_player = filtered_players[0]
    sell_price = top_player.selling_price(matchday=matchday)["price"]
    profit_value = top_player.profit(matchday=matchday)
    profit_style = "red" if profit_value < 0 else "green"
    console.print(
        Panel.fit(
            f"[bold]{top_player.name}[/bold] | {top_player.position} | {top_player.club}\n"
            f"Profit: [{profit_style}]{profit_value:.1f}M[/{profit_style}] | "
            f"Base: {top_player.base_value:.1f}M | Market: {top_player.market_value:.1f}M | Sell: {sell_price:.1f}M",
            title="Best current pick",
            border_style="cyan",
        )
    )

if __name__ == "__main__":
    run_analysis()