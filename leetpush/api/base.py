from abc import ABC, abstractmethod


class LeetCodeAPI(ABC):

    @abstractmethod
    def get_problem_metadata(self, slug: str) -> dict:
        """Return raw problem metadata dict with keys:
        questionId, title, titleSlug, difficulty, topicTags ([{name, slug}])
        """

    @abstractmethod
    def get_recent_ac_submissions(self, username: str, limit: int = 100) -> list[dict]:
        """Return list of recent accepted submissions (no code) with keys:
        id, title, titleSlug, timestamp (unix str), lang
        """

    @abstractmethod
    def get_submission_detail(self, submission_id: str) -> dict | None:
        """Return submission detail with keys:
        code, runtime_ms (int|None), memory_mb (float|None), lang (str)
        """

    @abstractmethod
    def get_profile_stats(self, username: str) -> dict[str, int]:
        """Return {total, easy, medium, hard} from the user's LeetCode profile."""

    @abstractmethod
    def get_submission_calendar(self, username: str) -> tuple[dict[str, int], int]:
        """Return ({date_str: count}, current_streak) from LeetCode's userCalendar.

        The calendar covers all historical activity (same data as the profile
        contribution graph). The streak is LeetCode's own authoritative value,
        calculated in the user's local timezone.
        date_str format: "YYYY-MM-DD"
        """
