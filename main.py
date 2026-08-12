from pathlib import Path

from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from change_league import STATE_FILE, open_career_selection, select_league_slot
from interactive_player import main as run_interactive_player
from parse_data import run_analysis, show_saved_leagues
from save_state import login_session, logout_session
from save_transfer_table import scrape_transfer_table

console = Console()


def prompt_action():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]1[/bold cyan]) Run analysis\n"
            "[bold cyan]2[/bold cyan]) Scrape transfer table\n"
            "[bold cyan]3[/bold cyan]) Change league\n"
            "[bold cyan]4[/bold cyan]) Login\n"
            "[bold cyan]5[/bold cyan]) Logout\n"
            "[bold cyan]6[/bold cyan]) Show saved leagues\n"
            "[bold cyan]7[/bold cyan]) Interactive player calculator\n"
            "[bold cyan]8[/bold cyan]) Quit",
            title="OSM Manager",
            border_style="green",
        )
    )
    return Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7", "8"]).strip()


def ask_for_slot_index():
    while True:
        raw = Prompt.ask("Enter league index", choices=["0", "1", "2", "3"])
        return int(raw)


def run_bot():
    if not Path(STATE_FILE).exists():
        console.print(f"[bold red]Error:[/bold red] '{STATE_FILE}' not found. Run save_state.py first.")
        return

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        try:
            console.print("[bold yellow]Opening dashboard...[/bold yellow]")
            page.goto("https://en.onlinesoccermanager.com/")

            while True:
                action = prompt_action()

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
                    slot_index = ask_for_slot_index()
                    console.print(f"[bold yellow]Changing to league slot #{slot_index}...[/bold yellow]")
                    select_league_slot(page, slot_index)
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

                if action in {"8", "q", "quit", "exit"}:
                    console.print("[bold red]Exiting.[/bold red]")
                    break

                console.print("[red]Invalid option. Please choose 1, 2, 3, 4, 5, 6, 7, or 8.[/red]")
        finally:
            browser.close()


# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    run_bot()