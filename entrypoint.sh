#!/bin/sh
set -e

# GitHub Docker actions mount the repo at /github/workspace
REPO=/github/workspace

# Mark the workspace as safe so git doesn't refuse to run
git config --global --add safe.directory "$REPO"

# Sync solutions from LeetCode
lp sync \
  --session "${INPUT_LEETCODE_SESSION}" \
  --username "${INPUT_USERNAME}" \
  --repo "$REPO"

# Commit and push if there are changes
cd "$REPO"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"
git add -A

if git diff --staged --quiet; then
  echo "No new solutions — nothing to commit."
  exit 0
fi

git commit -m "sync: update LeetCode solutions [skip ci]"

# Use the provided token so the push is authenticated
git remote set-url origin \
  "https://x-access-token:${INPUT_GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git push origin HEAD
