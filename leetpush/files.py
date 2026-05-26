from __future__ import annotations

import re
from pathlib import Path

from .models import Problem, Submission, SolutionsIndex

# ---------------------------------------------------------------------------
# Language → file extension
# ---------------------------------------------------------------------------

_LANG_EXT: dict[str, str] = {
    "python": "py",
    "python3": "py",
    "cpp": "cpp",
    "c": "c",
    "java": "java",
    "javascript": "js",
    "typescript": "ts",
    "golang": "go",
    "rust": "rs",
    "csharp": "cs",
    "kotlin": "kt",
    "swift": "swift",
    "scala": "scala",
    "ruby": "rb",
    "php": "php",
    "racket": "rkt",
    "erlang": "erl",
    "elixir": "ex",
    "dart": "dart",
    "bash": "sh",
    "mysql": "sql",
    "mssql": "sql",
    "oraclesql": "sql",
    "pandas": "pandas.py",  # avoids collision with python3
}


def language_filename(lang: str) -> str:
    ext = _LANG_EXT.get(lang.lower(), lang.lower())
    return f"solution.{ext}"


# ---------------------------------------------------------------------------
# Folder path derivation
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """'Dynamic Programming' → 'dynamic-programming'"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


def problem_folder(problem_id: int, slug: str, difficulty: str, topics: list[str]) -> str:
    """Derive the relative folder path from problem metadata.

    Pattern: solutions/<primary-topic>/<difficulty>/<id:04d>-<slug>
    """
    primary_topic = _slugify(topics[0]) if topics else "uncategorized"
    diff = difficulty.lower()
    return f"solutions/{primary_topic}/{diff}/{problem_id:04d}-{slug}"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def write_solution(repo_root: Path, problem: Problem, submission: Submission, code: str) -> Path:
    """Write code to the correct location and return the file path."""
    folder = repo_root / problem.folder
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / submission.filename
    target.write_text(code, encoding="utf-8")
    return target


def write_problem_readme(repo_root: Path, problem: Problem, content: str) -> Path:
    path = repo_root / problem.folder / "README.md"
    # Preserve existing user notes in the Approach section
    if path.exists():
        content = _preserve_approach(path.read_text(encoding="utf-8"), content)
    path.write_text(content, encoding="utf-8")
    return path


def write_root_readme(repo_root: Path, content: str) -> Path:
    path = repo_root / "README.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Note preservation
# ---------------------------------------------------------------------------

_APPROACH_RE = re.compile(
    r"(## Approach\s*\n)(.*?)(\n## |\Z)",
    re.DOTALL,
)


def _preserve_approach(old: str, new: str) -> str:
    """Copy the user's Approach notes from old README into the newly generated one."""
    old_match = _APPROACH_RE.search(old)
    if not old_match:
        return new

    user_notes = old_match.group(2).strip()
    if not user_notes or user_notes.startswith("<!--"):
        return new

    def _inject(m: re.Match) -> str:
        return f"{m.group(1)}\n{user_notes}\n{m.group(3)}"

    return _APPROACH_RE.sub(_inject, new, count=1)


# ---------------------------------------------------------------------------
# Sync orchestration helper
# ---------------------------------------------------------------------------

def build_problem_from_api(meta: dict) -> Problem:
    """Construct a Problem from raw LeetCode API metadata (no submissions)."""
    problem_id = int(meta["questionId"])
    slug = meta["titleSlug"]
    topics = [t["name"] for t in meta.get("topicTags", [])]
    folder = problem_folder(problem_id, slug, meta["difficulty"], topics)
    return Problem(
        id=problem_id,
        title=meta["title"],
        slug=slug,
        difficulty=meta["difficulty"],
        topics=topics,
        url=f"https://leetcode.com/problems/{slug}/",
        folder=folder,
    )


def build_submission_from_api(sub_id: str, lang: str, detail: dict, timestamp: str) -> Submission:
    """Construct a Submission from raw API detail + submission list entry."""
    from datetime import datetime, timezone

    solved_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return Submission(
        language=lang,
        filename=language_filename(lang),
        solved_at=solved_at,
        submission_id=sub_id,
        runtime_ms=detail.get("runtime_ms"),
        memory_mb=detail.get("memory_mb"),
    )


def deduplicate_submissions(raw: list[dict]) -> list[dict]:
    """From a flat list of AC submissions, keep the most recent per (slug, lang) pair."""
    seen: dict[tuple[str, str], dict] = {}
    for s in raw:
        key = (s["titleSlug"], s["lang"])
        if key not in seen or int(s["timestamp"]) > int(seen[key]["timestamp"]):
            seen[key] = s
    return list(seen.values())
