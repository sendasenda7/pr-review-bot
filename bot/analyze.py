"""
analyze.py
Ce module envoie le diff d'une PR à l'IA (Groq) et récupère une analyse
structurée : score de qualité, résumé, points d'attention, tests manquants.

L'IA répond en JSON strict (via response_format), ce qui garantit un format
toujours cohérent, plutôt que de dépendre d'un Markdown libre qui pourrait
varier d'une réponse à l'autre.
"""

import json
import time

from groq import Groq, APIStatusError, APIConnectionError, APITimeoutError


class AnalysisError(Exception):
    """Erreur métier levée quand l'analyse IA échoue de façon définitive,
    après épuisement des tentatives de retry."""
    pass


# Le "prompt système" définit le rôle et le format de sortie attendu de l'IA.
SYSTEM_PROMPT = """Tu es un assistant de revue de code expérimenté.
Tu analyses des diffs de pull requests et tu donnes un avis concis et utile, en français.

Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte autour, avec exactement ces clés :

{
  "score": <entier de 0 à 10, la qualité globale du changement>,
  "summary": "<une phrase sur ce que fait ce changement>",
  "concerns": ["<point d'attention 1>", "<point d'attention 2>", ...],
  "missing_tests": ["<test manquant 1>", "<test manquant 2>", ...]
}

Règles :
- "concerns" : liste des problèmes potentiels (bugs, mauvaises pratiques, risques
  de sécurité ou de performance). Liste vide si tout semble correct.
- "missing_tests" : liste des cas de test qui semblent manquants. Liste vide si aucun.
- Le score reflète la qualité du code, pas la longueur du changement.
- Reste concis dans chaque texte. Ne réécris pas le code.
"""


def analyze_diff(diff: str, api_key: str) -> dict:
    """
    Envoie un diff de code à l'IA Groq et retourne son analyse structurée.

    Args:
        diff: le diff de la pull request (texte brut)
        api_key: la clé API Groq

    Returns:
        Un dict avec les clés : score (int), summary (str),
        concerns (list[str]), missing_tests (list[str])
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

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                # Force l'IA à répondre en JSON valide, plutôt que du texte libre
                # qu'on devrait parser à l'aveugle.
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content
            return _parse_analysis(raw_content)

        except (APIStatusError, APIConnectionError, APITimeoutError) as error:
            last_error = error
            is_last_attempt = attempt == max_attempts

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


def _parse_analysis(raw_content: str) -> dict:
    """
    Parse et valide le JSON renvoyé par l'IA, avec des valeurs de repli
    si un champ manque ou si le JSON est malformé.
    """
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise AnalysisError(f"L'IA n'a pas renvoyé un JSON valide : {error}") from error

    score = data.get("score")
    if not isinstance(score, int) or not (0 <= score <= 10):
        score = None  # on affichera "N/A" plutôt qu'un chiffre inventé

    return {
        "score": score,
        "summary": data.get("summary", "Résumé non disponible."),
        "concerns": data.get("concerns") or [],
        "missing_tests": data.get("missing_tests") or [],
    }


def format_analysis_as_markdown(analysis: dict) -> str:
    """
    Construit le commentaire Markdown final à partir de l'analyse structurée.
    Fait de manière indépendante du JSON renvoyé par l'IA : le format est
    toujours identique, ce qui rend le rendu sur GitHub prévisible.
    """
    score = analysis["score"]
    score_display = f"{score}/10" if score is not None else "N/A"
    # Petite barre visuelle simple avec des étoiles pleines/vides, purement
    # esthétique, pour repérer le score en un coup d'œil.
    if score is not None:
        stars = "★" * score + "☆" * (10 - score)
    else:
        stars = ""

    lines = [f"### Score de qualité : {score_display} {stars}", ""]
    lines.append("## Résumé")
    lines.append(analysis["summary"])
    lines.append("")

    lines.append("## Points d'attention")
    if analysis["concerns"]:
        lines.extend(f"- {item}" for item in analysis["concerns"])
    else:
        lines.append("Aucun problème détecté.")
    lines.append("")

    lines.append("## Tests manquants")
    if analysis["missing_tests"]:
        lines.extend(f"- {item}" for item in analysis["missing_tests"])
    else:
        lines.append("Aucun test manquant identifié.")

    return "\n".join(lines)


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
    result = analyze_diff(fake_diff, api_key)
    print(format_analysis_as_markdown(result))