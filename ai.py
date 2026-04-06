import requests
import json
import os

API_KEY = os.getenv("ROUTE_LLM_API_KEY")
URL = "https://routellm.abacus.ai/v1/chat/completions"

if not API_KEY:
    raise ValueError("❌ ROUTE_LLM_API_KEY manquante")

def analyze_trades(text, market="US"):
    payload = {
        "model": "gpt-5",
        "messages": [
            {
                "role": "user",
                "content": f"""
Tu es un trader intraday expert basé sur :
- flux analystes
- macro économie
- géopolitique
- sentiment de marché

IMPORTANT :
Tu dois d'abord déduire le contexte global des dernières 24-48h à partir de tes connaissances (guerres, banques centrales, pétrole, etc.).

Ensuite, analyse UNIQUEMENT les actions suivantes :

{text}

Pour CHAQUE action, tu dois analyser :

1. Flow analyste :
- upgrade / downgrade
- cohérence ou contradiction récente

2. News du jour :
- type d’annonce
- variation du price target
- surprise vs attentes

3. Momentum :
- tendance récente
- réaction aux news
- intérêt du marché

---

OBJECTIF :

- Tu DOIS traiter TOUTES les actions (aucune omission)
- Tu DOIS classer les trades du MEILLEUR au PIRE
- Le classement est basé sur la probabilité de mouvement intraday

---

FORMAT STRICT (JSON uniquement, trié par confidence décroissante) :

[
  {{
    "stock": "...",
    "direction": "LONG ou SHORT",
    "confidence": 0-10,
    "reason": "max 15 mots"
  }}
]

RÈGLES IMPORTANTES :
- Toutes les actions doivent être présentes
- Le JSON doit être trié du plus fort au plus faible
- Aucun texte en dehors du JSON
"""
            }
        ],
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=180)
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Nettoyage JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return content.strip()

    except Exception as e:
        print("Erreur API :", e)
        return "[]"
