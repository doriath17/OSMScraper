import json
import re
from datetime import datetime, timezone
from typing import Any

from rich.console import Console

from feature.routing.BrowserState import BrowserState
from model.utils import to_number
from parse_data import get_league_paths

console = Console()

def scrape_league_info(*, browser_state: BrowserState) -> dict[str, Any]:
    """Read and persist league metadata for the currently active dashboard league."""
    page = browser_state.page

    page.wait_for_load_state("networkidle", timeout=30000)

    wallet_locator = page.locator(".wallet-amount span.pull-right").first
    wallet_locator.wait_for(state="visible", timeout=5000)

    raw_budget = (wallet_locator.text_content() or "").strip()
    budget = to_number(raw_budget)

    page.wait_for_selector("#club-name, #competition-name", timeout=20000)
    team_name = (page.locator("#club-name .club-name-text").first.text_content() or "").strip()
    league_country = (page.locator("#competition-name").first.text_content() or "").strip()

    raw_text = page.locator("a.matchday-title").first.text_content() or ""
    match = re.search(r"\d+", raw_text)
    matchday = int(match.group()) if match else 0

    league_index, _, _, _, league_info_path = get_league_paths()
    scraped_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    scraped_at_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "league_index": league_index,
        "team_name": team_name,
        "league_country": league_country,
        "matchday": matchday,
        "budget": budget,
        "scraped_at": scraped_at_utc,
        "scraped_at_local": scraped_at_local,
    }

    with open(league_info_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    console.print(f"[bold green]League info saved to {league_info_path}[/bold green]")
    return data