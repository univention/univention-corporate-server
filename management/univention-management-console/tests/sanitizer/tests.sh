#!/usr/bin/bash
#
# Univention
#  testscript for UMC sanitizer
#
# Copyright 2012 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

username=${1:-"Administrator"}
password=${2:-"univention"}

alias cmd="umc-command -U $username -P $password"

for c in ('bool', 'choices', 'dict', 'email', 'int', 'ldapsearch', 'list', 'mapping', 'pattern', 'search', 'string'); do
	echo 'check if required attribute works'
	cmd "sanitize/$c"
	echo 'end required'

echo boolean
for i in ('True', 'False', '1', '-2', '"string"', '0'); do
	cmd sanitize/bool -e -o '{"value": '$i'}'

echo choices
# success:
for i in ('"Ja"', '1', '2', 'True', '(2,)' ); do
	cmd sanitize/choices -e -o '{"value": '$i'}'

# failure:
for i in ('"Nein"', '0', 'False', '()' ); do
	cmd sanitize/choices -e -o '{"value": '$i'}'

echo int
for i in ('1', '"1"', '-50', '"-24"', 'True', 'False', '"11111111111111111111111"'); do # Long
	cmd sanitize/int -e -o '{"value": '$i'}'

echo dict
cmd sanitize/dict '{"value": (), "keys": {"foo":1, "bar":"2", "baz":3}}'
cmd sanitize/dict '{"value": dict(), "keys": {"foo":1, "bar":"1"}}'
cmd sanitize/dict '{"value": {}, "keys": {"foo":1}}'
