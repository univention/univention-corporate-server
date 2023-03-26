# shellcheck shell=sh
for _sh in /usr/share/univention-lib/*.sh
do
	[ "${_sh##*/}" = all.sh ] && continue
	# shellcheck source=/dev/null
	. "$_sh"
done
unset _sh
