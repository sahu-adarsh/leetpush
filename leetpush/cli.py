from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from .api import LeetCodeClient, MockLeetCodeClient
from .files import (
    build_problem_from_api,
    build_submission_from_api,
    deduplicate_submissions,
    write_problem_readme,
    write_root_readme,
    write_solution,
)
from .models import SolutionsIndex
from .readme import generate_problem_readme, generate_root_readme
from .store import load_index, save_index


def _get_api(mock: bool, session: str | None):
    if mock:
        return MockLeetCodeClient()
    if not session:
        session = os.environ.get("LEETCODE_SESSION")
    if not session:
        click.echo(
            "Error: no LeetCode session. Set LEETCODE_SESSION env var, "
            "pass --session, or use --mock for a dry run.",
            err=True,
        )
        sys.exit(1)
    return LeetCodeClient(session)


@click.group()
def main() -> None:
    """LeetPush — push your LeetCode solutions to GitHub beautifully."""


@main.command()
@click.option("--mock", is_flag=True, default=False, help="Use mock data (no LeetCode auth needed).")
@click.option("--session", default=None, envvar="LEETCODE_SESSION", help="LeetCode session cookie.")
@click.option("--username", default=None, envvar="LEETCODE_USERNAME", help="LeetCode username.")
@click.option("--limit", default=100, show_default=True, help="Max recent submissions to fetch.")
@click.option("--repo", default=".", show_default=True, help="Path to target solutions repo.")
def sync(mock: bool, session: str | None, username: str | None, limit: int, repo: str) -> None:
    """Fetch recent accepted submissions and push them to the repo."""
    repo_root = Path(repo).resolve()
    api = _get_api(mock, session)

    if not mock and not username:
        username = os.environ.get("LEETCODE_USERNAME") or click.prompt("LeetCode username")

    click.echo("Fetching recent accepted submissions...")
    raw = api.get_recent_ac_submissions(username or "mock_user", limit=limit)
    unique = deduplicate_submissions(raw)
    click.echo(f"  {len(raw)} submissions → {len(unique)} unique (slug, lang) pairs")

    index = load_index(repo_root)
    new_count = 0

    with click.progressbar(unique, label="Syncing") as bar:
        for entry in bar:
            slug = entry["titleSlug"]
            lang = entry["lang"]
            sub_id = entry["id"]
            timestamp = entry["timestamp"]

            # Skip if we already have this exact submission
            existing_problem = index.get_problem(slug)
            if existing_problem:
                existing_sub = existing_problem.get_submission(lang)
                if existing_sub and existing_sub.submission_id == sub_id:
                    continue

            # Fetch code + detail
            detail = api.get_submission_detail(sub_id)

            # Fetch problem metadata if not already in index
            if existing_problem is None:
                meta = api.get_problem_metadata(slug)
                problem = build_problem_from_api(meta)
            else:
                problem = existing_problem

            submission = build_submission_from_api(sub_id, lang, detail, timestamp)
            problem.upsert_submission(submission)

            # Write solution file
            write_solution(repo_root, problem, submission, detail["code"])

            # Write per-problem README
            problem_readme = generate_problem_readme(problem)
            write_problem_readme(repo_root, problem, problem_readme)

            index.upsert_problem(problem)
            new_count += 1

    # Persist index + regenerate root README
    save_index(repo_root, index)
    root_readme = generate_root_readme(index)
    write_root_readme(repo_root, root_readme)

    click.echo(f"\nDone. {new_count} new/updated submission(s). {index.total} problem(s) total.")


@main.command()
@click.option("--repo", default=".", show_default=True, help="Path to target solutions repo.")
def readme(repo: str) -> None:
    """Regenerate README.md from solutions.json (no network calls)."""
    repo_root = Path(repo).resolve()
    index = load_index(repo_root)
    if index.total == 0:
        click.echo("solutions.json is empty — run `lp sync` first.", err=True)
        sys.exit(1)

    content = generate_root_readme(index)
    write_root_readme(repo_root, content)
    click.echo(f"README.md regenerated ({index.total} problems).")


@main.command()
@click.option("--repo", default=".", show_default=True, help="Path to target solutions repo.")
def stats(repo: str) -> None:
    """Print a summary of your solutions to the terminal."""
    repo_root = Path(repo).resolve()
    index = load_index(repo_root)

    if index.total == 0:
        click.echo("No solutions synced yet. Run `lp sync` first.")
        return

    by_diff = index.by_difficulty
    click.echo(f"\nTotal solved : {index.total}")
    click.echo(f"  Easy       : {by_diff['Easy']}")
    click.echo(f"  Medium     : {by_diff['Medium']}")
    click.echo(f"  Hard       : {by_diff['Hard']}")
    click.echo("\nTop topics:")
    for topic, count in list(index.by_topic.items())[:5]:
        click.echo(f"  {topic:<30} {count}")
    click.echo(f"\nLast synced: {index.last_synced}")
