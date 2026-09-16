#!/usr/bin/env bash
# Install the do-skills into ~/.agents/skills and link them into ~/.claude/skills.
set -euo pipefail

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

git clone --depth 1 --quiet https://github.com/tullolabs/do-skills "$tmp/do-skills"

mkdir -p ~/.agents/skills ~/.claude/skills
for d in "$tmp"/do-skills/do-*/; do
  n=$(basename "$d")
  rm -rf ~/.agents/skills/"$n"
  cp -r "$d" ~/.agents/skills/"$n"
  ln -sfn "../../.agents/skills/$n" ~/.claude/skills/"$n"
  echo "installed /$n"
done

echo
echo "Done. Run /do-ops to see which skill handles what."
