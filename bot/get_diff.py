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


def get_changed_files(diff: str) -> list[str]:
    """
    Extrait la liste des noms de fichiers modifiés dans un diff, à partir
    des lignes "diff --git a/... b/...".
    """
    return [
        line.split(" b/")[-1]
        for line in diff.splitlines()
        if line.startswith("diff --git ")
    ]


def diff_has_code_changes(diff: str) -> bool:
    """
    Vérifie si un diff contient au moins un fichier de code modifié
    (par opposition à des fichiers purement documentaires ou de config).

    Args:
        diff: le diff au format texte brut

    Returns:
        True s'il y a au moins un fichier de code parmi les changements.
    """
    for filename in get_changed_files(diff):
        _, ext = os.path.splitext(filename)
        if ext.lower() not in NON_CODE_EXTENSIONS:
            return True

    return False


# Correspondance extension -> nom de langage lisible, utilisée pour adapter
# le prompt envoyé à l'IA (ex: mentionner les conventions Python vs JS).
EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
    ".sh": "Shell",
    ".html": "HTML",
    ".css": "CSS",
}


def detect_languages(diff: str) -> list[str]:
    """
    Détecte les langages de programmation présents dans un diff, à partir
    des extensions des fichiers modifiés.

    Args:
        diff: le diff au format texte brut

    Returns:
        Liste des noms de langages détectés, triée par nombre de fichiers
        décroissant (le langage principal en premier). Liste vide si aucun
        langage connu n'est reconnu.
    """
    language_counts: dict[str, int] = {}

    for filename in get_changed_files(diff):
        _, ext = os.path.splitext(filename)
        language = EXTENSION_TO_LANGUAGE.get(ext.lower())
        if language:
            language_counts[language] = language_counts.get(language, 0) + 1

    return sorted(language_counts, key=language_counts.get, reverse=True)


if __name__ == "__main__":
    # Ce bloc sert uniquement à tester le script tout seul, en local,
    # avant de l'intégrer dans le pipeline complet.
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    diff = get_pr_diff(repo, pr_number, token)
    print(diff)