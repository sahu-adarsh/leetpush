from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Submission:
    language: str       # "python3", "cpp", "java", etc.
    filename: str       # "solution.py", "solution.cpp"
    solved_at: str      # ISO 8601
    submission_id: str
    runtime_ms: Optional[int] = None
    memory_mb: Optional[float] = None

    @classmethod
    def from_dict(cls, d: dict) -> Submission:
        return cls(
            language=d["language"],
            filename=d["filename"],
            solved_at=d["solved_at"],
            submission_id=d["submission_id"],
            runtime_ms=d.get("runtime_ms"),
            memory_mb=d.get("memory_mb"),
        )


@dataclass
class Problem:
    id: int
    title: str
    slug: str
    difficulty: str     # "Easy" | "Medium" | "Hard"
    topics: list[str]   # primary topic first; folder derived from topics[0]
    url: str
    folder: str         # relative: "solutions/array/easy/0001-two-sum"
    submissions: list[Submission] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> Problem:
        return cls(
            id=d["id"],
            title=d["title"],
            slug=d["slug"],
            difficulty=d["difficulty"],
            topics=d["topics"],
            url=d["url"],
            folder=d["folder"],
            submissions=[Submission.from_dict(s) for s in d.get("submissions", [])],
        )

    def get_submission(self, language: str) -> Optional[Submission]:
        for s in self.submissions:
            if s.language == language:
                return s
        return None

    def upsert_submission(self, sub: Submission) -> None:
        for i, s in enumerate(self.submissions):
            if s.language == sub.language:
                self.submissions[i] = sub
                return
        self.submissions.append(sub)

    @property
    def languages(self) -> list[str]:
        return [s.language for s in self.submissions]


@dataclass
class SolutionsIndex:
    version: str = "1"
    last_synced: str = field(default_factory=_now_iso)
    problems: list[Problem] = field(default_factory=list)
    calendar: dict[str, int] = field(default_factory=dict)  # "YYYY-MM-DD" → submission count
    stats: dict[str, int] = field(default_factory=dict)    # {total, easy, medium, hard} from API
    lc_streak: int = 0                                      # authoritative streak from LeetCode's API

    @classmethod
    def empty(cls) -> SolutionsIndex:
        return cls()

    @classmethod
    def from_dict(cls, d: dict) -> SolutionsIndex:
        return cls(
            version=d.get("version", "1"),
            last_synced=d.get("last_synced", _now_iso()),
            problems=[Problem.from_dict(p) for p in d.get("problems", [])],
            calendar=d.get("calendar", {}),
            stats=d.get("stats", {}),
            lc_streak=d.get("lc_streak", 0),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def get_problem(self, slug: str) -> Optional[Problem]:
        for p in self.problems:
            if p.slug == slug:
                return p
        return None

    def upsert_problem(self, problem: Problem) -> None:
        existing = self.get_problem(problem.slug)
        if existing is None:
            self.problems.append(problem)
        else:
            # Merge metadata (in case topics/title were updated)
            existing.title = problem.title
            existing.difficulty = problem.difficulty
            existing.topics = problem.topics
            existing.url = problem.url
            existing.folder = problem.folder
            for sub in problem.submissions:
                existing.upsert_submission(sub)

    # --- aggregate stats ---

    @property
    def total(self) -> int:
        return self.stats.get("total", len(self.problems))

    @property
    def by_difficulty(self) -> dict[str, int]:
        if self.stats:
            return {
                "Easy": self.stats.get("easy", 0),
                "Medium": self.stats.get("medium", 0),
                "Hard": self.stats.get("hard", 0),
            }
        counts: dict[str, int] = {"Easy": 0, "Medium": 0, "Hard": 0}
        for p in self.problems:
            counts[p.difficulty] = counts.get(p.difficulty, 0) + 1
        return counts

    @property
    def by_topic(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self.problems:
            for t in p.topics:
                counts[t] = counts.get(t, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    @property
    def recent(self) -> list[Problem]:
        """Last 10 problems sorted by most-recent submission date."""
        def latest_date(p: Problem) -> str:
            return max((s.solved_at for s in p.submissions), default="")
        return sorted(self.problems, key=latest_date, reverse=True)[:10]
