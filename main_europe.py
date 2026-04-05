import requests
from bs4 import BeautifulSoup

def run():
    print("RUN EUROPE")

    url = "https://www.zonebourse.com/actualite-bourse/"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text()

    start = text.find("Les principaux changements de recommandations")

    if start == -1:
        print("Section non trouvée")
        return

    section = text[start:start+2000]

    print(section)

if __name__ == "__main__":
    run()
