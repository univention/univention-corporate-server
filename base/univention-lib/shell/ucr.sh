is_ucr_true () { # test if UCS variable is "true" or "false"
	local value
	value="$(univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
		1|yes|on|true|enable|enabled) return 0 ;;
		0|no|off|false|disable|disabled) return 1 ;;
		*) return 2 ;;
	esac
}

#
# removes a UCR template and moves it to /etc/univention/templates/removed
#
# remove_ucr_template <filename-of-config-file>
# e.g. remove_ucr_template /etc/obsolete-software.conf
#
remove_ucr_template () {
	if [ -e "$1" ] ; then
	    mv "$1" /etc/univention/templates/removed/
	fi

	if [ -e /etc/univention/templates/files/"$1" ] ; then
	    mv /etc/univention/templates/files/"$1" /etc/univention/templates/removed/"$1".template
	fi
}
