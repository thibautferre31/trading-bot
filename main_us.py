from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import time

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

        # attendre que la page charge
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # scroll pour déclencher le chargement JS
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        tables = soup.find_all("table")
        print(f"Tables trouvées : {len(tables)}")

        if not tables:
            print("⚠️ Aucune table trouvée → debug.html généré")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return []

        table = find_best_table(soup)

        if not table:
            print("⚠️ Aucune table exploitable trouvée")
            return []

        tbody = table.find("tbody")
        if not tbody:
            print("⚠️ Pas de tbody trouvé")
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

    text += "\n"
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

    # éviter erreur SMTP 421
    time.sleep(5)

    send_email(subject, body)

    print("Email envoyé ✅")


if __name__ == "__main__":
    run()
