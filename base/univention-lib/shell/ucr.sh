is_ucr_true () { # test if UCS variable is "true" or "false"
	local value
	value="$(univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
		1|yes|on|true|enable|enabled) return 0 ;;
		0|no|off|false|disable|disabled) return 1 ;;
		*) return 2 ;;
	esac
}
