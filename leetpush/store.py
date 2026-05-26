from __future__ import annotations

import json
from pathlib import Path

from .models import SolutionsIndex

_FILENAME = "solutions.json"


def load_index(repo_root: Path) -> SolutionsIndex:
    path = repo_root / _FILENAME
    if not path.exists():
        return SolutionsIndex.empty()
    with path.open() as f:
        return SolutionsIndex.from_dict(json.load(f))


def save_index(repo_root: Path, index: SolutionsIndex) -> None:
    path = repo_root / _FILENAME
    with path.open("w") as f:
        json.dump(index.to_dict(), f, indent=2, ensure_ascii=False)
        f.write("\n")
