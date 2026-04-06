import time
import random
import re
import unicodedata

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
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
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    driver.execute_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    )

    return driver


def load_page_with_selenium(url, label="", wait_range=(3, 5)):
    driver = None
    try:
        user_agent = random.choice(USER_AGENTS)
        print(f"Ouverture {label}: {url}")
        print(f"User-Agent : {user_agent}")

        driver = create_driver(user_agent=user_agent)
        driver.get(url)

        time.sleep(random.uniform(*wait_range))
        html = driver.page_source

        if not html or len(html) < 500:
            print(f"HTML trop court pour {label}")
            return None

        return html

    except Exception as e:
        print(f"Erreur Selenium sur {label}: {e}")
        return None

    finally:
        if driver:
            driver.quit()


def slugify_title(title):
    text = title.strip().lower()

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)

    return text.strip("-")


# -----------------------------
# 1. Récupérer le titre ivoox
# -----------------------------
def get_chronique_title():
    url = "https://www.ivoox.com/en/podcast-chronique-finance_sq_f11172576_1.html"
    html = load_page_with_selenium(url, label="ivoox", wait_range=(3, 5))

    if not html:
        print("Impossible de charger ivoox")
        return None

    soup = BeautifulSoup(html, "html.parser")
    h3 = soup.find("h3")

    if h3:
        title = h3.get_text(strip=True)
        print("Titre ivoox :", title)
        return title

    print("Titre ivoox introuvable")
    return None


# -----------------------------
# 2. Trouver l'article Zonebourse via slug
# -----------------------------
def find_zonebourse_article_by_slug(title):
    slug = slugify_title(title)
    print("Slug recherché :", slug)

    url = "https://www.zonebourse.com/auteur/anthony-bondain"
    html = load_page_with_selenium(url, label="zonebourse auteur", wait_range=(4, 6))

    if not html:
        print("Impossible de charger la page auteur Zonebourse")
        return None

    soup = BeautifulSoup(html, "html.parser")

    grid = soup.find("div", class_="grid")
    if not grid:
        print("Div grid introuvable")
        return None

    links = grid.find_all("a", href=True)
    print(f"Nombre de liens trouvés dans grid : {len(links)}")

    candidates = []

    for i, a_tag in enumerate(links, start=1):
        href = a_tag["href"].strip()
        text = a_tag.get_text(" ", strip=True)

        if "/actualite-bourse/" in href:
            full_url = "https://www.zonebourse.com" + href
            candidates.append((href, text, full_url))
            print(f"[{len(candidates)}] href = {href}")
            if text:
                print(f"    texte = {text}")

    print(f"Nombre de liens /actualite-bourse/ trouvés : {len(candidates)}")

    for href, text, full_url in candidates:
        if slug in href:
            print("Article trouvé :", full_url)
            return full_url

    print("Aucun article correspondant au slug n'a été trouvé")
    return None


# -----------------------------
# 3. MAIN TEST
# -----------------------------
def run():
    print("=== RUN EUROPE TEST SLUG ===")

    title = get_chronique_title()
    if not title:
        print("Erreur titre")
        return

    article_url = find_zonebourse_article_by_slug(title)
    if not article_url:
        print("Erreur article")
        return

    print("URL finale article :", article_url)


if __name__ == "__main__":
    run()
