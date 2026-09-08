"""
post_comment.py
Ce module gère les commentaires du bot sur une pull request GitHub :
il cherche si le bot a déjà commenté, et met à jour ce commentaire
au lieu d'en créer un nouveau à chaque push.
"""

import requests

# Ce marqueur invisible (commentaire HTML, non affiché sur GitHub) permet
# de retrouver le commentaire du bot parmi tous les autres commentaires
# de la PR, même des mois plus tard.
BOT_MARKER = "<!-- pr-review-bot-comment -->"

FOOTER = "\n\n---\n*Analyse générée automatiquement par PR Review Bot 🤖*"


def find_existing_comment(repo: str, pr_number: str, github_token: str):
    """
    Cherche si le bot a déjà posté un commentaire sur cette PR.

    Returns:
        L'ID du commentaire existant (int), ou None si aucun n'est trouvé.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    for comment in response.json():
        if BOT_MARKER in comment.get("body", ""):
            return comment["id"]

    return None


def post_pr_comment(repo: str, pr_number: str, comment_body: str, github_token: str) -> None:
    """
    Poste ou met à jour le commentaire de revue sur une pull request GitHub.

    Si le bot a déjà commenté sur cette PR, son commentaire est mis à jour
    (édité) au lieu de créer un doublon.

    Args:
        repo: le nom du repo au format "utilisateur/nom-du-repo"
        pr_number: le numéro de la pull request (ex: "12")
        comment_body: le texte du commentaire (peut contenir du Markdown)
        github_token: le token d'authentification GitHub
    """
    body = BOT_MARKER + "\n" + comment_body + FOOTER

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    existing_comment_id = find_existing_comment(repo, pr_number, github_token)

    if existing_comment_id:
        # PATCH sur un commentaire existant = on le modifie en place
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing_comment_id}"
        response = requests.patch(url, headers=headers, json={"body": body})
        response.raise_for_status()
        print(f"Commentaire existant mis à jour sur la PR #{pr_number}")
    else:
        # POST = on crée un nouveau commentaire (première analyse de cette PR)
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=headers, json={"body": body})
        response.raise_for_status()
        print(f"Nouveau commentaire posté sur la PR #{pr_number}")


if __name__ == "__main__":
    import os

    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    post_pr_comment(repo, pr_number, "Ceci est un test de commentaire.", token)