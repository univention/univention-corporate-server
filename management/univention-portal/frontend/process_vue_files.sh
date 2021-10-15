#!/bin/sh

set -e

rm -r src/tmp/ || true
mkdir src/tmp/
for f in $(ls src/views/*.vue src/components/*.vue src/components/*/*.vue); do
	mkdir -p "src/tmp/ts/$(dirname "$f")"
	sed -n '/^<script/,/^<\/script/p' "$f" | sed '1d;$ d' > "src/tmp/ts/$f"
	#mkdir -p "src/tmp/html/$(dirname "$f")"
	#sed -n '/^<template/,/^<\/template/p' "$f" | sed '1d;$ d' | sed -e '/^\s*</d;/^\s*\//d' > "src/tmp/html/$f"
done
