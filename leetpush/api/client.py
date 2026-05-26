from __future__ import annotations

import re
import requests

from .base import LeetCodeAPI

GRAPHQL_URL = "https://leetcode.com/graphql"

_PROBLEM_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    difficulty
    topicTags {
      name
      slug
    }
  }
}
"""

_RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
    lang
  }
}
"""

_SUBMISSION_DETAIL_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    code
    runtimeDisplay
    memoryDisplay
    lang {
      name
    }
  }
}
"""


def _parse_runtime(display: str | None) -> int | None:
    """'52 ms' → 52, 'N/A' → None"""
    if not display:
        return None
    m = re.search(r"(\d+)", display)
    return int(m.group(1)) if m else None


def _parse_memory(display: str | None) -> float | None:
    """'17.6 MB' → 17.6, 'N/A' → None"""
    if not display:
        return None
    m = re.search(r"([\d.]+)", display)
    return float(m.group(1)) if m else None


class LeetCodeClient(LeetCodeAPI):
    def __init__(self, session_cookie: str):
        self.session = requests.Session()
        self.session.cookies.set("LEETCODE_SESSION", session_cookie, domain="leetcode.com")
        self._init_csrf()

    def _init_csrf(self) -> None:
        resp = self.session.get("https://leetcode.com/", timeout=10)
        csrf = self.session.cookies.get("csrftoken")
        self.session.headers.update({
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/",
            "X-CSRFToken": csrf or "",
        })

    def _query(self, query: str, variables: dict) -> dict:
        resp = self.session.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]

    def get_problem_metadata(self, slug: str) -> dict:
        data = self._query(_PROBLEM_QUERY, {"titleSlug": slug})
        return data["question"]

    def get_recent_ac_submissions(self, username: str, limit: int = 100) -> list[dict]:
        data = self._query(_RECENT_AC_QUERY, {"username": username, "limit": limit})
        return data["recentAcSubmissionList"] or []

    def get_submission_detail(self, submission_id: str) -> dict:
        data = self._query(_SUBMISSION_DETAIL_QUERY, {"submissionId": int(submission_id)})
        detail = data["submissionDetails"]
        return {
            "code": detail["code"],
            "runtime_ms": _parse_runtime(detail.get("runtimeDisplay")),
            "memory_mb": _parse_memory(detail.get("memoryDisplay")),
            "lang": detail["lang"]["name"],
        }
