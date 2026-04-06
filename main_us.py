import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://fr.investing.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# 1. Récupérer articles (tous ceux de la page)
# -----------------------------
def get_articles(limit=None):
    url = "https://fr.investing.com/news/analyst-ratings"

    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    ul = soup.find("ul", {"data-test": "news-list"})
    if not ul:
        print("Liste articles non trouvée")
        return []

    articles = []
    for li in ul.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue

        href = a["href"].strip()
        full_url = urljoin(BASE_URL, href)  # gère href relatifs ou absolus
        articles.append(full_url)

    # enlever doublons proprement en gardant l'ordre
    articles = list(dict.fromkeys(articles))

    if limit is not None:
        return articles[:limit]
    return articles


# -----------------------------
# 2. Récupérer 1er paragraphe (sans filtre 50 caractères)
# -----------------------------
def get_first_paragraph(url):
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:  # premier paragraphe non vide
                return text

    except Exception:
        return None

    return None


# -----------------------------
# 3. MAIN
# -----------------------------
def run():
    print("=== RUN US ===")

    articles = get_articles(limit=None)  # tous les liens de la page
    print(f"{len(articles)} articles trouvés")

    texts = []
    for article in articles:
        text = get_first_paragraph(article)
        if text:
            texts.append(text)

    combined = "\n\n".join(texts)

    print("\n=== CONTENU ===\n")
    print(combined[:2000])


if __name__ == "__main__":
    run()
