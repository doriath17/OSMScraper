import re
from rich.console import Console

from feature.routing.BrowserState import BrowserState
console = Console()

def open_transfer_page(browser_state: BrowserState):
    """Navigate to the Transfer page on the OSM dashboard."""
    console.print("[bold cyan]--> Navigating to the Transfer page...[/bold cyan]")

    page = browser_state.page

    page.goto("https://en.onlinesoccermanager.com/Dashboard", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(1000)

    link = page.get_by_role("link", name=re.compile(r"^Transfer", re.IGNORECASE)).first
    link.click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=30000)