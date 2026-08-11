from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = "./tmp/state.json"

def update_session():
    if not Path(STATE_FILE).exists():
        print(f"Error: '{STATE_FILE}' not found. Run save_state.py first.")
        return

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        page.goto("https://en.onlinesoccermanager.com/")

        print(f"--> Loaded session from '{STATE_FILE}'.")
        
        input("--> Press ENTER here to overwrite state.json...")

        context.storage_state(path=STATE_FILE)
        print(f"--> Success! Updated state saved back to '{STATE_FILE}'.")
        
        browser.close()

if __name__ == "__main__":
    update_session()