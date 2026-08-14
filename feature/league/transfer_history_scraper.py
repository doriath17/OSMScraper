import csv
import re
import time

from rich.console import Console

from model.Player import Player
from TRParser import TRParser
from feature.routing.BrowserState import BrowserState
from model.Transfer import Transfer
from model.utils import to_number
from parse_data import get_current_league_index, get_league_paths

console = Console()

def scrape_transfer_history(
    browser_state: BrowserState,
    load_more: bool = True,
):
    """Scrape the transfer history for the current league.
    This function assumes the user is already logged in and on the dashboard page of the OSM website.
    If load_more is True, it will click the "Load More" button until all rows are loaded.
    """
    start = time.perf_counter()

    open_transfer_history_tab(browser_state)
    page = browser_state.page
    if load_more:
        load_more_transfer_history(page)
    transfers = scrape_transfer_history_table(page)
    save_transfer_history(transfers)

    elapsed = time.perf_counter() - start
    console.print(f"[bold green]--> Transfer history scraping completed in {elapsed:.2f} seconds.[/bold green]")


def open_transfer_history_tab(browser_state: BrowserState):
    """Navigate to the Transfer History tab on the OSM dashboard.
    Assumes the user is already on the Transfer page.
    """
    console.print("[bold cyan]--> Navigating to the Transfer History tab...[/bold cyan]")

    page = browser_state.page

    history_link = page.locator("a[href='#transfer-history']")
    history_link.wait_for(state="visible", timeout=20000)
    history_link.click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=30000)

    console.print('[bold cyan]--> Navigated to the Transfer History tab.[/bold cyan]')

def load_more_transfer_history(page):
    """Click the "Load More" button until all transfer history rows are loaded."""
    console.print("[bold cyan]--> Loading all transfer history rows...[/bold cyan]")

    container = page.locator("#transfer-history")
    container.wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(1000)

    load_more_btn = container.locator("button", has_text=re.compile(r"More transfers", re.IGNORECASE))

    container = page.locator("#transfer-history")
    load_more_btn = container.locator("button", has_text=re.compile(r"More transfers", re.IGNORECASE))

    while True:
        if load_more_btn.count() == 0:
            break

        if not load_more_btn.first.is_visible():
            break

        try:
            load_more_btn.first.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            load_more_btn.first.click()
            page.wait_for_timeout(1500)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_selector("#transfer-history .btn-loader:not([style*='display: none'])", state="detached", timeout=10000)
            page.wait_for_timeout(500)
        except Exception:
            break

    console.print("[bold cyan]--> All transfer history rows loaded.[/bold cyan]")

def scrape_transfer_history_table(page) -> list[Transfer]:
    """Parse and print the raw transfer-history table rows for inspection."""

    console.print("[bold cyan]--> Saving transfer history...[/bold cyan]")

    table_locator = page.locator("#transfer-history table").first
    if table_locator.count() == 0:
        console.print("[yellow]No transfer-history table found.[/yellow]")
        return []

    table_html = table_locator.inner_html()
    parser = TRParser()
    parser.feed(table_html)

    rows = parser.rows
    console.print(f"[bold cyan]Transfer history rows: {len(rows)}[/bold cyan]")

    transfers: list[Transfer] = []
    for index, row in enumerate(rows, start=1):
        if len(row) < 8:
            console.print(f"[yellow]Skipping row {index} due to insufficient columns: {row}[/yellow]")
            continue

        player_name, from_team, to_team, position, age, base_value, market_value, date_time = row[:8]

        try:
            transfer = Transfer(
                name=player_name,
                from_team=from_team,
                to_team=to_team,
                position=position,
                age=int(age),
                base_value=to_number(base_value),
                market_value=to_number(market_value),
                transfer_date=date_time
            )
        except ValueError as e:
            console.print(f"[yellow]Skipping row {index} due to error: {e}. Row data: {row}[/yellow]")
            continue

        transfers.append(transfer)

    return transfers

def get_transfer_history_save_path() -> str:
    """Get the path to save the transfer history CSV file."""
    league_index = get_current_league_index()
    _, _, _, transfer_history_csv_path, _ = get_league_paths(league_index)
    return str(transfer_history_csv_path)

def save_transfer_history(transfers: list[Transfer]):
    """Save the transfer history to a CSV file."""

    file_path = get_transfer_history_save_path()
    console.print(f"[bold cyan]--> Saving transfer history to {file_path}...[/bold cyan]")

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Player Name', 'From Team', 'To Team', 'Position', 'Age', 'Base Value', 'Market Value', 'Transfer Date'])
        for transfer in transfers:
            writer.writerow([
                transfer.name,
                transfer.from_team,
                transfer.to_team,
                transfer.position,
                transfer.age,
                transfer.base_value,
                transfer.market_value,
                transfer.transfer_date
            ])

    console.print(f"[bold green]Transfer history saved to {file_path}[/bold green]")