from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from .models import SolutionsIndex

# ---------------------------------------------------------------------------
# Geometry constants
# ---------------------------------------------------------------------------

CELL = 10
GAP = 3
STEP = CELL + GAP   # 13px per cell

MARGIN_LEFT = 28    # space for Mon/Wed/Fri labels
MARGIN_TOP = 18     # space for month labels
LEGEND_HEIGHT = 22  # space below grid for legend

# ---------------------------------------------------------------------------
# Color levels — GitHub contribution graph palette
# ---------------------------------------------------------------------------

# 0 = empty, 1 = 1 submission, 2 = 2-3, 3 = 4-6, 4 = 7+
_LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
_DARK  = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def _level(count: int) -> int:
    if count == 0: return 0
    if count == 1: return 1
    if count <= 3: return 2
    if count <= 6: return 3
    return 4


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _build_counts(index: SolutionsIndex) -> dict[date, int]:
    """Map each calendar date to the number of submissions on that day."""
    counts: dict[date, int] = defaultdict(int)
    for problem in index.problems:
        for sub in problem.submissions:
            d = date.fromisoformat(sub.solved_at[:10])
            counts[d] += 1
    return dict(counts)


def compute_streaks(index: SolutionsIndex, today: Optional[date] = None) -> tuple[int, int]:
    """Return (current_streak, longest_streak) in days.

    Current streak: consecutive days ending today (or yesterday if today is empty).
    Longest streak: longest consecutive run ever.
    """
    today = today or date.today()
    counts = _build_counts(index)

    if not counts:
        return 0, 0

    # Current streak — walk backwards from today
    cur = 0
    d = today
    if counts.get(d, 0) == 0:
        d -= timedelta(days=1)  # allow gap for today not yet solved
    while counts.get(d, 0) > 0:
        cur += 1
        d -= timedelta(days=1)

    # Longest streak — scan sorted date list for consecutive runs
    all_dates = sorted(counts.keys())
    best = 1
    run = 1
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i - 1]).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1

    return cur, best


# ---------------------------------------------------------------------------
# SVG generator
# ---------------------------------------------------------------------------

def _css() -> str:
    rules = []
    for lvl in range(5):
        rules.append(f".lv{lvl}{{fill:{_LIGHT[lvl]}}}")
        rules.append(f"@media(prefers-color-scheme:dark){{.lv{lvl}{{fill:{_DARK[lvl]}}}}}")
    return "<style>" + "".join(rules) + "rect{shape-rendering:crispEdges}</style>"


def _month_labels(cols: list[list[tuple[date, int]]]) -> str:
    parts = []
    prev = None
    for col_idx, week in enumerate(cols):
        first = week[0][0]
        if first.month != prev:
            x = MARGIN_LEFT + col_idx * STEP
            parts.append(
                f'<text x="{x}" y="{MARGIN_TOP - 5}" '
                f'font-size="9" font-family="sans-serif" fill="#767676">'
                f'{first.strftime("%b")}</text>'
            )
            prev = first.month
    return "".join(parts)


def _day_labels() -> str:
    parts = []
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = MARGIN_TOP + row * STEP + CELL - 1
        parts.append(
            f'<text x="0" y="{y}" font-size="9" font-family="sans-serif" fill="#767676">{label}</text>'
        )
    return "".join(parts)


def _cells(cols: list[list[tuple[date, int]]], today: date) -> str:
    parts = []
    for col_idx, week in enumerate(cols):
        x = MARGIN_LEFT + col_idx * STEP
        for row_idx, (d, count) in enumerate(week):
            if d > today:
                continue
            y = MARGIN_TOP + row_idx * STEP
            lvl = _level(count)
            tip = f"{d.isoformat()}: {count} submission{'s' if count != 1 else ''}"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" class="lv{lvl}"><title>{tip}</title></rect>'
            )
    return "".join(parts)


def _legend(width: int) -> str:
    y = MARGIN_TOP + 7 * STEP + 8
    # Right-align the legend
    block_w = 5 * (CELL + 2)
    label_less = 24
    label_more = 28
    total_w = label_less + 4 + block_w + 4 + label_more
    x0 = width - 10 - total_w

    parts = [
        f'<text x="{x0}" y="{y + CELL - 1}" font-size="9" font-family="sans-serif" fill="#767676">Less</text>'
    ]
    for lvl in range(5):
        lx = x0 + label_less + 4 + lvl * (CELL + 2)
        parts.append(f'<rect x="{lx}" y="{y}" width="{CELL}" height="{CELL}" rx="2" class="lv{lvl}"/>')
    x_more = x0 + label_less + 4 + 5 * (CELL + 2) + 2
    parts.append(
        f'<text x="{x_more}" y="{y + CELL - 1}" font-size="9" font-family="sans-serif" fill="#767676">More</text>'
    )
    return "".join(parts)


def generate_heatmap_svg(index: SolutionsIndex, today: Optional[date] = None) -> str:
    today = today or date.today()
    counts = _build_counts(index)

    # Start on the Sunday of the week 52 weeks ago
    start = today - timedelta(weeks=52)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # roll back to Sunday

    # Build week columns (Sun..Sat)
    cols: list[list[tuple[date, int]]] = []
    cur = start
    while cur <= today:
        week = [(cur + timedelta(days=d), counts.get(cur + timedelta(days=d), 0)) for d in range(7)]
        cols.append(week)
        cur += timedelta(weeks=1)

    num_weeks = len(cols)
    width = MARGIN_LEFT + num_weeks * STEP + 10
    height = MARGIN_TOP + 7 * STEP + LEGEND_HEIGHT

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  {_css()}\n'
        f'  {_month_labels(cols)}\n'
        f'  {_day_labels()}\n'
        f'  {_cells(cols, today)}\n'
        f'  {_legend(width)}\n'
        f'</svg>\n'
    )
