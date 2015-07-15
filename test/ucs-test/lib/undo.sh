#!/bin/bash
# Run shell snippets in reversed order to undo things

declare -r TEST_undo=$(mktemp -d)
declare -i TEST_order=1
undo () { # collect undo commands in file executed on EXIT
	# Usage: create_foo ... && undo remove_foo ...
	local arg args=()
	for arg in "$@"
	do
		args+=("$(printf '%q' "$arg")")
	done
	local order=$(printf '%s/%08d' "$TEST_undo" "$TEST_order")
	echo "${args[@]}" >"$order"
	TEST_order+=1
}
TEST_cleanup () {
	set +e
	local arg
	for arg in $(run-parts --list --reverse "$TEST_undo")
	do
		. "$arg"
	done
	rm -rf "$TEST_undo"
}
trap TEST_cleanup EXIT
