import time
from pathlib import Path
import re
import csv
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError
from TRParser import TRParser
from Player import Player, to_number
from parse_data import transfer_player_headers

# Imports for Rich TUI
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

def scrape_transfer_table(playwright: Playwright) -> None:
    start_time = time.perf_counter()

    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(storage_state="./tmp/state.json")
    page = context.new_page()
    page.goto("https://en.onlinesoccermanager.com/Dashboard", wait_until="domcontentloaded")

    raw_text = page.locator("a.matchday-title").first.text_content() or ""
    match = re.search(r"\d+", raw_text)
    matchday = int(match.group()) if match else 0
    with open("./tmp/league_info.txt", "w") as f:
        f.write(f'Matchday: {matchday}')

    # input("Press ENTER to continue after verifying the page has loaded...")
    # context.storage_state(path="./tmp/state.json")
    # context.close()
    # browser.close()

    elapsed_time = time.perf_counter() - start_time
    print(f"Total time elapsed: {elapsed_time:.2f} seconds")


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
                player = Player(
                    name=cleaned[0],
                    position=cleaned[1],
                    age=int(cleaned[2]),
                    nationality=cleaned[3],
                    club=cleaned[4],
                    attack=int(cleaned[5]),
                    defense=int(cleaned[6]),
                    overall=int(cleaned[7]),
                    market_value=to_number(cleaned[8])
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
                    value_locator.wait_for(state="visible", timeout=4000)

                    base_value_raw = value_locator.text_content()
                    base_value = to_number(base_value_raw)
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

    with open(csv_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            transfer_player_headers["NAME"], transfer_player_headers["POSITION"], transfer_player_headers["AGE"], transfer_player_headers["NATIONALITY"],
            transfer_player_headers["CLUB"], transfer_player_headers["ATTACK"], transfer_player_headers["DEFENSE"], transfer_player_headers["OVERALL"], transfer_player_headers["MARKET_VALUE"], transfer_player_headers["BASE_VALUE"]
        ])

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
        scrape_transfer_table(playwright)