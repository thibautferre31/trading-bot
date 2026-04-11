from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json

from email_utils import send_email

URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    return driver

def find_best_table(soup):
    tables = soup.find_all("table")

    best_table = None
    max_rows = 0

    for table in tables:
        tbody = table.find("tbody")
        if not tbody:
            continue

        rows = tbody.find_all("tr")

        if len(rows) > max_rows:
            max_rows = len(rows)
            best_table = table

    return best_table

def get_table_data(url):
    driver = create_driver()

    try:
        print(f"Chargement : {url}")
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        table = find_best_table(soup)

        if not table:
            print("Aucune table trouvée")
            return []

        tbody = table.find("tbody")
        if not tbody:
            print("tbody non trouvé")
            return []

        rows = []

        for tr in tbody.find_all("tr"):
            cols = tr.find_all("td")
            row = [td.get_text(" ", strip=True) for td in cols]

            if row:
                rows.append(row)

        return rows

    finally:
        driver.quit()

def format_table(rows, title):
    if not rows:
        return f"{title} : Aucun résultat\n\n"

    text = f"=== {title} ===\n\n"

    for row in rows:
        text += " | ".join(row) + "\n"

    text += "\n\n"
    return text


def run():
    print("=== MARKETBEAT SCRAPER ===")

    upgrades = get_table_data(URLS["UPGRADES"])
    downgrades = get_table_data(URLS["DOWNGRADES"])

    print(f"{len(upgrades)} upgrades récupérés")
    print(f"{len(downgrades)} downgrades récupérés")

    body = ""
    body += format_table(upgrades, "UPGRADES")
    body += format_table(downgrades, "DOWNGRADES")

    subject = "MarketBeat - Upgrades & Downgrades"

    send_email(subject, body)

    print("Email envoyé ✅")


if __name__ == "__main__":
    run()
