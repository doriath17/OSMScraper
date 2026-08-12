from pathlib import Path

from playwright.sync_api import sync_playwright

STATE_FILE = "./tmp/state.json"

def open_career_selection(page):
    """From the dashboard, open the career/league selection view."""
    page.goto("https://en.onlinesoccermanager.com/")

    # The username in the dashboard header opens the account menu.
    page.locator(".manager-name-text.ellipsis").first.click()

    # Then choose Career from the menu.
    page.locator("a.menu-item.stop-propagation[href='/Career']").first.click()

    page.wait_for_url("**/Career", timeout=20000)
    page.wait_for_selector(".career-teamslot-wrapper", timeout=20000)


def select_league_slot(page, slot_index=0):
    """Click one of the four career slots in the manager selection grid."""
    slots = page.locator(".career-teamslot-wrapper")
    count = slots.count()

    if count == 0:
        raise RuntimeError("No career slots were found on the page.")

    if slot_index < 0 or slot_index >= count:
        raise ValueError(f"slot_index={slot_index} is out of range for {count} slots")

    # Use the nth child of the container to select the slot you want.
    slot = slots.nth(slot_index)
    slot.locator(".career-teamslot-container").click(force=True)

    page.wait_for_load_state("networkidle", timeout=20000)


def run_change_league(slot_index=0):
    if not Path(STATE_FILE).exists():
        print(f"Error: '{STATE_FILE}' not found. Run save_state.py first.")
        return

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        open_career_selection(page)
        select_league_slot(page, slot_index)

        print(f"Opened dashboard -> Career -> selected slot #{slot_index}.")

        input("Press ENTER to close the browser...\n")
        browser.close()


if __name__ == "__main__":
    # 0 and 1 are typically the active manager slots; 2 and 3 are often locked.
    run_change_league(slot_index=0)
