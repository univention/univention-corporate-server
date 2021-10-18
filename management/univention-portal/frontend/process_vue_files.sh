#!/bin/sh

set -e

SRC_FOLDER="$(dirname "$0")"/src
echo looking in $SRC_FOLDER for .vue files
rm -r $SRC_FOLDER/tmp/ || true
mkdir $SRC_FOLDER/tmp/
for f in $(ls $SRC_FOLDER/views/*.vue $SRC_FOLDER/components/*.vue $SRC_FOLDER/components/*/*.vue); do
	mkdir -p "$SRC_FOLDER/tmp/ts/$(dirname "$f")"
	sed -n '/^<script/,/^<\/script/p' "$f" | sed '1d;$ d' > "$SRC_FOLDER/tmp/ts/$f"
	#mkdir -p "$SRC_FOLDER/tmp/html/$(dirname "$f")"
	#sed -n '/^<template/,/^<\/template/p' "$f" | sed '1d;$ d' | sed -e '/^\s*</d;/^\s*\//d' > "$SRC_FOLDER/tmp/html/$f"
done
