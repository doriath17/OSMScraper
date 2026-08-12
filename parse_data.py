import csv
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

def filter_players(players: list[Player], preseason: bool = False, current_budget: float = 0.0, exclude_attackers: bool = False) -> list[Player]:
    if current_budget > 0.0:
        # delete too expensive players
        players = [player for player in players if player.selling_price(preseason) <= current_budget]
    if exclude_attackers:
        players = [player for player in players if not player.is_stricker()]
    return sorted(players, key=lambda p: p.profit(preseason), reverse=True)

if __name__ == "__main__":
    players = load_transfer_players()
    current_budget = 10.6 
    exclude_attackers = False
    sorted_players = filter_players(players, preseason=False, current_budget=current_budget, exclude_attackers=exclude_attackers)
    for player in sorted_players:
        print(f"[{player.name}, {player.position}]: Profit = {player.profit(preseason=False):.2f}, Base Value = {player.base_value:.2f}, Selling Price = {player.selling_price(preseason=False):.2f}")