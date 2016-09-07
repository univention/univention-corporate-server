#!/usr/bin/env bash
shopt -s globstar
for fl in ./**/*.po; do
	mv "$fl" "$(dirname "$fl")/fr.po"
	#printf "%s\n" "$fl $(dirname "$fl")/fr.po"
done
