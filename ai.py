import os
import json
import requests

API_KEY = os.getenv("ROUTE_LLM_API_KEY")


def analyze_trades(text, market="US"):
    url = "https://routellm.abacus.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"""
Tu analyses des articles d'analystes financiers pour le marché {market}.

Chaque article fourni contient :
- un titre
- une url
- un paragraphe

Ta mission :
- identifier l'action concernée
- identifier le ticker si présent ou clairement déductible
- déterminer si le signal est bullish, bearish ou neutral
- donner un score de confiance entre 0 et 1
- donner une raison courte
- recopier le titre source
- recopier le paragraphe source utilisé

Réponds uniquement en JSON valide.
Retourne une liste JSON.
Chaque élément doit respecter exactement cette structure :

[
  {{
    "ticker": "...",
    "title": "...",
    "paragraph": "...",
    "sentiment": "bullish",
    "confidence": 0.0,
    "reason": "..."
  }}
]

Règles :
- Ne pose jamais de question
- N'ajoute aucun texte hors JSON
- Si le ticker n'est pas certain, mets le nom de l'action ou "UNKNOWN"
- Si aucun article exploitable n'est trouvé, retourne []
- Le champ paragraph doit contenir le paragraphe source correspondant
- Le champ title doit contenir le titre source correspondant

Voici les articles :
{text}
"""

    payload = {
        "model": "route-llm",
        "messages": [
            {
                "role": "system",
                "content": "You are a precise financial analyst. You always return strict valid JSON only."
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }

    try:
        print(f"Taille du texte envoyé à l'IA : {len(text)} caractères")

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        print("Réponse brute IA :")
        print(content)
        
        cleaned = content.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        
        return json.loads(cleaned)

    except Exception as e:
        print(f"Erreur API : {e}")
        return []
