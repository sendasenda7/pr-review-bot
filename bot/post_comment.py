"""
post_comment.py
Ce module poste un commentaire sur une pull request GitHub, contenant
l'analyse générée par l'IA.
"""

import requests


def post_pr_comment(repo: str, pr_number: str, comment_body: str, github_token: str) -> None:
    """
    Poste un commentaire sur une pull request GitHub.

    Args:
        repo: le nom du repo au format "utilisateur/nom-du-repo"
        pr_number: le numéro de la pull request (ex: "12")
        comment_body: le texte du commentaire (peut contenir du Markdown)
        github_token: le token d'authentification GitHub
    """
    # Fun fact : une PR est techniquement une "issue" côté API GitHub pour
    # tout ce qui concerne les commentaires. D'où l'URL "issues/{pr_number}/comments".
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    # On ajoute une petite signature en bas du commentaire pour que ce soit
    # clair que c'est un bot qui a écrit ça, pas un humain.
    footer = "\n\n---\n*Analyse générée automatiquement par PR Review Bot 🤖*"
    payload = {"body": comment_body + footer}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    print(f"Commentaire posté avec succès sur la PR #{pr_number}")


if __name__ == "__main__":
    import os

    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    post_pr_comment(repo, pr_number, "Ceci est un test de commentaire.", token)