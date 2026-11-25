#!/usr/bin/env bash
# Build one ZIP per skill for upload in the Claude app (Customize > Skills > Upload a skill).
# Each ZIP holds the skill folder with the shared rules copied in. Output: plugin/dist/ (not committed).
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist && mkdir -p dist/tmp
for dir in skills/*/; do
  name=$(basename "$dir")
  mkdir -p "dist/tmp/$name"
  cp -r "$dir". "dist/tmp/$name/"
  cp shared/rules.md "dist/tmp/$name/rules.md"
  sed -i 's#`\.\./\.\./shared/rules\.md`#`rules.md` (in this skill)#' "dist/tmp/$name/SKILL.md"
  (cd dist/tmp && zip -qr "../$name.zip" "$name")
done
rm -rf dist/tmp
ls -1 dist
