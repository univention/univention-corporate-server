#!/bin/bash
# shellcheck shell=bash

LANGUAGE="en"

while [ $# -gt 1 ]
do
	key="$1"
	shift
	case "$key" in
	-l|--language)
		LANGUAGE="$1"
		shift
		;;
	*)
		# unknown option
		;;
	esac
done

adapt_for_manual () {
	local SHADOW=false INFILE='' OUTFILE=default_outfile
	while [ $# -gt 0 ]
	do
		key="$1"
		shift
		case "$key" in
		-s|--shadow)
			SHADOW=true
			;;
		-i|--input-filename)
			INFILE="$1"
			shift
			;;
		-o|--output-filename)
			OUTFILE="$1"
			shift
			;;
		*)
			# unknown option
			;;
		esac
	done

	if "$SHADOW"; then
		convert "${INFILE:?}" \( +clone -background black -shadow 40x5+0+0 \) +swap -background white -layers merge +repage "${OUTFILE:?}"
	else
		cp "${INFILE:?}" "${OUTFILE:?}"
	fi
}

mkdir manual
adapt_for_manual -i "portal_$LANGUAGE.png" -o "manual/portal_$LANGUAGE.png"
adapt_for_manual -i "umc-favorites_$LANGUAGE.png" -o "manual/umc-favorites-tab_$LANGUAGE.png" -s
adapt_for_manual -i "umc-ldap_$LANGUAGE.png" -o "manual/umc_navigation_$LANGUAGE.png" -s
adapt_for_manual -i "umc-login_cropped_$LANGUAGE.png" -o "manual/umc_login_$LANGUAGE.png" -s
adapt_for_manual -i "umc-users-add_dialog_$LANGUAGE.png" -o "manual/users_user_$LANGUAGE.png" -s
adapt_for_manual -i "umc-users-details_$LANGUAGE.png" -o "manual/users_user_advanced_$LANGUAGE.png" -s
adapt_for_manual -i "umc-users-template_$LANGUAGE.png" -o "manual/users_usertemplate_$LANGUAGE.png" -s
adapt_for_manual -i "umc-users_$LANGUAGE.png" -o "manual/umc_user_$LANGUAGE.png" -s
