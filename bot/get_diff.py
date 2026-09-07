"""
get_diff.py
Ce module est responsable de récupérer le "diff" (les lignes de code changées)
d'une pull request GitHub, en utilisant l'API GitHub.
"""

import os
import requests


def get_pr_diff(repo: str, pr_number: str, github_token: str) -> str:
    """
    Récupère le diff complet d'une pull request GitHub.

    Args:
        repo: le nom du repo au format "utilisateur/nom-du-repo"
        pr_number: le numéro de la pull request (ex: "12")
        github_token: le token d'authentification GitHub

    Returns:
        Le diff sous forme de texte brut (format .diff / .patch)
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    headers = {
        "Authorization": f"Bearer {github_token}",
        # Ce header spécial dit à GitHub : "renvoie-moi le diff, pas du JSON"
        "Accept": "application/vnd.github.v3.diff",
    }

    response = requests.get(url, headers=headers)

    # Si la requête échoue (mauvais token, mauvais repo, etc.), on veut le savoir tout de suite
    response.raise_for_status()

    return response.text


if __name__ == "__main__":
    # Ce bloc sert uniquement à tester le script tout seul, en local,
    # avant de l'intégrer dans le pipeline complet.
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    diff = get_pr_diff(repo, pr_number, token)
    print(diff)