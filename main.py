"""
main.py
Point d'entrée du bot. Orchestre les 3 étapes :
1. Récupérer le diff de la PR
2. L'analyser avec l'IA
3. Poster le résultat en commentaire sur la PR
"""

import os
import sys

from bot.get_diff import get_pr_diff, diff_has_code_changes
from bot.analyze import analyze_diff, format_analysis_as_markdown, AnalysisError
from bot.post_comment import post_pr_comment


def main():
    # Ces variables seront fournies automatiquement par GitHub Actions
    # (on configurera ça dans le fichier .yml juste après).
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    github_token = os.environ.get("GITHUB_TOKEN")
    groq_api_key = os.environ.get("GROQ_API_KEY")

    # On vérifie que rien ne manque avant de commencer, pour avoir une
    # erreur claire plutôt qu'un plantage mystérieux plus loin.
    missing = [
        name
        for name, value in [
            ("GITHUB_REPOSITORY", repo),
            ("PR_NUMBER", pr_number),
            ("GITHUB_TOKEN", github_token),
            ("GROQ_API_KEY", groq_api_key),
        ]
        if not value
    ]
    if missing:
        print(f"Erreur : variables manquantes : {', '.join(missing)}")
        sys.exit(1)

    print(f"Récupération du diff pour {repo} PR #{pr_number}...")
    diff = get_pr_diff(repo, pr_number, github_token)

    if not diff.strip():
        print("Diff vide, rien à analyser.")
        return

    if not diff_has_code_changes(diff):
        print("Aucun fichier de code modifié (doc/config uniquement), analyse ignorée.")
        return

    print("Analyse du diff avec l'IA...")
    try:
        analysis = analyze_diff(diff, groq_api_key)
    except AnalysisError as error:
        # L'IA n'a pas pu répondre après plusieurs tentatives : on prévient
        # quand même les développeurs via un commentaire, plutôt que de
        # faire échouer le workflow en silence.
        print(f"Erreur d'analyse : {error}")
        fallback_message = (
            "⚠️ L'analyse automatique n'a pas pu être générée "
            f"(erreur technique : {error}). Réessayez plus tard ou relancez le workflow."
        )
        post_pr_comment(repo, pr_number, fallback_message, github_token)
        sys.exit(1)

    comment_body = format_analysis_as_markdown(analysis)

    print("Publication du commentaire sur la PR...")
    post_pr_comment(repo, pr_number, comment_body, github_token)

    print("Terminé !")


if __name__ == "__main__":
    main()