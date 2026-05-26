import pytest
from pathlib import Path

from leetpush.files import (
    deduplicate_submissions,
    language_filename,
    problem_folder,
    write_problem_readme,
    write_solution,
    _preserve_approach,
)
from leetpush.models import Problem, Submission


# ---------------------------------------------------------------------------
# language_filename
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang,expected", [
    ("python3", "solution.py"),
    ("python", "solution.py"),
    ("cpp", "solution.cpp"),
    ("java", "solution.java"),
    ("javascript", "solution.js"),
    ("golang", "solution.go"),
    ("pandas", "solution.pandas.py"),
])
def test_language_filename(lang: str, expected: str) -> None:
    assert language_filename(lang) == expected


# ---------------------------------------------------------------------------
# problem_folder
# ---------------------------------------------------------------------------

def test_problem_folder_basic() -> None:
    assert problem_folder(1, "two-sum", "Easy", ["Array"]) == "solutions/array/easy/0001-two-sum"


def test_problem_folder_primary_topic() -> None:
    folder = problem_folder(322, "coin-change", "Medium", ["Dynamic Programming", "BFS"])
    assert folder == "solutions/dynamic-programming/medium/0322-coin-change"


def test_problem_folder_no_topics() -> None:
    folder = problem_folder(1, "two-sum", "Easy", [])
    assert "uncategorized" in folder


def test_problem_folder_zero_pads_id() -> None:
    folder = problem_folder(42, "trapping-rain-water", "Hard", ["Array"])
    assert "0042-trapping-rain-water" in folder


# ---------------------------------------------------------------------------
# write_solution
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    return tmp_path


def _make_problem() -> Problem:
    return Problem(
        id=1, title="Two Sum", slug="two-sum", difficulty="Easy",
        topics=["Array"], url="https://leetcode.com/problems/two-sum/",
        folder="solutions/array/easy/0001-two-sum",
        submissions=[],
    )


def test_write_solution_creates_file(tmp_repo: Path) -> None:
    problem = _make_problem()
    sub = Submission(language="python3", filename="solution.py", solved_at="2026-05-20T00:00:00Z", submission_id="1")
    path = write_solution(tmp_repo, problem, sub, "def twoSum(): pass")
    assert path.exists()
    assert path.read_text() == "def twoSum(): pass"


def test_write_solution_multi_lang(tmp_repo: Path) -> None:
    problem = _make_problem()
    py_sub = Submission(language="python3", filename="solution.py", solved_at="2026-05-20T00:00:00Z", submission_id="1")
    cpp_sub = Submission(language="cpp", filename="solution.cpp", solved_at="2026-05-21T00:00:00Z", submission_id="2")
    write_solution(tmp_repo, problem, py_sub, "# py")
    write_solution(tmp_repo, problem, cpp_sub, "// cpp")

    folder = tmp_repo / problem.folder
    assert (folder / "solution.py").exists()
    assert (folder / "solution.cpp").exists()


# ---------------------------------------------------------------------------
# _preserve_approach
# ---------------------------------------------------------------------------

def test_preserve_approach_keeps_user_notes() -> None:
    old = "# Title\n\n## Approach\n\nMy custom notes here.\n\n## Complexity\n- Time: O(n)\n"
    new = "# Title\n\n## Approach\n\n<!-- Add your notes here -->\n\n## Complexity\n- Time:\n"
    result = _preserve_approach(old, new)
    assert "My custom notes here." in result


def test_preserve_approach_skips_placeholder() -> None:
    old = "# Title\n\n## Approach\n\n<!-- Add your notes here -->\n\n## Complexity\n"
    new = "# Title\n\n## Approach\n\n<!-- Add your notes here -->\n\n## Complexity\n"
    result = _preserve_approach(old, new)
    assert result == new


# ---------------------------------------------------------------------------
# deduplicate_submissions
# ---------------------------------------------------------------------------

def test_deduplicate_keeps_latest() -> None:
    raw = [
        {"id": "1", "titleSlug": "two-sum", "lang": "python3", "timestamp": "1000"},
        {"id": "2", "titleSlug": "two-sum", "lang": "python3", "timestamp": "2000"},
    ]
    result = deduplicate_submissions(raw)
    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_deduplicate_keeps_different_langs() -> None:
    raw = [
        {"id": "1", "titleSlug": "two-sum", "lang": "python3", "timestamp": "1000"},
        {"id": "2", "titleSlug": "two-sum", "lang": "cpp", "timestamp": "2000"},
    ]
    result = deduplicate_submissions(raw)
    assert len(result) == 2
