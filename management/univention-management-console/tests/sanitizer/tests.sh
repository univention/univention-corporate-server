#!/usr/bin/bash

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
