#!/bin/bash
# cmp.sh SNAPDIR: count trees changed vs identical against corpus/parsed
cd /home/user/builders_lab/corpus/parsed
same=0; ch=0
for f in */*.json; do case $f in _*) continue;; esac
  if cmp -s "$f" "$1/$f"; then same=$((same+1)); else ch=$((ch+1)); echo "CHANGED $f"; fi
done
echo "identical $same changed $ch"
