

from pathlib import Path

from rich.console import Console

from update_state import STATE_FILE

console = Console()

class BrowserState: 
    def __init__(self, browser, context, page):
        # the browser is guaranteed to be a valid Playwright browser instance, context is a valid browser context, and page is a valid page instance
        if browser is None or context is None or page is None:
            print("[bold red]Error: Browser, context, and page must all be provided to initialize BrowserState.[/bold red]")
            raise SystemExit(1)
        
        self.browser = browser
        self.context = context
        self.page = page

    def is_initialized(self) -> bool:
        return self.browser is not None and self.context is not None and self.page is not None

    # TODO: implement set methods to avoid None values being set after initialization, or make the attributes read-only after initialization

def launch_browser(playwright, headless: bool = False, state_filename: str = "./tmp/state.json") -> BrowserState:
    if not Path(state_filename).exists():
        console.print(f"[yellow]Warning:[/yellow] '{state_filename}' not found yet. You can log in later to create it.")

    browser = playwright.firefox.launch(headless=headless)
    context = browser.new_context(storage_state=state_filename) if Path(state_filename).exists() else browser.new_context()
    page = context.new_page()

    console.print("[bold green]Browser launched.[/bold green]")

    return BrowserState(browser, context, page)

def open_browser_state(browser_state: BrowserState, playwright):
    if browser_state.browser is None or browser_state.context is None or browser_state.page is None:
        console.print("[bold red]Browser state is not fully initialized.[/bold red]")
        return

    # Use the existing browser, context, and page
    browser = browser_state.browser
    context = browser_state.context
    page = browser_state.page

    # Navigate to the OSM website
    page.goto("https://en.onlinesoccermanager.com/")