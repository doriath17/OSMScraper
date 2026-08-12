import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from change_league import STATE_FILE, open_career_selection, select_league_slot
from interactive_player import main as run_interactive_player
from parse_data import run_analysis, show_saved_leagues
from save_state import login_session, logout_session
from save_transfer_table import scrape_transfer_table

console = Console()


def print_current_league_context(page):
    url = page.url
    team_name = ""
    league_name = ""

    try:
        team_name = (page.locator("#club-name .club-name-text").first.text_content() or "").strip()
    except Exception:
        team_name = ""

    try:
        league_name = (page.locator("#competition-name").first.text_content() or "").strip()
    except Exception:
        league_name = ""

    if team_name or league_name:
        message = f"Current league context: Team='{team_name or 'Unknown'}' | League='{league_name or 'Unknown'}' | URL='{url}'"
    elif "/Career" in url or "career" in url.lower():
        message = "Current league context: Career selection screen (no active league loaded)."
    else:
        message = "Current league context: Dashboard / no active league loaded."

    console.print(f"[bold cyan]{message}[/bold cyan]")


def prompt_action(browser_open: bool):
    console.print()
    if not browser_open:
        options = [
            "[bold cyan]1[/bold cyan]) Launch browser\n"
            "[bold cyan]2[/bold cyan]) Run analysis\n"
            "[bold cyan]3[/bold cyan]) Show saved leagues\n"
            "[bold cyan]4[/bold cyan]) Interactive player calculator\n"
            "[bold cyan]5[/bold cyan]) Quit",
        ]
        choices = ["1", "2", "3", "4", "5"]
    else:
        options = [
            "[bold cyan]1[/bold cyan]) Run analysis\n"
            "[bold cyan]2[/bold cyan]) Scrape transfer table\n"
            "[bold cyan]3[/bold cyan]) Change league\n"
            "[bold cyan]4[/bold cyan]) Login\n"
            "[bold cyan]5[/bold cyan]) Logout\n"
            "[bold cyan]6[/bold cyan]) Show saved leagues\n"
            "[bold cyan]7[/bold cyan]) Interactive player calculator\n"
            "[bold cyan]8[/bold cyan]) Close browser\n"
            "[bold cyan]9[/bold cyan]) Quit",
        ]
        choices = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

    console.print(Panel.fit("".join(options), title="OSM Manager", border_style="green"))
    return Prompt.ask("Choose an option", choices=choices).strip()


def ask_for_slot_index():
    while True:
        raw = Prompt.ask("Enter league index", choices=["0", "1", "2", "3"])
        return int(raw)


def run_bot(headless: bool = False, offline: bool = False):
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        console.print("[bold red]Playwright is not installed.[/bold red]")
        console.print("Install dependencies with: [bold cyan]pip install -r requirements.txt[/bold cyan]")
        raise SystemExit(1)

    browser = None
    context = None
    page = None

    if offline:
        console.print("[yellow]Offline mode enabled: browser is not launched. You can still use saved data, or launch the browser from the menu.[/yellow]")

    with sync_playwright() as playwright:
        while True:
            action = prompt_action(browser is not None)

            if not browser:
                if action == "1":
                    if not Path(STATE_FILE).exists():
                        console.print(f"[yellow]Warning:[/yellow] '{STATE_FILE}' not found yet. You can log in later to create it.")
                    browser = playwright.firefox.launch(headless=headless)
                    context = browser.new_context(storage_state=STATE_FILE) if Path(STATE_FILE).exists() else browser.new_context()
                    page = context.new_page()
                    console.print("[bold green]Browser launched.[/bold green]")
                    console.print("[bold yellow]Opening dashboard...[/bold yellow]")
                    page.goto("https://en.onlinesoccermanager.com/")
                    print_current_league_context(page)
                    continue
                if action == "2":
                    console.print("[bold green]Running analysis using saved local data...[/bold green]")
                    run_analysis()
                    continue
                if action == "3":
                    console.print("[bold green]Saved leagues overview:[/bold green]")
                    show_saved_leagues()
                    continue
                if action == "4":
                    console.print("[bold green]Opening interactive player calculator...[/bold green]")
                    run_interactive_player()
                    continue
                if action in {"5", "q", "quit", "exit"}:
                    console.print("[bold red]Exiting.[/bold red]")
                    break
                console.print("[red]Invalid option. Please choose from the visible menu.[/red]")
                continue

            if action == "1":
                console.print("[bold green]Running analysis using the currently loaded player data...[/bold green]")
                run_analysis()
                continue

            if action == "2":
                console.print("[bold green]Scraping transfer table and saving the league context...[/bold green]")
                scrape_transfer_table(
                    playwright,
                    state_file=STATE_FILE,
                    browser=browser,
                    context=context,
                    page=page,
                )
                continue

            if action == "3":
                console.print("[bold green]Opening career/league selection...[/bold green]")
                open_career_selection(page)
                print_current_league_context(page)
                slot_index = ask_for_slot_index()
                console.print(f"[bold yellow]Changing to league slot #{slot_index}...[/bold yellow]")
                select_league_slot(page, slot_index)
                print_current_league_context(page)
                console.print(f"[bold green]League slot #{slot_index} selected.[/bold green]")
                console.print("[cyan]You are now on the league page. Choose your next action from the dashboard.[/cyan]")
                continue

            if action == "4":
                console.print("[bold green]Starting login flow...[/bold green]")
                login_session()
                continue

            if action == "5":
                console.print("[bold yellow]Logging out...[/bold yellow]")
                logout_session()
                continue

            if action == "6":
                console.print("[bold green]Saved leagues overview:[/bold green]")
                show_saved_leagues()
                continue

            if action == "7":
                console.print("[bold green]Opening interactive player calculator...[/bold green]")
                run_interactive_player()
                continue

            if action == "8":
                console.print("[bold yellow]Closing browser...[/bold yellow]")
                browser.close()
                browser = None
                context = None
                page = None
                console.print("[bold cyan]Browser closed. Only local options remain until you launch it again.[/bold cyan]")
                continue

            if action in {"9", "q", "quit", "exit"}:
                console.print("[bold red]Exiting.[/bold red]")
                break

            console.print("[red]Invalid option. Please choose from the visible menu.[/red]")

        if browser is not None:
            browser.close()


# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSM manager dashboard")
    parser.add_argument("--headless", action="store_true", help="Launch the browser in headless mode for faster background scraping.")
    parser.add_argument("--offline", action="store_true", help="Start without opening the browser and use saved in-memory data only until you launch the browser manually.")
    args = parser.parse_args()
    run_bot(headless=args.headless, offline=args.offline)