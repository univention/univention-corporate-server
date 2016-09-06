for _sh in /usr/share/univention-lib/*.sh
do
	[ "${_sh##*/}" = all.sh ] && continue
	. "$_sh"
done
unset _sh
