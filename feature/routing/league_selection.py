

# open the browser and navigate to the OSM website to the main page: 
# for us the main page will be the league selection page
# From here the user can select a league to open

import json
from pathlib import Path

from rich.console import Console
console = Console()

from feature.routing.BrowserState import BrowserState
from feature.league.scrape_league_info import scrape_league_info

def open_league_selection(browser_state: BrowserState):
    console.print("[bold green]Opening career/league selection...[/bold green]")
    browser_state.page.goto("https://en.onlinesoccermanager.com/")

CURRENT_LEAGUE_PATH = Path('./tmp/current_league.json')

def normalize_slot_index(slot_index: int | None) -> int:
    if slot_index is None:
        return 1

    index = int(slot_index)
    if index < 1:
        return 1
    return index

def save_current_league_index(slot_index: int) -> Path:
    CURRENT_LEAGUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_index = normalize_slot_index(slot_index)
    with open(CURRENT_LEAGUE_PATH, 'w', encoding='utf-8') as file:
        json.dump({'current_league': int(normalized_index)}, file, indent=4)
    return CURRENT_LEAGUE_PATH

def select_league(browser_state: BrowserState, slot_index=1):
    """Click one of the career slots in the manager selection grid."""
    page = browser_state.page
    slots = page.locator(".career-teamslot-wrapper")
    count = slots.count()

    if count == 0:
        raise RuntimeError("No career slots were found on the page.")

    if slot_index < 1 or slot_index > count:
        raise ValueError(f"slot_index={slot_index} is out of range for {count} slots")

    zero_based_slot_index = slot_index - 1
    slot = slots.nth(zero_based_slot_index)
    slot.locator(".career-teamslot-container").click(force=True)

    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(1000)

    save_current_league_index(slot_index)

    # After switching leagues, return to the dashboard home page so the updated league is visible.
    home_link = page.get_by_role("link", name="Home")
    home_link.wait_for(state="visible", timeout=20000)
    home_link.click()
    page.wait_for_url("**/Dashboard", timeout=20000)
    page.wait_for_load_state("domcontentloaded", timeout=20000)

    scrape_league_info(browser_state=browser_state)