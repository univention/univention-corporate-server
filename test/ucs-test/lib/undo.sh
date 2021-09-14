#!/bin/bash
# shellcheck shell=bash
# Run shell snippets in reversed order to undo things

TEST_undo=$(mktemp -d)
declare -r TEST_undo
declare -i TEST_order=1
undo () { # collect undo commands in file executed on EXIT
	# Usage: create_foo ... && undo remove_foo ...
	local arg args=()
	for arg in "$@"
	do
		args+=("$(printf '%q' "$arg")")
	done
	local order
	order=$(printf '%s/%08d' "$TEST_undo" "$TEST_order")
	echo "${args[@]}" >"$order"
	TEST_order+=1
}
TEST_cleanup () {
	set +e
	local arg
	for arg in $(run-parts --list --reverse "$TEST_undo")
	do
		# shellcheck source=/dev/null
		. "$arg"
	done
	rm -rf "$TEST_undo"
}
trap TEST_cleanup EXIT
