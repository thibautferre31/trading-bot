from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import random
import re
import json
import unicodedata

from ai import analyze_trades
from email_utils import send_email


IVOX_URL = "https://www.ivoox.com/en/podcast-chronique-finance_sq_f11172576_1.html"
ZONEBOURSE_AUTHOR_URL = "https://www.zonebourse.com/auteur/anthony-bondain"
BASE_URL = "https://www.zonebourse.com"

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


def slugify_title(title):
    text = title.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def get_chronique_title():
    driver = create_driver()

    try:
        ok = load_page_with_retry(driver, IVOX_URL, retries=2, min_sleep=4, max_sleep=7)
        if not ok:
            print("Impossible de charger la page Ivoox")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")
        h3 = soup.find("h3")

        if not h3:
            print("Titre Ivoox introuvable")
            print(driver.page_source[:3000])
            return None

        title = h3.get_text(" ", strip=True)
        print("Titre Ivoox :", title)
        return title

    finally:
        driver.quit()


def find_zonebourse_article_by_slug(title):
    slug = slugify_title(title)
    print("Slug recherché :", slug)

    driver = create_driver()

    try:
        ok = load_page_with_retry(driver, ZONEBOURSE_AUTHOR_URL, retries=2, min_sleep=4, max_sleep=7)
        if not ok:
            print("Impossible de charger la page auteur Zonebourse")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        all_grids = soup.find_all("div", class_="grid")
        print(f"Nombre de div.grid trouvées : {len(all_grids)}")

        target_grid = None

        for idx, grid in enumerate(all_grids, start=1):
            cards = grid.find_all(
                "div",
                class_=lambda c: c and all(cls in c.split() for cls in ["c-12", "cs-6", "cxxl-4", "mb-15"])
            )
            print(f"Grid #{idx} -> {len(cards)} cards potentielles")

            if cards:
                target_grid = grid
                break

        if target_grid is None:
            print("Aucune grid contenant des cards d'articles trouvée")
            print(driver.page_source[:5000])
            return None

        cards = target_grid.find_all(
            "div",
            class_=lambda c: c and all(cls in c.split() for cls in ["c-12", "cs-6", "cxxl-4", "mb-15"])
        )

        print(f"Nombre de cards trouvées dans la bonne grid : {len(cards)}")

        for i, card in enumerate(cards, start=1):
            a_tag = card.find("a", href=True)
            if not a_tag:
                continue

            href = a_tag["href"].strip()
            text = a_tag.get_text(" ", strip=True)

            print(f"[{i}] href = {href}")
            if text:
                print(f"    texte = {text}")

            if "/actualite-bourse/" in href and slug in href:
                full_url = BASE_URL + href
                print("Article trouvé :", full_url)
                return full_url

        print("Aucun article correspondant au slug n'a été trouvé")
        return None

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

    title = get_chronique_title()
    if not title:
        print("Erreur titre")
        return

    article_url = find_zonebourse_article_by_slug(title)
    if not article_url:
        print("Erreur article Zonebourse")
        return

    recommendations = extract_recommendations(article_url)
    if not recommendations:
        print("Erreur recommandations")
        return

    print("\n=== RECOMMANDATIONS EXTRAITES ===\n")
    for i, reco in enumerate(recommendations, 1):
        print(f"[{i}] {reco}")

    ai_input = build_ai_input(title, article_url, recommendations)

    print("\n=== ANALYSE IA ===\n")
    result = analyze_trades(ai_input, market="EUROPE")

    formatted_result = json.dumps(result, ensure_ascii=False, indent=2)
    print(formatted_result)

    subject = "Trading Bot Europe - Analyse IA"
    body = f"Résultat de l'analyse IA :\n\n{formatted_result}"

    send_email(subject, body)


if __name__ == "__main__":
    run()
