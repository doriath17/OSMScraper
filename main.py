# from html.parser import HTMLParser

# ## you can copy the transfer table from the osm web page using:
# # copy(document.querySelector('table').outerHTML); in the browser console and save it to a file called table.html in the data folder 

# class TRParser(HTMLParser):
#     def __init__(self):
#         super().__init__()
#         self.in_tr = False
#         self.current_row = []
#         self.rows = []

#     def handle_starttag(self, tag, attrs):
#         if tag == 'tr':
#             self.in_tr = True
#             self.current_row = []
#         elif tag == 'td' and self.in_tr:
#             self.current_row.append('')

#     def handle_endtag(self, tag):
#         if tag == 'tr':
#             self.in_tr = False
#             self.rows.append(self.current_row)
#         elif tag == 'td' and self.in_tr:
#             pass

#     def handle_data(self, data):
#         if self.in_tr and self.current_row is not None:
#             if len(self.current_row) > 0:
#                 self.current_row[-1] += data.strip()

# table_rows = []
# parser = TRParser()

# with open('./data/table.html', 'r') as file:
#     html_content = file.read()

# parser.feed(html_content)
# table_rows = parser.rows

# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']
# class Player: 
#     def __init__(self, name, position, age, nationality, club, attack, defense, overall, market_value):

# print("Extracted Table Rows:")
# for row in table_rows:
#     print(row)

# from playwright.sync_api import sync_playwright

# with sync_playwright() as p:
#     # Launch Firefox (set headless=True to run without opening a visible browser window)
#     browser = p.firefox.launch(headless=False)
    
#     page = browser.new_page()
#     page.goto("https://en.onlinesoccermanager.com/")

#     # Playwright automatically waits for the element to be attached, visible, and enabled
#     # page.click("button#my-button-id")

#     # Keep browser open briefly to see the result if running headed

#     page.pause()  # This will pause the script and allow you to inspect the page

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