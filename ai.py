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
- donner un score de confiance entre 0 et 100 (100 = conviction très forte)
- donner une raison courte
- recopier le titre source
- recopier le paragraphe source utilisé

Tu dois raisonner non seulement à partir du contenu fourni, mais aussi en tenant compte du contexte actuel :
- contexte macroéconomique
- contexte de marché
- contexte géopolitique
- dynamique sectorielle de l'entreprise concernée
- sensibilité potentielle du secteur aux événements actuels

Exemples de raisonnement attendus :
- une recommandation positive sur une compagnie aérienne peut être affaiblie par un contexte géopolitique tendu, une hausse du pétrole, ou une aversion au risque
- une recommandation negative sur une valeur du petrole peut être renforcée par un contexte mondial incertain du a la guerre ou autre

Le champ "reason" doit être précis et détaillé.
Il doit expliquer :
1. ce que dit l'article ou la recommandation
2. pourquoi cela est bullish, bearish ou neutral
3. comment le contexte actuel du marché, du monde et du secteur influence l'interprétation
4. pourquoi le score de confiance est élevé ou faible

Le champ "reason" doit faire au minimum 2 phrases complètes si un cas exploitable est trouvé.

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
- Si aucun bloc exploitable n'est trouvé, retourne []
- Le champ paragraph doit contenir exactement le texte source correspondant
- Le champ title doit contenir exactement le titre source correspondant
- Le champ reason doit être concret, spécifique et relié au contenu source
- N'utilise pas de formules vagues comme "contexte mitigé" sans expliquer pourquoi
- Si le contexte sectoriel ou macro réduit la qualité du signal, baisse la confiance
- Si le contexte sectoriel ou macro renforce le signal, augmente la confiance
- N'invente pas de ticker précis si tu n'es pas sûr
- Ne fais pas semblant d'avoir une donnée en temps réel ultra précise non fournie ; utilise une compréhension générale et actuelle du contexte macro, géopolitique, sectoriel et boursier

Voici les contenus :
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
        
        results = json.loads(cleaned)

        for item in results:
            raw_conf = item.get("confidence", 0)
        
            try:
                conf = float(raw_conf)
            except:
                conf = 0
        
            # Si l'IA renvoie encore un score entre 0 et 1, on le convertit en 0-100
            if 0 <= conf <= 1:
                conf = conf * 100
        
            conf = int(round(conf))
            conf = max(0, min(100, conf))
            item["confidence"] = conf
        
        results = sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)
        
        return results

    except Exception as e:
        print(f"Erreur API : {e}")
        return []
