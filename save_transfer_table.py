import time
from pathlib import Path
import re
import csv
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError
from TRParser import TRParser
from Player import Player

# Imports for Rich TUI
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

def run(playwright: Playwright) -> None:
    start_time = time.perf_counter()

    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(storage_state="./tmp/state.json")
    page = context.new_page()
    page.goto("https://en.onlinesoccermanager.com/Dashboard")

    link = page.get_by_role("link", name=re.compile(r"^Transfer", re.IGNORECASE)).first
    link.click()

    selector = "table" 
    page.wait_for_selector(selector)

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
            
            if len(cleaned) == 9:
                player = Player(*cleaned)
                
                # Update TUI message in-place
                status_text.plain = f"[{index + 1}/{len(table_rows)}] Processing: {player.name} ({player.club})"
                status_text.style = "bold green"
                progress.update(task, completed=index + 1)
                
                try:
                    player_cell = page.locator("table").get_by_role("cell", name=player.name).first
                    player_cell.scroll_into_view_if_needed()
                    player_cell.click()

                    value_locator = page.locator(".player-profile-value span[data-bind*='currency']:visible").first
                    value_locator.wait_for(state="visible", timeout=4000)

                    base_value = value_locator.text_content()
                    player.set_base_value(base_value)

                    page.get_by_label("Close").first.click(force=True)
                    page.wait_for_timeout(300)

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

    # Save to CSV
    csv_path = Path('./tmp/players_data.csv')
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()

    headers = [
        'Name', 'Position', 'Age', 'Nationality', 
        'Club', 'Attack', 'Defense', 'Overall', 'Market Value', 'Base Value'
    ]

    with open(csv_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)

        for p in players:
            writer.writerow([
                p.name, p.position, p.age, p.nationality,
                p.club, p.attack, p.defense, p.overall, p.market_value, p.base_value
            ])

    print("CSV successfully written to ./tmp/players_data.csv")

    context.storage_state(path="./tmp/state.json")
    context.close()
    browser.close()

    elapsed_time = time.perf_counter() - start_time
    print(f"Total time elapsed: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)