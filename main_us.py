import requests
from bs4 import BeautifulSoup

def run():
    print("RUN US")

    url = "https://www.investing.com/news/stock-market-news"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "/news/" in href:
            links.append("https://www.investing.com" + href)

    links = list(set(links))[:10]

    texts = []

    for link in links:
        try:
            r = requests.get(link, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")

            p = soup.find("p")
            if p:
                texts.append(p.get_text())
        except:
            continue

    combined = "\n\n".join(texts)

    print(combined[:1000])

if __name__ == "__main__":
    run()
