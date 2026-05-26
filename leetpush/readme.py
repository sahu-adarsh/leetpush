from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .heatmap import compute_streaks
from .models import Problem, SolutionsIndex

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    def bar(count: int, total: int, width: int = 20) -> str:
        if total == 0:
            return "`" + " " * width + "`"
        filled = round(count / total * width)
        return "`" + "█" * filled + "░" * (width - filled) + "`"

    def strdate(iso: str) -> str:
        """'2026-05-25T10:30:00Z' → '2026-05-25'"""
        return iso[:10] if iso else ""

    env.globals["bar"] = bar
    env.filters["strdate"] = strdate

    return env


_env = _make_env()


def generate_root_readme(index: SolutionsIndex) -> str:
    current_streak, longest_streak = compute_streaks(index)
    tmpl = _env.get_template("root_readme.md.j2")
    return tmpl.render(
        index=index,
        by_diff=index.by_difficulty,
        by_topic=index.by_topic,
        recent=index.recent,
        current_streak=current_streak,
        longest_streak=longest_streak,
    )


def generate_problem_readme(problem: Problem) -> str:
    tmpl = _env.get_template("problem_readme.md.j2")
    return tmpl.render(problem=problem)
