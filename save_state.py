from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    sync_playwright = None
from rich.console import Console

console = Console()
STATE_FILE = "./tmp/state.json"


def save_context_state(context, state_file=STATE_FILE):
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(state_path))
    console.print(f"[bold green]--> Session saved to {state_file}.[/bold green]")


def save_session():
    if sync_playwright is None:
        console.print("[bold red]Playwright is not installed.[/bold red]")
        console.print("Install dependencies with: [bold cyan]pip install -r requirements.txt[/bold cyan]")
        raise SystemExit(1)

    state_path = Path(STATE_FILE)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://en.onlinesoccermanager.com/")

        console.print("[bold yellow]--> Please complete the login and email verification in the Firefox browser.[/bold yellow]")
        input("--> Once fully logged in, press ENTER here in the terminal to save session...")

        save_context_state(context, STATE_FILE)
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