"""
analyze.py
Ce module envoie le diff d'une PR à l'IA (Groq / Llama 3.3) et récupère
une analyse structurée : qualité du code, risques, tests manquants.
"""

from groq import Groq

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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Voici le diff à analyser :\n\n{diff}"},
        ],
        temperature=0.3,  # basse température = réponses plus stables et factuelles
        max_tokens=500,
    )

    return response.choices[0].message.content


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