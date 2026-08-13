import argparse
import time
import re
import csv
from typing import TYPE_CHECKING

from feature.routing.BrowserState import BrowserState

if TYPE_CHECKING:
    from playwright.sync_api import Playwright

try:
    from playwright.sync_api import sync_playwright
    PlaywrightTimeoutError = TimeoutError
except ModuleNotFoundError:
    sync_playwright = None
    PlaywrightTimeoutError = TimeoutError

from TRParser import TRParser
from Player import Player, to_number
from parse_data import (
    get_league_paths,
    transfer_player_headers,
)

# Imports for Rich TUI
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

# NOTE: this scraper assumes: 
# 1. The user is already logged in and has a valid session.
# 2. The user is on the dashboard page of the OSM website 
#       This means the user navigated to the dashboard league through the main loop
def scrape_transfer_table(
    *,
    browser_state: BrowserState,
) -> None:
    start_time = time.perf_counter()

    page = browser_state.page

    _, _, players_csv_path, _ = get_league_paths()

    link = page.get_by_role("link", name=re.compile(r"^Transfer", re.IGNORECASE)).first
    link.click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=30000)

    selector = "table" 
    page.wait_for_selector(selector, timeout=30000)

    table_html = page.locator(selector).inner_html()
    parser = TRParser()
    parser.feed(table_html)
    table_rows = parser.rows

    players = []
    modal = page.locator(".modal-dialog, .modal, [role='dialog']").first

    # --- TUI Setup ---
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    )
    task = progress.add_task("[cyan]Processing players...", total=len(table_rows))

    status_text = Text("Initializing...", style="bold yellow")

    def make_layout():
        layout = Layout()
        layout.split_column(
            Layout(Panel(progress, title="Scraper Progress"), size=5),
            Layout(Panel(status_text, title="Current Status"), size=3)
        )
        return layout

    # Render TUI during loop
    with Live(make_layout(), refresh_per_second=10) as live:
        for index, row in enumerate(table_rows):
            cleaned = [cell for cell in row if cell]

            if len(cleaned) >= 9:
                attack = int(cleaned[4])
                defense = int(cleaned[5])
                overall = int(cleaned[6])
                main_stat = int(cleaned[7])
                market_value = to_number(cleaned[8]) if len(cleaned) > 8 else 0.0

                player = Player(
                    name=cleaned[0],
                    position=cleaned[1],
                    age=int(cleaned[2]),
                    nationality="",
                    club=cleaned[3],
                    attack=attack,
                    defense=defense,
                    overall=overall,
                    main_stat=main_stat,
                    market_value=float(market_value or 0.0),
                    base_value=0.0,
                )
                
                # Update TUI message in-place
                status_text.plain = f"[{index + 1}/{len(table_rows)}] Processing: {player.name} ({player.position} {player.age} {player.nationality})"
                status_text.style = "bold green"
                progress.update(task, completed=index + 1)
                
                try:
                    player_cell = page.locator("table").get_by_role("cell", name=player.name).first
                    player_cell.scroll_into_view_if_needed()
                    player_cell.click()

                    value_locator = page.locator(".player-profile-value span[data-bind*='currency']:visible").first
                    value_locator.wait_for(state="visible", timeout=8000)

                    base_value_raw = value_locator.text_content()
                    base_value = to_number(base_value_raw)
                    player.set_base_value(base_value)

                    page.get_by_label("Close").first.click(force=True)
                    page.wait_for_timeout(500)

                except PlaywrightTimeoutError:
                    status_text.plain = f"[Warning] Timeout on {player.name}. Skipping..."
                    status_text.style = "bold red"
                    if modal.is_visible():
                        try:
                            page.get_by_label("Close").first.click(force=True)
                            page.wait_for_timeout(300)
                        except Exception:
                            pass
                except Exception as err:
                    status_text.plain = f"[Error] {player.name}: {err}"
                    status_text.style = "bold red"

                players.append(player)

    # Save to the active league-specific CSV
    players_csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(players_csv_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            transfer_player_headers["NAME"], transfer_player_headers["POSITION"], transfer_player_headers["AGE"],
            transfer_player_headers["CLUB"], transfer_player_headers["ATTACK"], transfer_player_headers["DEFENSE"],
            transfer_player_headers["OVERALL"], transfer_player_headers["MAIN_STAT"], transfer_player_headers["MARKET_VALUE"], transfer_player_headers["BASE_VALUE"]
        ])

        for p in players:
            writer.writerow([
                p.name, p.position, p.age,
                p.club, p.attack, p.defense, p.overall, p.main_stat, p.market_value, p.base_value
            ])

    console.print(f"[bold green]CSV successfully written to {players_csv_path}[/bold green]")

    elapsed_time = time.perf_counter() - start_time
    console.print(f"[cyan]Total time elapsed: {elapsed_time:.2f} seconds[/cyan]")


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape the OSM transfer table for a league.")
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode to improve performance.")
    parser.add_argument("--state-file", default="./tmp/state.json", help="Browser storage state JSON file to reuse.")
    parser.add_argument("--slot-index", type=int, default=None, help="Optional league slot index to scrape explicitly.")
    parser.add_argument("--offline", action="store_true", help="Use saved in-memory data without launching the browser.")
    return parser


if __name__ == "__main__":
    args = _build_argument_parser().parse_args()
    if sync_playwright is None:
        console.print("[bold red]Playwright is not installed.[/bold red]")
        console.print("Install dependencies with: [bold cyan]pip install -r requirements.txt[/bold cyan]")
        raise SystemExit(1)

    if args.offline:
        console.print("[yellow]Offline mode: using saved league data without launching the browser.[/yellow]")
        from parse_data import run_analysis
        run_analysis()
        raise SystemExit(0)

    from feature.routing.BrowserState import launch_browser
    from feature.routing.league_selection import open_league_selection, select_league

    with sync_playwright() as playwright:
        browser_state = launch_browser(playwright, headless=args.headless, state_filename=args.state_file)
        if args.slot_index is not None:
            open_league_selection(browser_state)
            select_league(browser_state, args.slot_index)
        else:
            browser_state.page.goto("https://en.onlinesoccermanager.com/")
        try:
            scrape_transfer_table(browser_state=browser_state)
        finally:
            browser_state.browser.close()