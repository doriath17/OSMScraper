import argparse
import csv

from rich.console import Console

from feature.league.transfer_history_scraper import get_transfer_history_save_path
from model.Transfer import Transfer

console = Console()

def load_search_history(file_path: str) -> list[Transfer]:
    """Load the search history from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            next(reader)  # Skip header
            return [Transfer(
                name=row['Player Name'],
                from_team=row['From Team'],
                to_team=row['To Team'],
                position=row['Position'],
                age=int(row['Age']),
                base_value=float(row['Base Value']),
                market_value=float(row['Market Value']),
                transfer_date=row['Transfer Date']
            ) for row in reader]
    except FileNotFoundError:
        console.print(f"[bold red]Error: File not found - {file_path}[/bold red]")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find a player in the loaded transfer history")
    parser.add_argument("--name", type=str, help="Name of the player to search for")
    args = parser.parse_args()

    file_path = get_transfer_history_save_path() 

    search_history = load_search_history(file_path)
    player_name = args.name
    found_transfer = None
    for transfer in search_history:
        if transfer.name == player_name:
            found_transfer = transfer
            break

    if found_transfer:
        found_transfer.print()
    else:
        console.print(f"[bold red]{player_name} not found in search history.[/bold red]")
