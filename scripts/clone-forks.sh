#!/bin/bash
# Clone Lukas's forks into ~/Projects/Github/lukaskellerstein/forks/, with
# `origin` = the fork and `upstream` = the original (PLAN.md section 5).
#
#   scripts/clone-forks.sh
#
# Lukas runs it in his own terminal: the worktree guard of a `claude -w`
# session refuses git in another folder. Safe to run again: an existing clone
# is only fetched. It stops at the first clone whose remotes are not the ones
# below, rather than fetch into a checkout that belongs to something else. A
# sixth fork is one more line in REPOS. FORKS_DIR overrides the target, for a
# test. bash 3.2.

set -eu

forks_dir="${FORKS_DIR:-$HOME/Projects/Github/lukaskellerstein/forks}"
owner=lukaskellerstein

# <repo> <upstream owner>; the fork is github.com/$owner/<repo>.
REPOS="
agent-eval-harness opendatahub-io
eval-hub eval-hub
eval-hub-contrib eval-hub
trustyai-service-operator trustyai-explainability
odh-dashboard opendatahub-io
"

# The URL as configured, not as a url.<base>.insteadOf rule rewrites it.
remote_url() { git -C "$1" config --get "remote.$2.url" || true; }

check_remote() {
  actual=$(remote_url "$1" "$2")
  if [ "$actual" != "$3" ]; then
    echo "clone-forks: $1: $2 is '${actual:-missing}', expected $3; stopping" >&2
    exit 1
  fi
}

mkdir -p "$forks_dir"
# REPOS comes in on fd 3, so a git that reads stdin cannot eat the next lines.
while read -r repo upstream_owner <&3; do
  [ -n "$repo" ] || continue
  dir="$forks_dir/$repo"
  fork="https://github.com/$owner/$repo.git"
  upstream="https://github.com/$upstream_owner/$repo.git"
  if [ -e "$dir" ]; then
    check_remote "$dir" origin "$fork"
  else
    # Blobs on demand keep a clone of a large monorepo such as odh-dashboard fast.
    git clone --quiet --filter=blob:none "$fork" "$dir"
  fi
  if [ -z "$(remote_url "$dir" upstream)" ]; then
    git -C "$dir" remote add upstream "$upstream"
  fi
  check_remote "$dir" upstream "$upstream"
  git -C "$dir" fetch --quiet --all --prune
  echo "$repo: origin $fork, upstream $upstream"
done 3<<EOF
$REPOS
EOF
