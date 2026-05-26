import json
import pytest
from pathlib import Path

from leetpush.models import Problem, SolutionsIndex, Submission
from leetpush.store import load_index, save_index


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    return tmp_path


def _sample_index() -> SolutionsIndex:
    sub = Submission(language="python3", filename="solution.py", solved_at="2026-05-20T08:00:00Z", submission_id="1")
    problem = Problem(
        id=1, title="Two Sum", slug="two-sum", difficulty="Easy",
        topics=["Array", "Hash Table"],
        url="https://leetcode.com/problems/two-sum/",
        folder="solutions/array/easy/0001-two-sum",
        submissions=[sub],
    )
    idx = SolutionsIndex.empty()
    idx.upsert_problem(problem)
    return idx


def test_round_trip(tmp_repo: Path) -> None:
    original = _sample_index()
    original.stats = {"total": 42, "easy": 10, "medium": 20, "hard": 12}
    save_index(tmp_repo, original)

    loaded = load_index(tmp_repo)
    assert loaded.total == 42          # stats take precedence over len(problems)
    assert loaded.stats["easy"] == 10
    p = loaded.get_problem("two-sum")
    assert p is not None
    assert p.title == "Two Sum"
    assert len(p.submissions) == 1
    assert p.submissions[0].language == "python3"


def test_load_missing_returns_empty(tmp_repo: Path) -> None:
    idx = load_index(tmp_repo)
    assert idx.total == 0


def test_json_is_readable(tmp_repo: Path) -> None:
    save_index(tmp_repo, _sample_index())
    raw = json.loads((tmp_repo / "solutions.json").read_text())
    assert raw["version"] == "1"
    assert len(raw["problems"]) == 1


def test_upsert_merges_submissions(tmp_repo: Path) -> None:
    idx = _sample_index()
    # Add a second language for the same problem
    cpp_sub = Submission(language="cpp", filename="solution.cpp", solved_at="2026-05-21T10:00:00Z", submission_id="2")
    p = idx.get_problem("two-sum")
    p.upsert_submission(cpp_sub)
    save_index(tmp_repo, idx)

    loaded = load_index(tmp_repo)
    p2 = loaded.get_problem("two-sum")
    assert len(p2.submissions) == 2
    assert {s.language for s in p2.submissions} == {"python3", "cpp"}


def test_upsert_replaces_same_language(tmp_repo: Path) -> None:
    idx = _sample_index()
    new_sub = Submission(language="python3", filename="solution.py", solved_at="2026-05-25T00:00:00Z", submission_id="99")
    p = idx.get_problem("two-sum")
    p.upsert_submission(new_sub)
    assert len(p.submissions) == 1
    assert p.submissions[0].submission_id == "99"
