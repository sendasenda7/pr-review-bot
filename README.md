# PR Review Bot 🤖

[![PR Review Bot](https://github.com/sendasenda7/pr-review-bot/actions/workflows/review.yml/badge.svg)](https://github.com/sendasenda7/pr-review-bot/actions/workflows/review.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)

An AI-powered GitHub bot that automatically reviews pull requests. It analyzes the code diff using an LLM (Groq / Llama & GPT-OSS models) and posts a structured review comment directly on the PR — summary, potential issues, and missing tests — within seconds of the PR being opened or updated.

## Why this project

Code review is essential but time-consuming, and human reviewers aren't always available right away. This bot provides an **instant first-pass review** so developers get immediate feedback before a human even looks at the PR — similar to commercial tools like CodeRabbit or Sourcery, built from scratch to understand the full CI/CD + AI integration pipeline.

## How it works

```
PR opened / updated
        ↓
GitHub Actions triggers the workflow
        ↓
Fetch the PR diff via the GitHub API
        ↓
Send the diff to Groq (LLM) with a structured review prompt
        ↓
Post the AI's analysis as a comment on the PR via the GitHub API
```

## Example output

> ### Quality score: 8/10 ★★★★★★★★☆☆
>
> **Summary**
> This change updates the AI model used in `analyze_diff` and adds a small `demo.py` file with two utility functions.
>
> **Points of attention**
> - `divide` does not guard against division by zero
> - `get_user` does not handle out-of-range indices
>
> **Missing tests**
> - Test `divide` with `b = 0`
> - Test `get_user` with an out-of-range index

## Features

- **Structured AI output** — the LLM returns strict JSON (quality score, summary, concerns, missing tests), parsed and rendered into consistent Markdown
- **Language-aware review** — detects the programming language(s) touched by the diff and tailors the analysis to their conventions
- **No duplicate comments** — updates the existing review comment on new commits instead of piling up new ones
- **Skips non-code diffs** — doc-only or config-only changes (README, lockfiles, etc.) don't trigger an AI call
- **Resilient to API errors** — retries with exponential backoff on transient Groq errors, and posts a clear fallback message if the analysis ultimately fails

## Tech stack

- **Python** — core logic
- **GitHub Actions** — CI/CD trigger, runs on every `pull_request` event
- **GitHub REST API** — fetching diffs and posting comments
- **Groq API** (`openai/gpt-oss-120b`, JSON mode) — LLM-powered code analysis

## Project structure

```
pr-review-bot/
├── .github/workflows/review.yml   # GitHub Actions workflow
├── bot/
│   ├── get_diff.py                # Fetches the PR diff from GitHub
│   ├── analyze.py                 # Sends the diff to the LLM for analysis
│   └── post_comment.py            # Posts the review as a PR comment
├── main.py                        # Orchestrates the full pipeline
└── requirements.txt
```

## Setup

1. **Fork or clone this repo.**

2. **Add a Groq API secret.**
   Go to `Settings → Secrets and variables → Actions → New repository secret`
   - Name: `GROQ_API_KEY`
   - Value: your [Groq API key](https://console.groq.com)

3. **That's it.** The workflow triggers automatically on every pull request — no extra configuration needed. `GITHUB_TOKEN` is provided automatically by GitHub Actions.

## Running locally (optional)

```bash
pip install -r requirements.txt

export GITHUB_REPOSITORY="owner/repo"
export PR_NUMBER="1"
export GITHUB_TOKEN="your_github_token"
export GROQ_API_KEY="your_groq_api_key"

python main.py
```

## Possible improvements

- Configurable review rules via a `.pr-review-bot.yml` file in the target repo
- Inline comments on specific lines instead of a single summary comment
- Support for a local pre-commit hook to preview the review before opening the PR

## License

MIT