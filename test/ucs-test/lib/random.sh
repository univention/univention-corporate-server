#!/bin/bash
STRINGLENGTH=8 #length of the username to test
SIGNOFFSET=4 #wich letter the . or - schould be in the username (from behind)

_lowerletters="abcdefghijklmnopqrstuvwxyz"
_upperletters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ciphers="0123456789"

random_chars () { # [length [characters]]
	local stringlength=${1:-$STRINGLENGTH}
	local charset=${2:-${_lowerletters}}
	local string=
	while ((${#string} < $stringlength))
	do
		local pos=$((RANDOM % ${#charset}))
		string+=${charset:$pos:1}
	done
	echo -n "$string"
}

random_lowercasedigit () { # Generates a random lowercase character (a-z0-9äöü)
	random_chars 1 "${_lowerletters}${_ciphers}äöü"
}

random_uppercasedigit () { # Generates a random uppercase character (A-Z0-9ÄÖÜ)
	random_chars 1 "${_upperletters}${_ciphers}ÄÖÜ"
}

random_maildigit () { # Generates a random lowercase character (a-z0-9)
	random_chars 1 "${_lowerletters}${_ciphers}"
}

random_letter () { # Generates a random lowercase letter (a-z)
	random_chars 1 "${_lowerletters}"
}

random_string () { # Generates a random string with length $STRINGLENGTH. The String is lowercase
	random_chars "$STRINGLENGTH" "${_lowerletters}${_ciphers}äöü"
}

random_stringstartinguppercase () { # Generates a random string with length $STRINGLENGTH. The String starts uppercase
	random_chars 1 "${_upperletters}${_ciphers}ÄÖÜ"
	random_chars "$(($STRINGLENGTH -1))" "${_lowerletters}${_ciphers}äöü"
}

random_mailaddress () { # Generates a random string with a length of 20 characters
	random_chars 20 "${_lowerletters}${_ciphers}"
}

random_hostname () { # Generates a random string with a length of 20
	random_chars 1 "${_lowerletters}"
	random_chars 19 "${_lowerletters}${_ciphers}"
}

random_share () { # Generates a random string with length $STRINGLENGTH. string_numbers_letters_dots_spaces
	random_chars 1 "${_upperletters}${_lowerletters}${_ciphers}"
	random_chars "$(($STRINGLENGTH -2))" "${_upperletters}${_lowerletters}${_ciphers}._ -"
	random_chars 1 "${_upperletters}${_lowerletters}${_ciphers}"
}

random_octet () { # Generates an octet for an ip-adress and echos it.
	echo -n $((RANDOM % 255))
}

random_ipv4 () { # Generate a random IPv4 address
	echo -n $((RANDOM % 253 + 1)).$((RANDOM % 253 + 1)).$((RANDOM % 253 + 1)).$((RANDOM % 253 + 1))
}

# vim:set filetype=sh ts=4:
