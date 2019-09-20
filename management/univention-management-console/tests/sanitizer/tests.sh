#!/bin/bash
#
# Univention
#  testscript for UMC sanitizer
#
# Copyright 2012-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

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

