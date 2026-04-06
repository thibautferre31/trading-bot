from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import random
import re
import json

from ai import analyze_trades

BASE_URL = "https://fr.investing.com"
LIST_URL = "https://fr.investing.com/news/analyst-ratings"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

KEYWORDS = ["relève", "releve", "abaisse", "dégrade", "degrade", "réduit", "reduit"]


def create_driver(user_agent=None):
    if user_agent is None:
        user_agent = random.choice(USER_AGENTS)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={user_agent}")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['fr-FR', 'fr', 'en-US', 'en']
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
            """
        },
    )

    return driver


def load_page_with_retry(driver, url, retries=2, min_sleep=4, max_sleep=7):
    for attempt in range(1, retries + 1):
        try:
            driver.get(url)
            time.sleep(random.uniform(min_sleep, max_sleep))
            return True
        except TimeoutException:
            print(f"Timeout chargement ({attempt}/{retries}) : {url}")
        except WebDriverException as e:
            print(f"WebDriverException ({attempt}/{retries}) sur {url}: {e}")

        if attempt < retries:
            time.sleep(random.uniform(3, 6))

    return False


def title_matches(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in KEYWORDS)


def get_articles(limit=10):
    driver = create_driver()

    try:
        ok = load_page_with_retry(driver, LIST_URL, retries=2, min_sleep=4, max_sleep=7)

        if not ok:
            print("Impossible de charger la page liste des articles")
            return []

        soup = BeautifulSoup(driver.page_source, "html.parser")

        ul = soup.find("ul", {"data-test": "news-list"})
        if not ul:
            print("Liste articles non trouvée")
            print(driver.page_source[:3000])
            return []

        articles = []
        seen_urls = set()

        for li in ul.find_all("li"):
            a = li.find("a", href=True)
            if not a:
                continue

            title = a.get_text(" ", strip=True)
            href = a["href"].strip()
            full_url = urljoin(BASE_URL, href)

            if not title:
                continue

            if full_url in seen_urls:
                continue

            if not title_matches(title):
                continue

            seen_urls.add(full_url)
            articles.append({
                "title": title,
                "url": full_url
            })

            print(f"Article retenu : {title}")
            print(f"URL : {full_url}")

            if len(articles) >= limit:
                break

        return articles

    finally:
        driver.quit()


def extract_first_real_paragraph(html):
    soup = BeautifulSoup(html, "html.parser")

    anti_bot_markers = [
        "security service to protect against malicious bots",
        "verify you are not a bot",
        "press and hold",
        "captcha",
    ]

    full_text = soup.get_text(" ", strip=True).lower()
    for marker in anti_bot_markers:
        if marker in full_text:
            return None

    article_div = soup.find("div", id="article")
    if not article_div:
        print("div#article non trouvée")
        return None

    paragraphs = article_div.find_all("p")

    for p in paragraphs:
        text = p.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,.;:!)])", r"\1", text)
        text = re.sub(r"([(])\s+", r"\1", text)

        if not text:
            continue

        if len(text) < 40:
            continue

        return text

    print("Aucun paragraphe valide trouvé dans div#article")
    return None


def get_first_paragraph(url, retries=2):
    user_agent = random.choice(USER_AGENTS)

    for attempt in range(1, retries + 1):
        driver = create_driver(user_agent=user_agent)

        try:
            print(f"Article : {url}")
            print(f"User-Agent : {user_agent}")
            print(f"Tentative : {attempt}/{retries}")

            time.sleep(random.uniform(2, 5))

            ok = load_page_with_retry(driver, url, retries=1, min_sleep=6, max_sleep=10)
            if not ok:
                print("Chargement article échoué")
                continue

            html = driver.page_source
            text = extract_first_real_paragraph(html)

            if text:
                return text

            print("Anti-bot détecté ou paragraphe introuvable")
            print(html[:2000])

        except Exception as e:
            print(f"Erreur sur {url}: {e}")

        finally:
            driver.quit()

        if attempt < retries:
            time.sleep(random.uniform(3, 6))

    return None


def build_ai_input(items):
    blocks = []
    for i, item in enumerate(items, 1):
        block = (
            f"ARTICLE {i}\n"
            f"TITRE: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"PARAGRAPHE: {item['paragraph']}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def run():
    print("=== RUN US ===")

    articles = get_articles(limit=10)
    print(f"{len(articles)} articles filtrés trouvés")

    if not articles:
        print("Aucun article filtré récupéré, arrêt.")
        return

    collected_items = []

    for i, article_data in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] {article_data['title']}")
        time.sleep(random.uniform(3, 6))

        paragraph = get_first_paragraph(article_data["url"], retries=2)
        if paragraph:
            collected_items.append({
                "title": article_data["title"],
                "url": article_data["url"],
                "paragraph": paragraph
            })

    print("\n=== PARAGRAPHES EXTRAITS ===\n")
    for i, item in enumerate(collected_items, 1):
        print(f"[{i}] {item['title']}")
        print(item["paragraph"])
        print()

    if not collected_items:
        print("Aucun contenu récupéré, analyse IA ignorée.")
        return

    ai_input = build_ai_input(collected_items)

    print("\n=== ANALYSE IA ===\n")
    result = analyze_trades(ai_input, market="US")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
