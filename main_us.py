from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re


URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


# =========================
# SELENIUM SCRAPER
# =========================

def fetch_page_selenium(url):
    print(f"\nLoading: {url}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
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


# =========================
# PARSING RAW TABLE
# =========================

def parse_raw_table(html):
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

        if len(cols) < 5:
            continue

        row = [c.get_text(" ", strip=True) for c in cols]
        rows.append(row)

    return rows


# =========================
# CLEANING + FEATURE ENGINEERING
# =========================

def extract_price(price_str):
    match = re.search(r"[\d,.]+", price_str)
    return float(match.group().replace(",", "")) if match else None


def extract_target(target_str):
    if not target_str:
        return None

    nums = re.findall(r"[\d,.]+", target_str)
    if not nums:
        return None

    return float(nums[-1].replace(",", ""))


def clean_rows(rows):
    cleaned = []

    for r in rows:
        if len(r) < 5:
            continue

        ticker = r[0]
        upgraded_by = r[1]
        analyst = r[2]
        price_str = r[3]
        target_str = r[4] if len(r) > 4 else ""
        rating = r[-1]

        current_price = extract_price(price_str)
        price_target = extract_target(target_str)

        if not price_target:
            price_target = current_price

        gap = price_target - current_price if current_price else 0

        cleaned.append({
            "ticker": ticker,
            "upgraded_by": upgraded_by,
            "analyst": analyst,
            "current_price": current_price,
            "price_target": price_target,
            "rating": rating,
            "gap": gap
        })

    return cleaned


# =========================
# SORTING LOGIC
# =========================

def sort_upgrades(data):
    def score(x):
        strong_buy_bonus = 1000 if "Strong-Buy" in x["rating"] or "Strong Buy" in x["rating"] else 0
        return strong_buy_bonus + x["gap"]

    return sorted(data, key=score, reverse=True)


def sort_downgrades(data):
    return sorted(data, key=lambda x: x["gap"], reverse=True)


# =========================
# DISPLAY
# =========================

def display(data, title):
    print(f"\n==================== {title} ====================\n")

    for d in data:
        print(
            f"{d['ticker']} | "
            f"{d['rating']} | "
            f"{d['current_price']} → {d['price_target']} | "
            f"gap: {round(d['gap'], 2)}"
        )


# =========================
# MAIN
# =========================

def run():

    print("=== MARKETBEAT FULL PIPELINE ===")

    # SCRAPE
    upgrades_html = fetch_page_selenium(URLS["UPGRADES"])
    downgrades_html = fetch_page_selenium(URLS["DOWNGRADES"])

    # PARSE
    upgrades_raw = parse_raw_table(upgrades_html)
    downgrades_raw = parse_raw_table(downgrades_html)

    print(f"\nRaw upgrades: {len(upgrades_raw)}")
    print(f"Raw downgrades: {len(downgrades_raw)}")

    # CLEAN
    upgrades = clean_rows(upgrades_raw)
    downgrades = clean_rows(downgrades_raw)

    # SORT
    upgrades_sorted = sort_upgrades(upgrades)
    downgrades_sorted = sort_downgrades(downgrades)

    # DISPLAY
    display(upgrades_sorted, "UPGRADES (SORTED)")
    display(downgrades_sorted, "DOWNGRADES (SORTED)")


if __name__ == "__main__":
    run()
