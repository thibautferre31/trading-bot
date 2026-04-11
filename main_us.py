import time
import re
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from ai import analyze_marketbeat


URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


# -----------------------------
# SELENIUM DRIVER
# -----------------------------
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
    )

    return webdriver.Chrome(options=options)


def fetch_page(url):
    driver = create_driver()

    try:
        print(f"\nLoading: {url}")
        driver.get(url)

        time.sleep(6)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        return driver.page_source

    finally:
        driver.quit()


# -----------------------------
# PARSER
# -----------------------------
def parse_table(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = []

    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")

        if len(cols) < 3:
            continue

        row = [c.get_text(" ", strip=True) for c in cols]

        # conversion en dict structuré
        structured = normalize_row(row)
        if structured:
            rows.append(structured)

    return rows


# -----------------------------
# NORMALISATION ROW
# -----------------------------
def normalize_row(row):
    """
    transforme row brut en dict exploitable par AI
    """

    try:
        ticker_name = row[0].split(" ", 1)
        ticker = ticker_name[0]
        name = ticker_name[1] if len(ticker_name) > 1 else ""

        return {
            "ticker": ticker,
            "name": name,
            "analyst": row[1] if len(row) > 1 else "",
            "price": row[-3] if len(row) >= 3 else "",
            "price_target": row[-2] if len(row) >= 2 else "",
            "rating": row[-1] if len(row) >= 1 else ""
        }

    except:
        return None


# -----------------------------
# DISPLAY
# -----------------------------
def display(title, data):
    print(f"\n=== {title} ===\n")

    for x in data[:10]:
        print(
            x.get("ticker"),
            "|",
            x.get("rating"),
            "|",
            x.get("price"),
            "|",
            x.get("price_target"),
            "|",
            x.get("market_cap")
        )


# -----------------------------
# MAIN
# -----------------------------
def run():
    print("=== MARKETBEAT FULL PIPELINE ===")

    # -------------------------
    # SCRAPING
    # -------------------------
    upgrades_html = fetch_page(URLS["UPGRADES"])
    downgrades_html = fetch_page(URLS["DOWNGRADES"])

    upgrades = parse_table(upgrades_html)
    downgrades = parse_table(downgrades_html)

    print(f"\nRaw upgrades: {len(upgrades)}")
    print(f"Raw downgrades: {len(downgrades)}")

    if not upgrades and not downgrades:
        print("No data scraped")
        return

    # -------------------------
    # AI PROCESSING
    # -------------------------
    result = analyze_marketbeat(upgrades, downgrades)

    # -------------------------
    # DISPLAY RESULTS
    # -------------------------
    print("\n============================")
    print("FINAL SORTED UPGRADES")
    print("============================")

    display("UPGRADES", result["upgrades"])

    print("\n============================")
    print("FINAL SORTED DOWNGRADES")
    print("============================")

    display("DOWNGRADES", result["downgrades"])

    # -------------------------
    # JSON OUTPUT
    # -------------------------
    print("\n=== FULL JSON OUTPUT ===\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
