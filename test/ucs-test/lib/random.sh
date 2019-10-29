#!/bin/bash
STRINGLENGTH=8 #length of the username to test
SIGNOFFSET=4 #which letter the . or - should be in the username (from behind)

_lowerletters="abcdefghijklmnopqrstuvwxyz"
_upperletters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ciphers="0123456789"

random_chars () { # [length [characters]]
	local prefix= suffix=
	while [ $# -ge 2 ]
	do
		case "$1" in
		--prefix) prefix+="${2:$((RANDOM % ${#2})):1}" ; shift 2 ;;
		--suffix) suffix+="${2:$((RANDOM % ${#2})):1}" ; shift 2 ;;
		*) break ;;
		esac
	done
	local chars="${2:-${_lowerletters}}"

	declare -i now=$(($(date +%s%N) / 1000000 % (24*60*60))) modulo=${#chars}
	while [ $now -gt 0 ]
	do
		suffix="${chars:$((now % modulo)):1}${suffix}"
		now=$((now / modulo))
	done

	declare -i length=$((${1:-$STRINGLENGTH}-${#prefix}-${#suffix}))
	while [ $length -ge 1 ]
	do
		prefix+="${chars:$((RANDOM % ${#chars})):1}"
		length+=-1
	done
	echo -n "${prefix}${suffix}"
}

random_string () { # Generates a random string with length $STRINGLENGTH. The String is lowercase
	random_chars "$STRINGLENGTH" "${_lowerletters}${_ciphers}äöü"
}

random_mailaddress () { # Generates a random string with a length of 20 characters
	random_chars 20 "${_lowerletters}${_ciphers}"
}

random_hostname () { # Generates a random string with a length of 20
	random_chars --prefix "${_lowerletters}" 20 "${_lowerletters}${_ciphers}"
}

random_share () { # Generates a random string with length $STRINGLENGTH. string_numbers_letters_dots_spaces
	random_chars --prefix "${_upperletters}${_lowerletters}${_ciphers}" --suffix "${_upperletters}${_lowerletters}${_ciphers}" "$STRINGLENGTH" "${_upperletters}${_lowerletters}${_ciphers}._ -"
}

random_ipv4 () { # Generate a random IPv4 address
	echo -n $((RANDOM % 253 + 1)).$((RANDOM % 253 + 1)).$((RANDOM % 253 + 1)).$((RANDOM % 253 + 1))
}
random_date () { # Generate a random date Y-m-d between 4000 days before and after today
	echo -n $(date +%F --date="$((RANDOM %8000 - 4000))day")
}

# vim:set filetype=sh ts=4:
