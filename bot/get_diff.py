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


# Extensions considérées comme "non-code" : les modifier ne justifie pas
# un appel à l'IA (documentation, données, dépendances verrouillées...).
NON_CODE_EXTENSIONS = {
    ".md", ".txt", ".rst",
    ".json", ".lock", ".yml", ".yaml",
    ".gitignore", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".csv", ".log",
}


def diff_has_code_changes(diff: str) -> bool:
    """
    Vérifie si un diff contient au moins un fichier de code modifié
    (par opposition à des fichiers purement documentaires ou de config).

    On se base sur les lignes "diff --git a/... b/..." qui indiquent le
    début de chaque fichier changé dans le diff.

    Args:
        diff: le diff au format texte brut

    Returns:
        True s'il y a au moins un fichier de code parmi les changements.
    """
    changed_files = [
        line.split(" b/")[-1]
        for line in diff.splitlines()
        if line.startswith("diff --git ")
    ]

    for filename in changed_files:
        _, ext = os.path.splitext(filename)
        if ext.lower() not in NON_CODE_EXTENSIONS:
            return True

    return False


if __name__ == "__main__":
    # Ce bloc sert uniquement à tester le script tout seul, en local,
    # avant de l'intégrer dans le pipeline complet.
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    diff = get_pr_diff(repo, pr_number, token)
    print(diff)