import requests
import json

API_URLS = {
    "UPGRADES": "https://www.marketbeat.com/api/ratings/upgrades/",
    "DOWNGRADES": "https://www.marketbeat.com/api/ratings/downgrades/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.marketbeat.com/"
}


def fetch_api(url):
    try:
        print(f"Appel API : {url}")
        response = requests.get(url, headers=HEADERS, timeout=20)

        print(f"Status code : {response.status_code}")

        if response.status_code != 200:
            print("❌ Erreur API")
            print(response.text[:500])  # debug
            return []

        data = response.json()

        # debug JSON complet si besoin
        with open("debug_api.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data.get("data", [])

    except Exception as e:
        print(f"Erreur : {e}")
        return []


def display_rows(rows, title):
    print(f"\n=== {title} ===\n")

    if not rows:
        print("Aucun résultat\n")
        return

    for row in rows[:20]:  # limite pour affichage
        company = row.get("company", "")
        rating = row.get("rating", "")
        price_target = row.get("price_target", "")
        analyst = row.get("analyst", "")

        print(f"{company} | {rating} | {price_target} | {analyst}")

    print("\n")


def run():
    print("=== MARKETBEAT API TEST ===")

    upgrades = fetch_api(API_URLS["UPGRADES"])
    downgrades = fetch_api(API_URLS["DOWNGRADES"])

    print(f"\nUpgrades récupérés : {len(upgrades)}")
    print(f"Downgrades récupérés : {len(downgrades)}")

    display_rows(upgrades, "UPGRADES")
    display_rows(downgrades, "DOWNGRADES")


if __name__ == "__main__":
    run()
