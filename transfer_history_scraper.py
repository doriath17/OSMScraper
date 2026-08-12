
import argparse
import re
import time

from rich.console import Console

from TRParser import TRParser


console = Console()


def print_transfer_history_table(page):
    """Parse and print the raw transfer-history table rows for inspection."""
    table_locator = page.locator("#transfer-history table").first
    if table_locator.count() == 0:
        console.print("[yellow]No transfer-history table found.[/yellow]")
        return []

    table_html = table_locator.inner_html()
    parser = TRParser()
    parser.feed(table_html)

    rows = parser.rows
    console.print(f"[bold cyan]Transfer history rows: {len(rows)}[/bold cyan]")

    for index, row in enumerate(rows, start=1):
        console.print(f"[bold]Row {index}:[/bold] {row}")

    return rows


def scrape_transfer_history(
        playwright,
        state_file="./tmp/state.json",
        browser=None,
        context=None,
        page=None,
        slot_index: int | None = None,
        headless: bool = False,
):
    start = time.perf_counter()

    if browser is None:
        browser = playwright.firefox.launch(headless=headless)
    if context is None:
        context = browser.new_context(storage_state=state_file)
    if page is None:
        page = context.new_page()

    page.goto("https://en.onlinesoccermanager.com/Dashboard", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(1000)

    link = page.get_by_role("link", name=re.compile(r"^Transfer", re.IGNORECASE)).first
    link.click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=30000)

    link = page.locator("a[href='#transfer-history']")
    link.wait_for(state="visible", timeout=20000)
    link.click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=30000)

    console.print('[bold cyan]--> Navigated to the Transfer History tab.[/bold cyan]')

    container = page.locator("#transfer-history")
    container.wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(1000)

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

    print_transfer_history_table(page)

    context.storage_state(path=state_file)
    if context is not None and page is None: 
        context.close()
    if browser is not None and page is None:
        browser.close()

    elaspsed = time.perf_counter() - start
    console.print(f"[bold green]--> Transfer history scraping completed in {elaspsed:.2f} seconds.[/bold green]")


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the OSM transfer history for a league.")
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode.")
    parser.add_argument("--state-file", default="./tmp/state.json", help="Browser storage state JSON file to reuse.")
    return parser


if __name__ == "__main__":
    args = _build_argument_parser().parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        console.print("[bold red]Playwright is not installed.[/bold red]")
        console.print("Install dependencies with: [bold cyan]pip install -r requirements.txt[/bold cyan]")
        raise SystemExit(1)

    with sync_playwright() as playwright:
        scrape_transfer_history(
            playwright,
            state_file=args.state_file,
            headless=args.headless,
        )

