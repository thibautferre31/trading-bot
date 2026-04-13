from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from email_utils import send_email

URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


def fetch_page_selenium(url):
    print(f"\nLoading: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)

        # IMPORTANT : laisser le JS charger
        print("Waiting page load...")
        time.sleep(6)

        # scroll pour déclencher lazy load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source

        return html

    finally:
        driver.quit()


def parse_marketbeat_table(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")

    if not table:
        print("❌ Table introuvable")
        return []

    tbody = table.find("tbody")

    if not tbody:
        print("❌ tbody introuvable")
        return []

    rows_data = []

    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")

        if len(cols) < 3:
            continue

        row = [c.get_text(" ", strip=True) for c in cols]

        rows_data.append(row)

    return rows_data


def display(rows, title):
    print(f"\n=== {title} ===\n")

    if not rows:
        print("Aucune donnée")
        return

    for r in rows[:30]:
        print(" | ".join(r))

def format_section(title, rows, max_rows=10):
    text = f"\n=== {title} ===\n\n"

    if not rows:
        return text + "Aucune donnée\n"

    for r in rows[:max_rows]:
        text += " | ".join(r) + "\n"

    return text

def run():
    print("=== MARKETBEAT SCRAPER (SELENIUM ADAPTED) ===")

    upgrades_html = fetch_page_selenium(URLS["UPGRADES"])
    downgrades_html = fetch_page_selenium(URLS["DOWNGRADES"])

    upgrades = parse_marketbeat_table(upgrades_html)
    downgrades = parse_marketbeat_table(downgrades_html)

    print(f"\nUpgrades: {len(upgrades)} lignes")
    print(f"Downgrades: {len(downgrades)} lignes")

    display(upgrades, "UPGRADES")
    display(downgrades, "DOWNGRADES")

    subject = "Trading Bot US - Analyse"

    body = ""
    body += format_section("UPGRADES", upgrades)
    body += "\n"
    body += format_section("DOWNGRADES", downgrades)
    
    send_email(subject, body)

if __name__ == "__main__":
    run()
