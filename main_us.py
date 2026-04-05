import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# 1. Récupérer articles
# -----------------------------
def get_articles(limit=15):
    url = "https://fr.investing.com/news/analyst-ratings"

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    ul = soup.find("ul", {"data-test": "news-list"})

    if not ul:
        print("Liste articles non trouvée")
        return []

    articles = []

    for li in ul.find_all("li"):
        a = li.find("a")

        if not a:
            continue

        href = a.get("href")

        # IMPORTANT : déjà un lien complet
        if href and href.startswith("http"):
            articles.append(href)

    # enlever doublons proprement
    articles = list(dict.fromkeys(articles))

    return articles[:limit]


# -----------------------------
# 2. Récupérer 1er paragraphe
# -----------------------------
def get_first_paragraph(url):
    try:
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        # premier paragraphe réel
        paragraphs = soup.find_all("p")

        for p in paragraphs:
            text = p.get_text().strip()

            if len(text) > 50:  # filtre anti bruit
                return text

    except:
        return None

    return None


# -----------------------------
# 3. MAIN
# -----------------------------
def run():
    print("=== RUN US ===")

    articles = get_articles(limit=15)

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
