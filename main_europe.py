from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import random
import re
import json
from urllib.parse import urljoin

from ai import analyze_trades
from email_utils import send_email


BASE_URL = "https://www.zonebourse.com"
HOME_URL = "https://www.zonebourse.com/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


def create_driver(user_agent=None):
    if user_agent is None:
        user_agent = random.choice(USER_AGENTS)

    options = Options()
    options.page_load_strategy = "eager"
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


def has_all_classes(tag, needed_classes):
    classes = tag.get("class", [])
    return all(cls in classes for cls in needed_classes)


def get_main_article():
    driver = create_driver()

    try:
        ok = load_page_with_retry(driver, HOME_URL, retries=2, min_sleep=4, max_sleep=7)
        if not ok:
            print("Impossible de charger la homepage Zonebourse")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        target_div = soup.find(
            lambda tag: tag.name == "div" and has_all_classes(
                tag,
                ["c-12", "cm-8", "mb-m-15", "pos-1", "pos-m-2"]
            )
        )

        if not target_div:
            print("Div principale introuvable")
            print(driver.page_source[:5000])
            return None

        a_tag = target_div.find("a", href=True)
        if not a_tag:
            print("Lien article introuvable dans la div principale")
            return None

        href = a_tag["href"].strip()
        title = a_tag.get_text(" ", strip=True)
        article_url = urljoin(BASE_URL, href)

        print("Article principal trouvé :")
        print("Titre :", title)
        print("URL :", article_url)

        return {
            "title": title,
            "url": article_url
        }

    finally:
        driver.quit()


def extract_recommendations(article_url):
    driver = create_driver()

    try:
        ok = load_page_with_retry(driver, article_url, retries=2, min_sleep=5, max_sleep=8)
        if not ok:
            print("Impossible de charger l'article Zonebourse")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        target_u = None
        for u in soup.find_all("u"):
            txt = u.get_text(" ", strip=True).lower()
            if "les principaux changements de recommandations" in txt:
                target_u = u
                break

        if target_u is None:
            print("Titre de section recommandations introuvable")
            print(driver.page_source[:5000])
            return None

        current = target_u
        ul = None

        while current:
            current = current.find_next()
            if current is None:
                break

            if getattr(current, "name", None) == "ul":
                ul = current
                break

            if getattr(current, "name", None) == "p":
                break

        if ul is None:
            print("Liste <ul> introuvable après la section recommandations")
            return None

        items = ul.find_all("li")
        recommendations = []

        for li in items:
            txt = li.get_text(" ", strip=True)
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                recommendations.append(txt)

        if not recommendations:
            print("Aucune recommandation trouvée dans la liste")
            return None

        print(f"Nombre de recommandations extraites : {len(recommendations)}")
        return recommendations

    finally:
        driver.quit()


def build_ai_input(title, article_url, recommendations):
    blocks = []
    for i, reco in enumerate(recommendations, 1):
        block = (
            f"ARTICLE {i}\n"
            f"TITRE: {title}\n"
            f"URL: {article_url}\n"
            f"PARAGRAPHE: {reco}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def run():
    print("=== RUN EUROPE ===")

    article = get_main_article()
    if not article:
        print("Erreur récupération article principal")
        return

    recommendations = extract_recommendations(article["url"])
    if not recommendations:
        print("Erreur recommandations")
        return

    print("\n=== RECOMMANDATIONS EXTRAITES ===\n")
    for i, reco in enumerate(recommendations, 1):
        print(f"[{i}] {reco}")

    ai_input = build_ai_input(article["title"], article["url"], recommendations)

    print("\n=== ANALYSE IA ===\n")
    result = analyze_trades(ai_input, market="EUROPE")

    formatted_result = json.dumps(result, ensure_ascii=False, indent=2)
    print(formatted_result)

    subject = "Trading Bot Europe - Analyse IA"
    body = f"Résultat de l'analyse IA :\n\n{formatted_result}"

    send_email(subject, body)


if __name__ == "__main__":
    run()
