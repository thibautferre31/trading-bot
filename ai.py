import requests
import json
import os

API_KEY = os.getenv("ROUTE_LLM_API_KEY")
URL = "https://routellm.abacus.ai/v1/chat/completions"

def analyze_trades(text, market="US"):
    payload = {
        "model": "gpt-5",
        "messages": [
            {
                "role": "user",
                "content": f"""
Tu es un trader intraday expert.
Contexte : marché {market}
Voici des informations récentes : {text}
Ta mission :
1. Analyse le contexte global (macro, géopolitique, sentiment)
2. Identifie les opportunités intéressantes
3. Ignore le bruit
Donne uniquement les 3 meilleurs trades au format JSON :
[
{{
"stock": "...",
"direction": "LONG ou SHORT",
"confidence": 1-5,
"reason": "explication courte"
}}
]
"""
            }
        ],
        "stream": False
    }

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    response = requests.post(URL, headers=headers, data=json.dumps(payload))
    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except:
        return str(data)
