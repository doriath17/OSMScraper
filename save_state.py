from playwright.sync_api import sync_playwright

def save_session():
    with sync_playwright() as p: 
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://en.onlinesoccermanager.com/")

        print("--> Please complete the login and email verification in the Firefox browser.")
        input("--> Once fully logged in, press ENTER here in the terminal to save session...")

        context.storage_state(path="./tmp/state.json")
        print("--> Session saved to ./tmp/state.json.")
        browser.close()

if __name__ == "__main__":
    save_session()