from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE_URL = "https://fr.investing.com"


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    return driver


def get_articles(driver, limit=None):
    url = "https://fr.investing.com/news/analyst-ratings"
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    ul = soup.find("ul", {"data-test": "news-list"})
    if not ul:
        print("Liste articles non trouvée")
        print(driver.page_source[:3000])
        return []

    articles = []
    for li in ul.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue

        href = a["href"].strip()
        full_url = urljoin(BASE_URL, href)
        articles.append(full_url)

    articles = list(dict.fromkeys(articles))

    if limit is not None:
        return articles[:limit]
    return articles


def get_first_paragraph(driver, url):
    try:
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                return text

    except Exception as e:
        print(f"Erreur sur {url}: {e}")
        return None

    return None


def run():
    print("=== RUN US ===")
    driver = create_driver()

    try:
        articles = get_articles(driver, limit=5)
        print(f"{len(articles)} articles trouvés")

        texts = []
        for article in articles:
            print("Article :", article)
            text = get_first_paragraph(driver, article)
            if text:
                texts.append(text)

        combined = "\n\n".join(texts)

        print("\n=== CONTENU ===\n")
        print(combined[:2000])

    finally:
        driver.quit()


if __name__ == "__main__":
    run()
