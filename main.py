from pathlib import Path

from playwright.sync_api import sync_playwright

from change_league import STATE_FILE, open_career_selection, select_league_slot
from parse_data import run_analysis
from save_transfer_table import scrape_transfer_table


def prompt_action():
    print("\nWhat do you want to do?")
    print("1) Run analysis")
    print("2) Scrape transfer table")
    print("3) Change league")
    print("4) Quit")
    return input("Choose an option [1/2/3/4]: ").strip()


def ask_for_slot_index():
    while True:
        raw = input("Enter league index (0-3): ").strip()
        try:
            slot_index = int(raw)
        except ValueError:
            print("Please enter a valid integer.")
            continue

        if slot_index not in (0, 1, 2, 3):
            print("League index must be one of: 0, 1, 2, 3")
            continue

        return slot_index


def run_bot():
    if not Path(STATE_FILE).exists():
        print(f"Error: '{STATE_FILE}' not found. Run save_state.py first.")
        return

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        try:
            print("Opening dashboard...")
            page.goto("https://en.onlinesoccermanager.com/")

            while True:
                action = prompt_action()

                if action == "1":
                    print("Running analysis using the currently loaded player data...")
                    run_analysis()
                    continue

                if action == "2":
                    print("Scraping transfer table and saving the league context...")
                    scrape_transfer_table(
                        playwright,
                        state_file=STATE_FILE,
                        browser=browser,
                        context=context,
                        page=page,
                    )
                    continue

                if action == "3":
                    print("Opening career/league selection...")
                    open_career_selection(page)
                    slot_index = ask_for_slot_index()
                    print(f"Changing to league slot #{slot_index}...")
                    select_league_slot(page, slot_index)
                    print(f"League slot #{slot_index} selected.")
                    print("You are now on the league page. Choose next action from the dashboard when ready.")
                    continue

                if action in {"4", "q", "quit", "exit"}:
                    print("Exiting.")
                    break

                print("Invalid option. Please choose 1, 2, 3, or 4.")
        finally:
            browser.close()


# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    run_bot()