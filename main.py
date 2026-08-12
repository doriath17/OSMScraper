from playwright.sync_api import sync_playwright
from parse_data import filter_players, load_transfer_players
from save_transfer_table import scrape_transfer_table

def run_bot():
    with sync_playwright() as playwright:
        scrape_transfer_table(playwright)

    players = load_transfer_players()
    current_budget = 10.6 
    exclude_attackers = False
    sorted_players = filter_players(players, preseason=False, current_budget=current_budget, exclude_attackers=exclude_attackers)
    for player in sorted_players:
        print(f"[{player.name}, {player.position}]: Profit = {player.profit(preseason=False):.2f}, Base Value = {player.base_value:.2f}, Selling Price = {player.selling_price(preseason=False):.2f}")

# playwright codegen --browser firefox --load-storage=./tmp/state.json --save-storage=./tmp/state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    run_bot()