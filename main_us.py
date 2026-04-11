import requests
from bs4 import BeautifulSoup
import time

from email_utils import send_email


URLS = {
    "UPGRADES": "https://www.marketbeat.com/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/ratings/downgrades/"
}


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.marketbeat.com/",
    "Connection": "keep-alive",
}


def fetch_page(url):
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.marketbeat.com/"
    })

    # hit homepage first (important)
    session.get("https://www.marketbeat.com/")

    response = session.get(url, timeout=30)

    if response.status_code != 200:
        print(f"Erreur HTTP : {response.status_code}")
        return None

    return response.text


def parse_table(html):
    soup = BeautifulSoup(html, "lxml")

    # même logique que ton gars → flexible
    table = soup.find("table", {"class": "scroll-table"}) or soup.find("table")

    if not table:
        print("❌ Table introuvable")
        return []

    print("✓ Table trouvée")

    rows_data = []

    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")

    for row in rows:
        cells = row.find_all("td")

        if len(cells) < 3:
            continue

        row_text = [td.get_text(" ", strip=True) for td in cells]

        rows_data.append(row_text)

    print(f"✓ {len(rows_data)} lignes extraites")

    return rows_data


def format_table(rows, title):
    if not rows:
        return f"{title} : Aucun résultat\n\n"

    text = f"=== {title} ===\n\n"

    for row in rows[:50]:  # limite pour email
        text += " | ".join(row) + "\n"

    text += "\n"
    return text


def run():
    print("=== MARKETBEAT SCRAPER (REQUESTS) ===")

    upgrades_html = fetch_page(URLS["UPGRADES"])
    downgrades_html = fetch_page(URLS["DOWNGRADES"])

    if not upgrades_html or not downgrades_html:
        print("❌ Impossible de récupérer les pages")
        return

    upgrades = parse_table(upgrades_html)
    downgrades = parse_table(downgrades_html)

    body = ""
    body += format_table(upgrades, "UPGRADES")
    body += format_table(downgrades, "DOWNGRADES")
    print(body)

if __name__ == "__main__":
    run()
