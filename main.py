from playwright.sync_api import sync_playwright

def run_bot():
    with sync_playwright() as p: 
        browser = p.firefox.launch(headless=False)

        context = browser.new_context(storage_state="./tmp/state.json")
        page = context.new_page()

        page.goto("https://en.onlinesoccermanager.com/")

        input("Press ENTER in the terminal to exit...")
        browser.close()

# playwright codegen --browser firefox --load-storage=state.json --save-storage=state.json https://en.onlinesoccermanager.com/

if __name__ == "__main__":
    run_bot()