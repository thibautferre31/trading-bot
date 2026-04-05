import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

HEADERS = {"User-Agent": "Mozilla/5.0"}

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

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_zonebourse_article(title):
    url = "https://www.zonebourse.com/actualite-bourse/"

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a")

    best_match = None
    best_score = 0

    for link in links:
        text = link.get_text().strip()
        href = link.get("href", "")

        if not text or not href:
            continue

        score = similar(title.lower(), text.lower())

        if score > best_score:
            best_score = score
            best_match = href

    if best_match and best_score > 0.4:
        full_url = "https://www.zonebourse.com" + best_match
        print(f"Article trouvé (score {best_score:.2f}) :", full_url)
        return full_url

    print("Aucun article pertinent trouvé")
    return None
    
def extract_recommendations(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text()

    start = text.find("Les principaux changements de recommandations")

    if start == -1:
        print("Section non trouvée")
        return None

    section = text[start:start + 4000]
    return section

def run():
    print("=== RUN EUROPE ===")

    title = get_chronique_title()
    if not title:
        print("Erreur : titre non récupéré")
        return

    article_url = find_zonebourse_article(title)
    if not article_url:
        print("Erreur : article non trouvé")
        return

    section = extract_recommendations(article_url)
    if not section:
        print("Erreur : section non trouvée")
        return

    print("\n=== SECTION EXTRAITE ===\n")
    print(section[:2000])


if __name__ == "__main__":
    run()
