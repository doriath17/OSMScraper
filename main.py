import argparse

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from change_league import STATE_FILE
from feature.routing.BrowserState import BrowserState, launch_browser
from feature.routing.league_selection import open_league_selection, select_league
from interactive_player import main as run_interactive_player
from parse_data import get_saved_leagues, run_analysis, show_saved_leagues
from save_state import login_session, logout_session, save_context_state
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
            "[bold cyan]l[/bold cyan]) Launch browser\n"
            "[bold cyan]ra[/bold cyan]) Run analysis\n"
            "[bold cyan]sl[/bold cyan]) Show saved leagues\n"
            "[bold cyan]ipc[/bold cyan]) Interactive player calculator\n"
            "[bold cyan]q[/bold cyan]) Quit",
        ]
        choices = ["l", "ra", "sl", "ipc", "q"]
    else:
        options = [
            "[bold cyan]ra[/bold cyan]) Run analysis\n"
            "[bold cyan]stt[/bold cyan]) Scrape transfer table\n"
            "[bold cyan]goto sl[/bold cyan]) Goto Select League\n"
            "[bold cyan]sl[/bold cyan]) Select League\n"
            "[bold cyan]ss[/bold cyan]) Save state\n"
            "[bold cyan]show sl[/bold cyan]) Show saved leagues\n"
            "[bold cyan]ipc[/bold cyan]) Interactive player calculator\n"
            "[bold cyan]cb[/bold cyan]) Close browser\n"
            "[bold cyan]q[/bold cyan]) Quit",
        ]
        choices = ["ra", "stt", "goto sl", "ss", "sl", "show sl", "ipc", "cb", "q"]

    console.print(Panel.fit("".join(options), title="OSM Manager", border_style="green"))
    return Prompt.ask("Choose an option", choices=choices).strip()


def ask_for_slot_index():
    available_slots = []
    saved_leagues = {league["index"]: league for league in get_saved_leagues()}

    for slot_index in range(1, 5):
        league_name = saved_leagues.get(slot_index, {}).get("team_name")
        available_slots.append(slot_index)

    console.print("Available league slots:")
    for slot_index in available_slots:
        league_name = saved_leagues.get(slot_index, {}).get("team_name")
        if league_name and league_name != "Unknown team":
            console.print(f"[cyan]{slot_index}[/cyan] - {league_name}")
        else:
            console.print(f"[cyan]{slot_index}[/cyan]")

    while True:
        raw = Prompt.ask("Enter league index", choices=[str(slot) for slot in available_slots])
        try:
            return int(raw.strip())
        except ValueError:
            console.print("[red]Please choose a valid league index.[/red]")


def run_bot(headless: bool = False, offline: bool = False):
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        console.print("[bold red]Playwright is not installed.[/bold red]")
        console.print("Install dependencies with: [bold cyan]pip install -r requirements.txt[/bold cyan]")
        raise SystemExit(1)

    if offline:
        console.print("[yellow]Offline mode enabled: browser is not launched. You can still use saved data, or launch the browser from the menu.[/yellow]")

    with sync_playwright() as playwright:
        browser_state: None | BrowserState = None

        while True:
            action = prompt_action(browser_state is not None)

            if not browser_state:
                if action == "l":
                    browser_state = launch_browser(playwright, headless=headless)
                    open_league_selection(browser_state)
                    continue
                if action == "ra":
                    console.print("[bold green]Running analysis using saved local data...[/bold green]")
                    run_analysis()
                    continue
                if action == "sl":
                    console.print("[bold green]Saved leagues overview:[/bold green]")
                    show_saved_leagues()
                    continue
                if action == "ipc":
                    console.print("[bold green]Opening interactive player calculator...[/bold green]")
                    run_interactive_player()
                    continue
                if action in {"q", "quit", "exit"}:
                    console.print("[bold red]Exiting.[/bold red]")
                    break
                console.print("[red]Invalid option. Please choose from the visible menu.[/red]")
                continue

            if action == "ra":
                console.print("[bold green]Running analysis using the currently loaded player data...[/bold green]")
                run_analysis()
                continue

            if action == "stt":
                console.print("[bold green]Scraping transfer table and saving the league context...[/bold green]")
                scrape_transfer_table(
                    playwright,
                    state_file=STATE_FILE,
                    browser=browser_state.browser,
                    context=browser_state.context,
                    page=browser_state.page,
                )
                continue

            if action == "goto sl":
                open_league_selection(browser_state)
                continue

            if action == "sl":
                print_current_league_context(browser_state.page)
                slot_index = ask_for_slot_index()
                console.print(f"[bold yellow]Changing to league slot #{slot_index}...[/bold yellow]")
                select_league(browser_state, slot_index)
                print_current_league_context(browser_state.page)
                console.print(f"[bold green]League slot #{slot_index} selected.[/bold green]")
                console.print("[cyan]You are now on the league page. Choose your next action from the dashboard.[/cyan]")
                continue

            if action == "ss":
                if browser_state.context is None:
                    console.print("[bold red]No browser context available to save.[/bold red]")
                    continue
                console.print("[bold green]Saving current browser state...[/bold green]")
                save_context_state(browser_state.context, STATE_FILE)
                continue

            if action == "show sl":
                console.print("[bold green]Saved leagues overview:[/bold green]")
                show_saved_leagues()
                continue

            if action == "ipc":
                console.print("[bold green]Opening interactive player calculator...[/bold green]")
                run_interactive_player()
                continue

            if action == "cb":
                console.print("[bold yellow]Closing browser...[/bold yellow]")
                browser_state.browser.close()
                browser_state = None
                console.print("[bold cyan]Browser closed. Only local options remain until you launch it again.[/bold cyan]")
                continue

            if action in {"q", "quit", "exit"}:
                console.print("[bold red]Exiting.[/bold red]")
                break

            console.print("[red]Invalid option. Please choose from the visible menu.[/red]")

        if browser_state is not None:
            browser_state.browser.close()


# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSM manager dashboard")
    parser.add_argument("--headless", action="store_true", help="Launch the browser in headless mode for faster background scraping.")
    parser.add_argument("--offline", action="store_true", help="Start without opening the browser and use saved in-memory data only until you launch the browser manually.")
    parser.add_argument("--login", action="store_true", help="Run the login flow as a standalone command and exit.")
    parser.add_argument("--logout", action="store_true", help="Run the logout flow as a standalone command and exit.")
    args = parser.parse_args()

    if args.login:
        login_session()
        raise SystemExit(0)

    if args.logout:
        logout_session()
        raise SystemExit(0)

    run_bot(headless=args.headless, offline=args.offline)