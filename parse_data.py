import csv
import json
from pathlib import Path
from Player import Player

transfer_player_headers = {
    "NAME": "Name",
    "POSITION": "Position",
    "AGE": "Age",
    "NATIONALITY": "Nationality",
    "CLUB": "Club",
    "ATTACK": "Attack",
    "DEFENSE": "Defense",
    "OVERALL": "Overall",
    "MARKET_VALUE": "Market Value",
    "BASE_VALUE": "Base Value"
}

TRANSFER_PLAYERS_CSV_PATH = Path('./tmp/players_data.csv')
LEAGUE_INFO_JSON_PATH = Path('./tmp/league_info.json')

def load_transfer_players() -> list[Player]:
    csv_file = TRANSFER_PLAYERS_CSV_PATH
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    players = []

    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            player = Player(
                name=row[transfer_player_headers["NAME"]],
                position=row[transfer_player_headers["POSITION"]],
                age=int(row[transfer_player_headers["AGE"]]),
                nationality=row[transfer_player_headers["NATIONALITY"]],
                club=row[transfer_player_headers["CLUB"]],
                attack=int(row[transfer_player_headers["ATTACK"]]),
                defense=int(row[transfer_player_headers["DEFENSE"]]),
                overall=int(row[transfer_player_headers["OVERALL"]]),
                market_value=float(row[transfer_player_headers["MARKET_VALUE"]]),
                base_value=float(row[transfer_player_headers["BASE_VALUE"]])
            )
            players.append(player)

    return players

def load_league_info() -> dict:
    if not LEAGUE_INFO_JSON_PATH.exists():
        raise FileNotFoundError(f"League info file not found: {LEAGUE_INFO_JSON_PATH}")

    with open(LEAGUE_INFO_JSON_PATH, "r", encoding="utf-8") as file:
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

def run_analysis():
    players = load_transfer_players()

    league_info = load_league_info()
    matchday = league_info.get("matchday", 0)
    budget = league_info.get("budget", 0.0)
    
    filtered_players = filter_players(players, current_budget=budget, matchday=matchday)

    print(f"Matchday: {matchday}")
    print(f"Budget: {budget}M")
    print(f"Total Players Loaded: {len(players)}")
    for player in filtered_players:
        analyze_player(player, matchday=matchday)

if __name__ == "__main__":
    run_analysis()