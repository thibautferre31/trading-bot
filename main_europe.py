import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# 1. Récupérer le titre ivoox
# -----------------------------
def get_chronique_title():
    url = "https://www.ivoox.com/en/podcast-chronique-finance_sq_f11172576_1.html"

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    h3 = soup.find("h3")

    if h3:
        title = h3.get_text().strip()
        print("Titre ivoox :", title)
        return title

    return None


# -----------------------------
# 2. Trouver article Zonebourse
# -----------------------------
def find_zonebourse_article(title):
    url = "https://www.zonebourse.com/actualite-bourse/"

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table", {"id": "newsScreener"})

    if not table:
        print("Table non trouvée")
        return None

    tbody = table.find("tbody")

    if not tbody:
        print("tbody non trouvé")
        return None

    best_link = None
    best_score = 0

    from difflib import SequenceMatcher

    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    for tr in tbody.find_all("tr"):
        a_tag = tr.find("a")

        if not a_tag:
            continue

        text = a_tag.get_text().strip()
        href = a_tag.get("href")

        if not text or not href:
            continue

        score = similar(title.lower(), text.lower())

        if score > best_score:
            best_score = score
            best_link = href

    if best_link and best_score > 0.4:
        full_url = "https://www.zonebourse.com" + best_link
        print(f"Article trouvé (score {best_score:.2f}) :", full_url)
        return full_url

    print("Aucun article trouvé")
    return None


# -----------------------------
# 3. Extraire recommandations
# -----------------------------
def extract_recommendations(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    # trouver tous les <u>
    for u in soup.find_all("u"):
        if "changements de recommandations" in u.get_text().lower():

            ul = u.find_next("ul")

            if ul:
                items = ul.find_all("li")
                texts = [li.get_text().strip() for li in items]

                return "\n".join(texts)

    print("Section recommandations non trouvée")
    return None


# -----------------------------
# 4. MAIN
# -----------------------------
def run():
    print("=== RUN EUROPE ===")

    title = get_chronique_title()
    if not title:
        print("Erreur titre")
        return

    article_url = find_zonebourse_article(title)
    if not article_url:
        print("Erreur article")
        return

    reco = extract_recommendations(article_url)
    if not reco:
        print("Erreur recommandations")
        return

    print("\n=== RECOMMANDATIONS ===\n")
    print(reco)


if __name__ == "__main__":
    run()
