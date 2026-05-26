from datetime import date, timedelta

import pytest

from leetpush.heatmap import (
    _build_counts,
    _level,
    compute_streaks,
    generate_heatmap_svg,
)
from leetpush.models import Problem, SolutionsIndex, Submission


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_index(solved_dates: list[str]) -> SolutionsIndex:
    """One submission per date, all on problem #1."""
    idx = SolutionsIndex.empty()
    for i, d in enumerate(solved_dates):
        sub = Submission(language="python3", filename="solution.py", solved_at=f"{d}T10:00:00Z",
                         submission_id=str(i))
        p = Problem(id=1, title="Two Sum", slug="two-sum", difficulty="Easy", topics=["Array"],
                    url="https://leetcode.com/problems/two-sum/",
                    folder="solutions/array/easy/0001-two-sum",
                    submissions=[sub])
        # We re-create per date to get separate submissions
        sub2 = Submission(language=f"lang{i}", filename=f"solution{i}.py",
                          solved_at=f"{d}T10:00:00Z", submission_id=str(i))
        p2 = Problem(id=i + 100, title=f"P{i}", slug=f"p{i}", difficulty="Easy", topics=["Array"],
                     url=f"https://leetcode.com/problems/p{i}/",
                     folder=f"solutions/array/easy/{i + 100:04d}-p{i}",
                     submissions=[sub2])
        idx.upsert_problem(p2)
    return idx


# ---------------------------------------------------------------------------
# _level
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("count,expected", [
    (0, 0), (1, 1), (2, 2), (3, 2), (4, 3), (6, 3), (7, 4), (100, 4),
])
def test_level(count: int, expected: int) -> None:
    assert _level(count) == expected


# ---------------------------------------------------------------------------
# _build_counts
# ---------------------------------------------------------------------------

def test_build_counts_aggregates_per_day() -> None:
    idx = SolutionsIndex.empty()
    for lang in ["python3", "cpp"]:
        sub = Submission(language=lang, filename=f"solution.{lang}", solved_at="2026-05-20T10:00:00Z",
                         submission_id=lang)
        p = Problem(id=1, title="Two Sum", slug="two-sum", difficulty="Easy", topics=["Array"],
                    url="", folder="solutions/array/easy/0001-two-sum", submissions=[sub])
        idx.upsert_problem(p)  # upserts merge submissions on same slug

    counts = _build_counts(idx)
    assert counts[date(2026, 5, 20)] == 2


def test_build_counts_empty_index() -> None:
    assert _build_counts(SolutionsIndex.empty()) == {}


def test_build_counts_prefers_calendar() -> None:
    idx = SolutionsIndex.empty()
    idx.calendar = {"2026-01-01": 5, "2026-01-02": 3}
    # Even though there are no problems, calendar data should be used
    counts = _build_counts(idx)
    assert counts[date(2026, 1, 1)] == 5
    assert counts[date(2026, 1, 2)] == 3


# ---------------------------------------------------------------------------
# compute_streaks
# ---------------------------------------------------------------------------

def test_streak_consecutive() -> None:
    today = date(2026, 5, 26)
    idx = _make_index(["2026-05-24", "2026-05-25", "2026-05-26"])
    cur, best = compute_streaks(idx, today=today)
    assert cur == 3
    assert best == 3


def test_streak_gap_yesterday_still_counts() -> None:
    """If nothing solved today, streak counts from yesterday."""
    today = date(2026, 5, 26)
    idx = _make_index(["2026-05-23", "2026-05-24", "2026-05-25"])
    cur, best = compute_streaks(idx, today=today)
    assert cur == 3


def test_streak_broken() -> None:
    today = date(2026, 5, 26)
    idx = _make_index(["2026-05-20", "2026-05-21", "2026-05-25", "2026-05-26"])
    cur, best = compute_streaks(idx, today=today)
    assert cur == 2
    assert best == 2


def test_streak_empty_index() -> None:
    cur, best = compute_streaks(SolutionsIndex.empty())
    assert cur == 0
    assert best == 0


def test_longest_streak_non_consecutive() -> None:
    today = date(2026, 5, 26)
    idx = _make_index([
        "2026-05-01", "2026-05-02", "2026-05-03",  # run of 3
        "2026-05-10", "2026-05-11",                 # run of 2
    ])
    _, best = compute_streaks(idx, today=today)
    assert best == 3


# ---------------------------------------------------------------------------
# generate_heatmap_svg
# ---------------------------------------------------------------------------

def test_svg_is_valid_xml() -> None:
    idx = _make_index(["2026-05-20", "2026-05-21"])
    svg = generate_heatmap_svg(idx, today=date(2026, 5, 26))
    assert svg.startswith("<svg ")
    assert "</svg>" in svg


def test_svg_contains_colored_cells() -> None:
    idx = _make_index(["2026-05-20"])
    svg = generate_heatmap_svg(idx, today=date(2026, 5, 26))
    # Level-1 cell should appear (1 submission on that day)
    assert 'class="lv1"' in svg


def test_svg_empty_index_only_empty_cells() -> None:
    svg = generate_heatmap_svg(SolutionsIndex.empty(), today=date(2026, 5, 26))
    assert 'class="lv0"' in svg
    # The legend always renders one rect per level; data cells for an empty
    # index should all be lv0, so each of lv1-4 appears exactly once (legend only).
    for lvl in [1, 2, 3, 4]:
        assert svg.count(f'class="lv{lvl}"') == 1


def test_svg_contains_legend_and_labels() -> None:
    svg = generate_heatmap_svg(SolutionsIndex.empty(), today=date(2026, 5, 26))
    assert "Less" in svg
    assert "More" in svg
    assert "Mon" in svg


def test_svg_no_future_cells() -> None:
    today = date(2026, 5, 26)
    svg = generate_heatmap_svg(SolutionsIndex.empty(), today=today)
    # A date one week from now should not appear in the SVG
    future = (today + timedelta(days=7)).isoformat()
    assert future not in svg


def test_svg_dark_mode_css() -> None:
    svg = generate_heatmap_svg(SolutionsIndex.empty(), today=date(2026, 5, 26))
    assert "prefers-color-scheme:dark" in svg
