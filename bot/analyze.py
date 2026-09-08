"""
analyze.py
Ce module envoie le diff d'une PR à l'IA (Groq / Llama 3.3) et récupère
une analyse structurée : qualité du code, risques, tests manquants.
"""

import time

from groq import Groq, APIStatusError, APIConnectionError, APITimeoutError


class AnalysisError(Exception):
    """Erreur métier levée quand l'analyse IA échoue de façon définitive,
    après épuisement des tentatives de retry."""
    pass

# Le "prompt système" définit le rôle et le comportement attendu de l'IA.
# On lui donne des instructions précises pour avoir une réponse utile et courte.
SYSTEM_PROMPT = """Tu es un assistant de revue de code expérimenté.
Tu analyses des diffs de pull requests et tu donnes un avis concis et utile.

Ta réponse doit être structurée en 3 parties, en français, au format Markdown :

## Résumé
Une phrase sur ce que fait ce changement.

## Points d'attention
Une liste à puces des problèmes potentiels (bugs, mauvaises pratiques,
risques de sécurité ou de performance). Si tout semble correct, dis-le.

## Tests manquants
Une liste à puces des cas de test qui semblent manquants, s'il y en a.

Reste concis : maximum 150 mots au total. Ne réécris pas le code, donne
uniquement ton analyse.
"""


def analyze_diff(diff: str, api_key: str) -> str:
    """
    Envoie un diff de code à l'IA Groq et retourne son analyse.

    Args:
        diff: le diff de la pull request (texte brut)
        api_key: la clé API Groq

    Returns:
        L'analyse de l'IA sous forme de texte Markdown
    """
    client = Groq(api_key=api_key)

    # Un diff peut être très long. On le tronque pour éviter de dépasser
    # les limites de taille de contexte du modèle et pour rester rapide.
    max_chars = 12000
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n\n[... diff tronqué, trop long ...]"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Voici le diff à analyser :\n\n{diff}"},
    ]

    # On tente jusqu'à 3 fois en cas d'erreur temporaire (rate limit, timeout,
    # petit souci réseau côté Groq), avec une pause croissante entre chaque essai.
    # C'est ce qu'on appelle un "backoff exponentiel" : 2s, puis 4s, puis 8s.
    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.3,  # basse température = réponses plus stables et factuelles
                max_tokens=500,
            )
            return response.choices[0].message.content

        except (APIStatusError, APIConnectionError, APITimeoutError) as error:
            last_error = error
            is_last_attempt = attempt == max_attempts

            # Une erreur 4xx autre que le rate limit (429) est probablement
            # une erreur de configuration (clé invalide, modèle inexistant...) :
            # réessayer ne sert à rien, on arrête tout de suite.
            status_code = getattr(error, "status_code", None)
            if status_code and 400 <= status_code < 500 and status_code != 429:
                raise AnalysisError(
                    f"Erreur de configuration Groq (code {status_code}) : {error}"
                ) from error

            if is_last_attempt:
                break

            wait_seconds = 2 ** attempt
            print(f"Tentative {attempt} échouée ({error}), nouvel essai dans {wait_seconds}s...")
            time.sleep(wait_seconds)

    raise AnalysisError(
        f"L'analyse IA a échoué après {max_attempts} tentatives : {last_error}"
    ) from last_error


if __name__ == "__main__":
    # Test rapide en local avec un faux diff
    import os

    fake_diff = """
diff --git a/app.py b/app.py
index e69de29..b6fc4c6 100644
--- a/app.py
+++ b/app.py
@@ -0,0 +1,5 @@
+def divide(a, b):
+    return a / b
+
+result = divide(10, 0)
+print(result)
"""
    api_key = os.environ.get("GROQ_API_KEY")
    analysis = analyze_diff(fake_diff, api_key)
    print(analysis)