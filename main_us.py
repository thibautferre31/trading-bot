from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re


URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


# -----------------------------
# SELENIUM FETCH
# -----------------------------
def fetch_page_selenium(url):
    print(f"\nLoading: {url}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(6)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        return driver.page_source

    finally:
        driver.quit()


# -----------------------------
# PARSING TABLE
# -----------------------------
def parse_table(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        print("❌ Table not found")
        return []

    tbody = table.find("tbody")
    if not tbody:
        print("❌ tbody not found")
        return []

    rows = []

    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")

        if len(cols) < 3:
            continue

        row = [c.get_text(" ", strip=True) for c in cols]
        rows.append(row)

    return rows


# -----------------------------
# CLEANING HELPERS
# -----------------------------
def clean_row(row):
    """
    enlève colonnes inutiles (comme demandé)
    on garde :
    ticker, name, analyst, price, price target, rating
    """
    if len(row) < 6:
        return row

    return [row[0], row[1], row[2], row[-3], row[-2], row[-1]]


def is_strong_buy(row):
    return "strong buy" in " ".join(row).lower()


def extract_price_target_diff(row):
    """
    extrait diff entre prix cible si format "x ➝ y"
    """
    text = row[-2]

    nums = re.findall(r"\$?(\d+\.?\d*)", text)

    if len(nums) >= 2:
        return float(nums[1]) - float(nums[0])
    elif len(nums) == 1:
        return float(nums[0])

    return 0


# -----------------------------
# UPGRADES PROCESS
# -----------------------------
def process_upgrades(rows):
    cleaned = []

    for r in rows:
        c = clean_row(r)

        cleaned.append({
            "row": c,
            "strong": is_strong_buy(c),
            "upside": extract_price_target_diff(c)
        })

    # TRI :
    # 1. Strong Buy en haut
    # 2. plus gros upside ensuite
    cleaned.sort(key=lambda x: (
        not x["strong"],
        -x["upside"]
    ))

    return cleaned


# -----------------------------
# DOWNGRADES PROCESS
# -----------------------------
def process_downgrades(rows):
    cleaned = []

    for r in rows:
        c = clean_row(r)

        cleaned.append({
            "row": c,
            "downside": extract_price_target_diff(c)
        })

    # plus mauvais en haut
    cleaned.sort(key=lambda x: x["downside"])

    return cleaned


# -----------------------------
# DISPLAY
# -----------------------------
def display(title, data):
    print(f"\n=== {title} ===\n")

    for item in data:
        print(" | ".join(item["row"]))
        print()


# -----------------------------
# MAIN
# -----------------------------
def run():
    print("=== MARKETBEAT FULL SCRAPER ===")

    upgrades_html = fetch_page_selenium(URLS["UPGRADES"])
    downgrades_html = fetch_page_selenium(URLS["DOWNGRADES"])

    upgrades_rows = parse_table(upgrades_html)
    downgrades_rows = parse_table(downgrades_html)

    print(f"\nUpgrades: {len(upgrades_rows)} lignes")
    print(f"Downgrades: {len(downgrades_rows)} lignes")

    upgrades = process_upgrades(upgrades_rows)
    downgrades = process_downgrades(downgrades_rows)

    display("UPGRADES SORTED", upgrades)
    display("DOWNGRADES SORTED", downgrades)


if __name__ == "__main__":
    run()
