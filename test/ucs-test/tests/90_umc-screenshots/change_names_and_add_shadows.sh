#!/bin/bash

LANGUAGE="en"

while [[ $# -gt 1 ]]
do
key="$1"
case $key in
	-l|--language)
		LANGUAGE="$2"
		shift # past argument
		;;
	*)
		# unknown option
		;;
esac
shift # past argument or value
done

function adapt_for_manual {
	SHADOW=NO
	OUTFILE=default_outfile

	while [[ $# -gt 0 ]]
	do
	key="$1"
	case $key in
		-s|--shadow)
			SHADOW=YES
			;;
		-i|--input-filename)
			INFILE="$2"
			shift # past argument
			;;
		-o|--output-filename)
			OUTFILE="$2"
			shift # past argument
			;;
		*)
			# unknown option
			;;
	esac
	shift # past argument or value
	done

	if [ "$SHADOW" = "YES" ]; then
		convert "$INFILE" \( +clone -background black -shadow 40x5+0+0 \) +swap -background white -layers merge +repage "$OUTFILE"
	else
		cp "$INFILE" "$OUTFILE"
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
