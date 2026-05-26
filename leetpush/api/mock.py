from __future__ import annotations

from datetime import date, timezone

from .base import LeetCodeAPI

# ---------------------------------------------------------------------------
# Static fixture data
# ---------------------------------------------------------------------------

_PROBLEMS: dict[str, dict] = {
    "two-sum": {
        "questionId": "1",
        "title": "Two Sum",
        "titleSlug": "two-sum",
        "difficulty": "Easy",
        "topicTags": [{"name": "Array", "slug": "array"}, {"name": "Hash Table", "slug": "hash-table"}],
    },
    "coin-change": {
        "questionId": "322",
        "title": "Coin Change",
        "titleSlug": "coin-change",
        "difficulty": "Medium",
        "topicTags": [
            {"name": "Dynamic Programming", "slug": "dynamic-programming"},
            {"name": "Breadth-First Search", "slug": "breadth-first-search"},
        ],
    },
    "merge-k-sorted-lists": {
        "questionId": "23",
        "title": "Merge k Sorted Lists",
        "titleSlug": "merge-k-sorted-lists",
        "difficulty": "Hard",
        "topicTags": [
            {"name": "Linked List", "slug": "linked-list"},
            {"name": "Divide and Conquer", "slug": "divide-and-conquer"},
            {"name": "Heap (Priority Queue)", "slug": "heap-priority-queue"},
        ],
    },
    "binary-search": {
        "questionId": "704",
        "title": "Binary Search",
        "titleSlug": "binary-search",
        "difficulty": "Easy",
        "topicTags": [{"name": "Array", "slug": "array"}, {"name": "Binary Search", "slug": "binary-search"}],
    },
}

_SUBMISSIONS: list[dict] = [
    # binary-search — python3 (most recent)
    {"id": "3000001", "title": "Binary Search", "titleSlug": "binary-search", "timestamp": "1748217600", "lang": "python3"},
    # merge-k-sorted-lists — java
    {"id": "3000002", "title": "Merge k Sorted Lists", "titleSlug": "merge-k-sorted-lists", "timestamp": "1748131200", "lang": "java"},
    # coin-change — python3
    {"id": "3000003", "title": "Coin Change", "titleSlug": "coin-change", "timestamp": "1748044800", "lang": "python3"},
    # two-sum — cpp (solved after python, same problem different lang)
    {"id": "3000004", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": "1747958400", "lang": "cpp"},
    # two-sum — python3 (earlier submission, should still be kept since different lang)
    {"id": "3000005", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": "1747872000", "lang": "python3"},
]

_DETAILS: dict[str, dict] = {
    "3000001": {
        "code": (
            "class Solution:\n"
            "    def search(self, nums: list[int], target: int) -> int:\n"
            "        left, right = 0, len(nums) - 1\n"
            "        while left <= right:\n"
            "            mid = (left + right) // 2\n"
            "            if nums[mid] == target:\n"
            "                return mid\n"
            "            elif nums[mid] < target:\n"
            "                left = mid + 1\n"
            "            else:\n"
            "                right = mid - 1\n"
            "        return -1\n"
        ),
        "runtime_ms": 43,
        "memory_mb": 16.8,
        "lang": "python3",
    },
    "3000002": {
        "code": (
            "class Solution {\n"
            "    public ListNode mergeKLists(ListNode[] lists) {\n"
            "        PriorityQueue<ListNode> pq = new PriorityQueue<>(\n"
            "            (a, b) -> a.val - b.val\n"
            "        );\n"
            "        for (ListNode node : lists) if (node != null) pq.offer(node);\n"
            "        ListNode dummy = new ListNode(0), cur = dummy;\n"
            "        while (!pq.isEmpty()) {\n"
            "            cur.next = pq.poll();\n"
            "            cur = cur.next;\n"
            "            if (cur.next != null) pq.offer(cur.next);\n"
            "        }\n"
            "        return dummy.next;\n"
            "    }\n"
            "}\n"
        ),
        "runtime_ms": 3,
        "memory_mb": 44.2,
        "lang": "java",
    },
    "3000003": {
        "code": (
            "class Solution:\n"
            "    def coinChange(self, coins: list[int], amount: int) -> int:\n"
            "        dp = [float('inf')] * (amount + 1)\n"
            "        dp[0] = 0\n"
            "        for coin in coins:\n"
            "            for x in range(coin, amount + 1):\n"
            "                dp[x] = min(dp[x], dp[x - coin] + 1)\n"
            "        return dp[amount] if dp[amount] != float('inf') else -1\n"
        ),
        "runtime_ms": 1243,
        "memory_mb": 14.3,
        "lang": "python3",
    },
    "3000004": {
        "code": (
            "class Solution {\n"
            "public:\n"
            "    vector<int> twoSum(vector<int>& nums, int target) {\n"
            "        unordered_map<int, int> map;\n"
            "        for (int i = 0; i < nums.size(); i++) {\n"
            "            int complement = target - nums[i];\n"
            "            if (map.count(complement)) return {map[complement], i};\n"
            "            map[nums[i]] = i;\n"
            "        }\n"
            "        return {};\n"
            "    }\n"
            "};\n"
        ),
        "runtime_ms": 7,
        "memory_mb": 10.2,
        "lang": "cpp",
    },
    "3000005": {
        "code": (
            "class Solution:\n"
            "    def twoSum(self, nums: list[int], target: int) -> list[int]:\n"
            "        seen = {}\n"
            "        for i, n in enumerate(nums):\n"
            "            if target - n in seen:\n"
            "                return [seen[target - n], i]\n"
            "            seen[n] = i\n"
            "        return []\n"
        ),
        "runtime_ms": 52,
        "memory_mb": 17.6,
        "lang": "python3",
    },
}


class MockLeetCodeClient(LeetCodeAPI):
    """In-memory mock — same interface as LeetCodeClient, no network calls."""

    def get_problem_metadata(self, slug: str) -> dict:
        if slug not in _PROBLEMS:
            raise KeyError(f"Mock has no problem with slug '{slug}'")
        return _PROBLEMS[slug]

    def get_recent_ac_submissions(self, username: str, limit: int = 100) -> list[dict]:
        return _SUBMISSIONS[:limit]

    def get_submission_detail(self, submission_id: str) -> dict:
        if submission_id not in _DETAILS:
            raise KeyError(f"Mock has no submission with id '{submission_id}'")
        return _DETAILS[submission_id]

    def get_profile_stats(self, username: str) -> dict[str, int]:
        easy = sum(1 for s in _SUBMISSIONS if _PROBLEMS.get(s["titleSlug"], {}).get("difficulty") == "Easy")
        medium = sum(1 for s in _SUBMISSIONS if _PROBLEMS.get(s["titleSlug"], {}).get("difficulty") == "Medium")
        hard = sum(1 for s in _SUBMISSIONS if _PROBLEMS.get(s["titleSlug"], {}).get("difficulty") == "Hard")
        # deduplicate by slug
        slugs = {s["titleSlug"] for s in _SUBMISSIONS}
        by_diff: dict[str, int] = {"Easy": 0, "Medium": 0, "Hard": 0}
        for slug in slugs:
            d = _PROBLEMS.get(slug, {}).get("difficulty", "")
            if d in by_diff:
                by_diff[d] += 1
        return {"total": len(slugs), "easy": by_diff["Easy"], "medium": by_diff["Medium"], "hard": by_diff["Hard"]}

    def get_submission_calendar(self, username: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for sub in _SUBMISSIONS:
            d = date.fromtimestamp(int(sub["timestamp"]), tz=timezone.utc).isoformat()
            counts[d] = counts.get(d, 0) + 1
        return counts
