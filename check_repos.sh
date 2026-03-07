#!/bin/bash

REPOS=("soulprint-core" "soulprint-python" "soulprint-ts")

for repo in "${REPOS[@]}"
do
  echo "=============================="
  echo "Checking repo: $repo"
  echo "=============================="

  cd ~/projects/$repo || continue

  echo "Current branch:"
  git branch --show-current

  echo ""
  echo "Remote:"
  git remote -v

  echo ""
  echo "Last commit:"
  git log -1 --oneline

  echo ""
  echo "Uncommitted changes:"
  git status -s

  echo ""
done
