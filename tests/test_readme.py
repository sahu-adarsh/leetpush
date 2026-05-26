from leetpush.models import Problem, Submission, SolutionsIndex
from leetpush.readme import generate_problem_readme, generate_root_readme


def _make_index() -> SolutionsIndex:
    idx = SolutionsIndex.empty()

    for problem_id, title, slug, diff, topics, lang, solved_at, rt, mem in [
        (1,   "Two Sum",            "two-sum",            "Easy",   ["Array"],                 "python3", "2026-05-20T08:00:00Z", 52,   17.6),
        (322, "Coin Change",        "coin-change",        "Medium", ["Dynamic Programming"],   "python3", "2026-05-22T10:00:00Z", 1243, 14.3),
        (23,  "Merge k Sorted Lists","merge-k-sorted-lists","Hard", ["Linked List"],           "java",    "2026-05-23T14:00:00Z", 3,    44.2),
    ]:
        sub = Submission(language=lang, filename=f"solution.{lang[:2]}", solved_at=solved_at,
                         submission_id=str(problem_id), runtime_ms=rt, memory_mb=mem)
        p = Problem(id=problem_id, title=title, slug=slug, difficulty=diff, topics=topics,
                    url=f"https://leetcode.com/problems/{slug}/",
                    folder=f"solutions/{topics[0].lower()}/{diff.lower()}/{problem_id:04d}-{slug}",
                    submissions=[sub])
        idx.upsert_problem(p)

    return idx


def test_root_readme_contains_stats() -> None:
    idx = _make_index()
    out = generate_root_readme(idx)
    assert "solved-3" in out
    assert "easy-1" in out
    assert "medium-1" in out
    assert "hard-1" in out


def test_root_readme_contains_problems() -> None:
    out = generate_root_readme(_make_index())
    assert "Two Sum" in out
    assert "Coin Change" in out
    assert "Merge k Sorted Lists" in out


def test_root_readme_topic_table() -> None:
    out = generate_root_readme(_make_index())
    assert "Dynamic Programming" in out
    assert "Linked List" in out


def test_problem_readme_basic() -> None:
    idx = _make_index()
    p = idx.get_problem("coin-change")
    out = generate_problem_readme(p)
    assert "322. Coin Change" in out
    assert "Medium" in out
    assert "1243 ms" in out
    assert "14.3 MB" in out


def test_problem_readme_multi_lang() -> None:
    sub2 = Submission(language="cpp", filename="solution.cpp", solved_at="2026-05-24T00:00:00Z",
                      submission_id="999", runtime_ms=7, memory_mb=10.2)
    idx = _make_index()
    p = idx.get_problem("two-sum")
    p.upsert_submission(sub2)

    out = generate_problem_readme(p)
    assert "python3" in out
    assert "cpp" in out


def test_problem_readme_null_runtime() -> None:
    sub = Submission(language="python3", filename="solution.py", solved_at="2026-05-20T00:00:00Z",
                     submission_id="1", runtime_ms=None, memory_mb=None)
    p = Problem(id=1, title="Two Sum", slug="two-sum", difficulty="Easy",
                topics=["Array"], url="https://leetcode.com/problems/two-sum/",
                folder="solutions/array/easy/0001-two-sum", submissions=[sub])
    out = generate_problem_readme(p)
    assert "N/A" in out
