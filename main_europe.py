import time
import random
from difflib import SequenceMatcher

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from ai import analyze_trades


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
# 2. Similarité
# -----------------------------
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


# -----------------------------
# 3. Trouver article Zonebourse
# -----------------------------
def find_zonebourse_article(title):
    url = "https://www.zonebourse.com/actualite-bourse/"
    html = load_page_with_selenium(url, label="zonebourse liste", wait_range=(4, 6))

    if not html:
        print("Impossible de charger la page liste Zonebourse")
        return None

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "newsScreener"})
    if not table:
        print("Table newsScreener non trouvée")
        return None

    tbody = table.find("tbody")
    if not tbody:
        print("tbody non trouvé")
        return None

    best_link = None
    best_score = 0
    best_text = None

    for tr in tbody.find_all("tr"):
        a_tag = tr.find("a")
        if not a_tag:
            continue

        text = a_tag.get_text(strip=True)
        href = a_tag.get("href")

        if not text or not href:
            continue

        score = similar(title.lower(), text.lower())

        if score > best_score:
            best_score = score
            best_link = href
            best_text = text

    if best_link and best_score > 0.4:
        full_url = "https://www.zonebourse.com" + best_link
        print(f"Meilleur match Zonebourse (score {best_score:.2f}) : {best_text}")
        print("URL :", full_url)
        return full_url

    print("Aucun article Zonebourse trouvé")
    return None


# -----------------------------
# 4. Extraire recommandations
# -----------------------------
def extract_recommendations(article_url):
    html = load_page_with_selenium(article_url, label="article zonebourse", wait_range=(4, 6))

    if not html:
        print("Impossible de charger l'article Zonebourse")
        return None

    soup = BeautifulSoup(html, "html.parser")

    for u in soup.find_all("u"):
        text = u.get_text(" ", strip=True).lower()

        if "changements de recommandations" in text:
            ul = u.find_next("ul")

            if ul:
                items = ul.find_all("li")
                recos = []

                for li in items:
                    txt = li.get_text(" ", strip=True)
                    if txt:
                        recos.append(txt)

                if recos:
                    return recos

    print("Section recommandations non trouvée")
    return None


# -----------------------------
# 5. MAIN
# -----------------------------
def run():
    print("=== RUN EUROPE ===")

    title = get_chronique_title()
    if not title:
        print("Erreur titre")
        return

    article_url = find_zonebourse_article(title)
    if not article_url:
        print("Erreur article Zonebourse")
        return

    recommendations = extract_recommendations(article_url)
    if not recommendations:
        print("Erreur recommandations")
        return

    print("\n=== RECOMMANDATIONS ===")
    for i, reco in enumerate(recommendations, start=1):
        print(f"[{i}] {reco}")

    text_for_ai = "\n".join(recommendations)

    print("\n=== ANALYSE IA ===")
    trades = analyze_trades(text_for_ai)
    print(trades)


if __name__ == "__main__":
    run()
