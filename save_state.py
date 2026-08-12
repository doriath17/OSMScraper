from pathlib import Path

from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()
STATE_FILE = "./tmp/state.json"


def save_session():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://en.onlinesoccermanager.com/")

        console.print("[bold yellow]--> Please complete the login and email verification in the Firefox browser.[/bold yellow]")
        input("--> Once fully logged in, press ENTER here in the terminal to save session...")

        context.storage_state(path=STATE_FILE)
        console.print(f"[bold green]--> Session saved to {STATE_FILE}.[/bold green]")
        browser.close()


def login_session():
    console.print("[bold cyan]Login flow started.[/bold cyan]")
    save_session()


def logout_session():
    state_path = Path(STATE_FILE)
    if state_path.exists():
        state_path.unlink()
        console.print(f"[bold yellow]--> Logged out: removed {STATE_FILE}.[/bold yellow]")
    else:
        console.print(f"[bold yellow]--> No active session found at {STATE_FILE}.[/bold yellow]")


if __name__ == "__main__":
    login_session()