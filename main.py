from playwright.sync_api import sync_playwright
from parse_data import filter_players, load_transfer_players, run_analysis
from save_transfer_table import scrape_transfer_table

def run_bot():
    with sync_playwright() as playwright:
        scrape_transfer_table(playwright)

    run_analysis()

# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    run_bot()