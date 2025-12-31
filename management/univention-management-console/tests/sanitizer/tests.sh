#!/bin/bash
#
# Univention
#  testscript for UMC sanitizer
#
# SPDX-FileCopyrightText: 2012-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

username=${1:-"Administrator"}
password=${2:-"univention"}

_cmd() {
	umc-command -r -U "$username" -P "$password" "$@" 2>/dev/null | sed '1,/MIMETYPE/d;'
}

cmd() {
	_cmd "$1" -e -o "{\"value\": $2}"
}

result() {
#	echo "$@"
	echo -n 'Out: '
	cmd "$@" | sed '1,/MESSAGE/d; s/\s*RESULT\s*:\s*\(.*\)/\1/'
	echo -e '\n###\n'
}

echo -en 'If no assertion tracebacks occur everything should be fine!\n\n'

echo boolean
for i in 'True' 'False' '1' '-2' '"string"' '0'; do
	echo "In: $i"
	result sanitize/bool "$i"
done

echo -en '\n\n\n'

echo choices
# success:
for i in '"Ja"' '1' '2' 'True' '(2,)'; do
	echo "In: $i"
	result sanitize/choices "$i"
done

# failure:
for i in '"Nein"' '0' 'False' '()'; do
	echo "In: $i"
	result sanitize/choices "$i"
done

echo -en '\n\n\n'

echo int
for i in '1' '"1"' '-50' '"-24"' 'True' 'False' '"11111111111111111111111"'; do # Long
	echo "In: $i"
	result sanitize/int "$i"
done

echo -en '\n\n\n'

echo dict
for i in '()' 'dict()' '{}' '1', 'True' '("foo", "bar")'; do
	echo "In: $i"
	result sanitize/dict "$i"
done

echo dict2
for i in '{"foo":1, "bar":"2", "baz":3}' '{"foo":1, "bar":"1"}' '{"foo":1}'; do
	echo "In: $i"
	result sanitize/dict_a "$i"
done

echo -en '\n\n\n'

echo list
for i in '()' '[]' '{}' '1', 'True' '("foo", "bar")'; do
	echo "In: $i"
	result sanitize/list "$i"
done

echo list2
for i in '(1,2,3)' '[1,2,3]' '[1]' '[1,2,3,4]', '[1,2,3,4,5]' '[1,2,3,4,5,6]' '[1,2,3,4,5,6,7]', 'range(100)'; do
	echo "In: $i"
	result sanitize/list_a "$i"
done

echo -en '\n\n\n'

echo mapping
for i in '"foo"' '"bar"' '"baz"' '"notexisting"'; do
	echo "In: $i"
	result sanitize/mapping "$i"
done

echo -en '\n\n\n'

echo string
for i in '"foo"' '1' 'True' '"UTF-8 ;) → O.o"'; do
	echo "In: $i"
	result sanitize/string "$i"
done

echo -en '\n\n\n'

echo pattern
for i in '"* * * * * * * * ** ** "' '"*foo*"' '"*foo"' '"foo*"' '"foo"'; do
	echo "In: $i"
	result sanitize/pattern "$i"
done

echo -en '\n\n\n'

echo "manually check if required attributes works (a message have to be displayed): "
for c in 'bool' 'choices' 'dict' 'email' 'int' 'ldapsearch' 'list' 'mapping' 'pattern' 'string'; do
	echo $c
	_cmd "sanitize/$c"
	_cmd "sanitize/$c"
done
echo 'end required'

