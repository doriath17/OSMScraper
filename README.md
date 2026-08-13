# OSMScraper

OSMScraper is a Python utility for working with Online Soccer Manager (OSM) data from a local terminal. It can:

- open and reuse a saved browser session
- switch between saved league slots
- scrape transfer table data
- save per-league player CSV files and league metadata
- analyse players by budget, matchday, and projected profit
- run an interactive player calculator
- work in both browser mode and offline mode

The project is built around Playwright, Firefox, and Rich for a terminal UI and is named OSMScraper.

## Project layout

- `main.py` – main interactive dashboard/menu
- `save_state.py` – login/session saving flow
- `update_state.py` – refresh or update saved browser state
- `change_league.py` – switch between career/league slots
- `save_transfer_table.py` – scrape transfer table data and save league/player files
- `parse_data.py` – load saved data, analyse players, and render table output
- `interactive_player.py` – interactive player-value calculator
- `Player.py` – player model and pricing logic
- `TRParser.py` – transfer table HTML parsing helper
- `tmp/` – saved browser state, current league state, league data, and generated CSV/JSON files

## Requirements

Before you start, install the following:

- Python 3.10 or newer
- Firefox browser
- Playwright Python package and browser dependencies

## Installation

From the project root:

```bash
cd /home/ale/tmp/OSMScraper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m playwright install firefox
```

If you are using a different shell, replace the activation command as needed:

- macOS/Linux: `source .venv/bin/activate`
- PowerShell: `.venv\Scripts\Activate.ps1`

## Browser/session setup

The app stores your browser session state in:

```text
tmp/state.json
```

This file is used so you do not need to log in every time.

### Log in / save session

Run:

```bash
python3 save_state.py
```

This opens Firefox and waits for you to complete the login flow. Once you are logged in and verified, press Enter in the terminal to save the session state.

### Update session state

If you want to refresh the saved state after login or a page change:

```bash
python3 update_state.py
```

### Logout

From the main app menu choose the logout option, or delete the state file manually.

## Running the app

Start the main dashboard:

```bash
python3 main.py
```

### Command-line options

```bash
python3 main.py --headless
```

Runs the browser in headless mode.

```bash
python3 main.py --offline
```

Starts the app without launching the browser. This mode keeps the app local-only until you manually launch the browser from the menu.

## Main menu behaviour

When the browser is closed, the menu shows only:

1. Launch browser
2. Quit

When the browser is open, the menu also shows:

1. Run analysis
2. Scrape transfer table
3. Change league
4. Save state
5. Show saved leagues
6. Interactive player calculator
7. Close browser
8. Quit

## Browser lifecycle and offline mode

The app can run in two modes:

### Browser mode

This is the normal mode for live OSM access:

- the browser is launched
- the dashboard is opened
- league state can be checked or switched
- transfer table scraping works
- login/logout flows are available

### Offline mode

This mode is meant for local-only usage:

- no browser is launched
- the app does not attempt online scraping
- saved league/player data can still be used for analysis
- the browser can be launched manually later from the menu

This is useful when you want to inspect saved data without a live browser session.

## League switching

From the main menu:

- choose Change league
- choose the desired slot index (0 to 3)
- the app opens the career/league selection and loads the selected league
- the active league context is printed so you can see which team/league is loaded

The current league index is saved under:

```text
tmp/current_league.json
```

## Scraping transfer table data

Use the Transfer table option in the main menu or run the script directly:

```bash
python3 save_transfer_table.py
```

### CLI options

```bash
python3 save_transfer_table.py --headless
```

```bash
python3 save_transfer_table.py --slot-index 0
```

```bash
python3 save_transfer_table.py --offline
```

The scraper:

- opens the OSM dashboard
- reads the current league/team info
- opens the transfer table
- extracts player rows
- fetches market/base values when possible
- saves a per-league CSV file and league metadata

## Saved data format

League data is saved under:

```text
tmp/leagues/league_<index>/
```

Each league directory contains:

- `league_info.json`
- `league_<index>_<team>_players.csv`

Example:

```text
tmp/leagues/league_0/
    league_info.json
    league_0_ac_milan_players.csv
```

The league JSON contains values such as:

- team name
- league country
- matchday
- budget

The CSV stores player data like:

- name
- position
- age
- club
- attack
- defense
- overall
- main stat
- market value
- base value

## Analysis flow

Use Run analysis from the main menu or call:

```bash
python3 parse_data.py
```

This loads the current league data, filters players by budget and matchday, and prints a rich table showing candidate players and their estimated profit.

## Interactive player calculator

Use the interactive calculator from the main menu:

```bash
python3 main.py
```

Then choose:

- Interactive player calculator

The tool asks for:

- position
- age
- main stat
- base value
- market value
- matchday (from saved league data if available)

It then calculates a player price/profit profile.

## Typical workflow

1. Save your browser session:

   ```bash
   python3 save_state.py
   ```

2. Start the app:

   ```bash
   python3 main.py
   ```

3. Choose Change league and select a league slot.

4. Run Scrape transfer table to load and save league data.

5. Run analysis to see transfer targets and projected profit.

6. Use the interactive player calculator for custom values.

## Troubleshooting

### Playwright not installed

If you see a missing dependency error, run:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install firefox
```

### State file missing

If the app says the saved state file is missing, run:

```bash
python3 save_state.py
```

### Browser login issues

If login fails or session state is stale:

- log out from the app
- delete or refresh `tmp/state.json`
- run `save_state.py` again

### No leagues found

If there are no saved leagues, first scrape or load data for a league using the scraper flow.

## Notes

- This project expects live OSM pages to be reachable from the browser.
- The browser session is stored locally in `tmp/state.json`.
- All player and league tracking is saved under `tmp/` so it can be reused and analysed later.
- `--offline` is useful when you want to work only with saved data and avoid launching the browser.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
