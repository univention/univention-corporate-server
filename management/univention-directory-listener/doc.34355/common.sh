#!/bin/bash
# 1. Setup ACLs once:
#    ssh root@master ". common.sh && HOSTNAME=test setup_slapd"
# 2. Register Listener once:
#    ssh root@test 'ucr set tests/domainadmin/account?"uid=Administrator,cn=users,$(ucr get ldap/base)" tests/domainadmin/pwd?univention'
#    ssh root@test ". common.sh && setup_listener"
# 3. Run tests as often as needed:
#    run-parts --verbose --regex '^test' doc.34355

BUG32685=false # move to selective
BUG33594=true # modrdn delold=1
BUG34355=false # modify+modrdn
BUG34749=false # ldap escape
BUG34833=false # move via temporary
BUG35334=false # utf8 strcasecmp()

LOG="${LBASE:-/root}/listener.log"
LDIF="/var/lib/univention-directory-replication/failed.ldif"
BASE="$(ucr get ldap/base)"
BINDDN="$(ucr get tests/domainadmin/account)"
BINDPW="$(ucr get tests/domainadmin/pwd)"
BINDHOST="$(ucr get ldap/master)"
BINDPORT="$(ucr get ldap/master/port)"
DEBUGPROCNAME="listener"
LCACHE="${LBASE:-/var/lib/univention-directory-listener}"
LMODUL="${LBASE:-/usr/lib/univention-directory-listener}/system"

udm () {
	local module="$1" action="$2"
	shift 2
	/usr/sbin/udm "$module" "$action" --binddn "$BINDDN" --bindpwd "$BINDPW" "$@"
}
ldapsearch () {
	/usr/bin/ldapsearch -h "$BINDHOST" -p "$BINDPORT" -x -D "$BINDDN" -w "$BINDPW" -LLL -o ldif-wrap=no "$@"
}
ldapadd () {
	/usr/bin/ldapadd -x -h "$BINDHOST" -p "$BINDPORT" -D "$BINDDN" -w "$BINDPW" "$@"
}
ldapmodify () {
	/usr/bin/ldapmodify -x -h "$BINDHOST" -p "$BINDPORT" -D "$BINDDN" -w "$BINDPW" "$@"
}
ldapmodrdn () {
	/usr/bin/ldapmodrdn -x -h "$BINDHOST" -p "$BINDPORT" -D "$BINDDN" -w "$BINDPW" "$@"
}
ldapdelete () {
	/usr/bin/ldapdelete -x -h "$BINDHOST" -p "$BINDPORT" -D "$BINDDN" -w "$BINDPW" "$@"
}

setup () {
	tmp="$(mktemp -d)"
	TRACE="${tmp}/trace"
	: >"$LOG"
	setup_ldap
	setup_trace
	sed -ne 's/^## *desc: */*** /p' "$0"
	START="$(date +%s)"
}
setup_slapd () {
	cat >>/etc/univention/templates/files/etc/ldap/slapd.conf.d/60univention-ldap-server_acl-master <<__LDAP__
access to dn.sub="cn=restricted,$BASE"
	by dn.exact="cn=$HOSTNAME,cn=dc,cn=computers,$BASE" none stop
	by * none break
__LDAP__
	ucr commit /etc/ldap/slapd.conf
	slaptest
	/etc/init.d/slapd restart
}
setup_ldap () {
	udm container/cn create --ignore_exists --position "$BASE" --set name=restricted
	udm container/cn create --ignore_exists --position "$BASE" --set name=visible
}
setup_listener () {
	[ -f "$LMODUL/printusers.py" ] && return
	cat >>"$LMODUL/printusers.py" <<__PY__
from __future__ import absolute_import
import listener
name = 'printusers'
description = 'print all changes into a file'
filter = """(objectClass=*)""".translate(None, '\t\n\r')
attributes = []
modrdn = "1"
USER_LIST = '$LOG'
def handler(dn, new, old, command):
	old = old.get('entryUUID', ('-',))[0] if old else '-'
	new = new.get('entryUUID', ('-',))[0] if new else '-'
	with AsRoot():
		with open(USER_LIST, 'a') as out:
			print >> out, "dn=%r old=%s new=%s command=%s" % (
				dn, old, new, command,)
class AsRoot(object):
	def __enter__(self):
		listener.setuid(0)
	def __exit__(self, exc_type, exc_value, traceback):
		listener.unsetuid()
__PY__
	ucr set options='-o'
	listener restart
}
setup_trace () {
	trap on_error ERR
	trap on_exit EXIT
	PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]:-}: '
	exec 3>"$TRACE"
	BASH_XTRACEFD=3
	set -o errexit -o xtrace -o errtrace -o nounset
}
on_error () {
	local rv=$?
	set +e +u +x
	exec 3>&2
	echo "***************************** ERROR $rv ********************************" >&2
	echo "*** Failed command: ${BASH_COMMAND}" >&2
	log_traceback 1
	log_trace
	log_actions
	log_failed_ldif
	log_listener
	exit "$rv"
}
on_exit () {
	local rv=$?
	echo "***************************** EXIT $rv ********************************" >&2
	[ 0 -ne $rv -a -t 0 ] && read -p "Hit key to continue with cleanup"
	ldapsearch -b "$BASE" -s one '(&(objectClass=univentionPackageList)(cn=test*))' dn |
		sed -ne 's/^dn: //p' |
		ldapdelete
	ldapdelete -r "cn=restricted,$BASE"
	ldapdelete -r "cn=visible,$BASE"
	rm -rf "$tmp"
	[ -s "$LDIF" ] && rv=1
	exit "$rv"
}
log_traceback () {
	local -i start=$(( ${1:-0} + 1 ))
	local -i end=${#BASH_SOURCE[@]}
	local -i i=0
	local -i j=0
	echo "Traceback (last called is first): " >&2
	for ((i=${start}; i<${end}; i++))
	do
		j=$(( $i - 1 ))
		echo "    ${FUNCNAME[$i]}() in ${BASH_SOURCE[$i]}:${BASH_LINENO[$j]}" >&2
	done
}
log_trace () {
	[ -s "$TRACE" ] || return 0
	echo "*** Execution trace:" >&2
	cat "$TRACE" >&2 || :
}
log_actions () {
	[ -s "$LOG" ] || return 0
	echo "*** Listener actions:" >&2
	cat "$LOG" >&2 || :
}
log_failed_ldif () {
	[ -s "$LDIF" ] || return 0
	echo "*** Failed LDIF:" >&2
	cat "$LDIF" >&2 || :
}
log_listener () {
	echo "*** Listener log:" >&2
	local date time proc _lp level _rp _co msg ts
	END="$(date +%s)"
	tail -n 1000 /var/log/univention/listener.log |
	while IFS=' ' read date time proc _lp level _rp _co msg
	do
		case "$proc" in
		LISTENER) ;;
		LDAP|*) continue ;;
		esac
		case "$level" in
		ERROR|WARN|PROCESS|INFO) ;;
		ALL|*) continue ;;
		esac
		case "$msg" in
		'importing handler '*) continue ;;
		*': listener passed key='*) continue ;;
		'postrun handler: '*) continue ;;
		'handler:'*) continue ;;
		'connecting to ldap'*) continue ;;
		'simple_bind as '*) continue ;;
		'running handlers for '*) continue ;;
		esac
		ts="$(date -d "20${date:6:2}-${date:3:2}-${date:0:2} ${time}" +%s)"
		[ "$START" -le "$ts" -a "$ts" -le "$END" ] &&
			echo "${level}: ${msg}" >&2
	done
}

check () {
	local dn="$(_py_repr "${1},${BASE}")" old="${2:-.*}" new="${3:-.*}" cmd="${4-[amdrn]}"
	wait_listener
	grep -x "dn=${dn} old=${old} new=${new} command=${cmd}" "$LOG"
}
neg () {
	"$@" && return 1 || return 0
}
_py_repr () {
	python -c 'import sys,re;print re.sub(r"[][^\\.*$]", lambda m:"\\"+m.group(0), repr(sys.argv[1]))' "$1"
}
wait_listener () {
	while [ "$(<"$LCACHE/notifier_id")" -lt "$(/usr/share/univention-directory-listener/get_notifier_id.py)" ]
	do
		[ -s "$LDIF" ] && exit 1
		printf .
		sleep 10
	done
}
listener () {
	case "$1" in
	stop) wait_listener ;;
	esac
	if pgrep -x gdb >/dev/null && pgrep -x "$DEBUGPROCNAME" >/dev/null
	then
		case "$1" in
		stop) pkill -STOP "$DEBUGPROCNAME" ; return ;;
		start) pkill -CONT "$DEBUGPROCNAME" ; return ;;
		esac
	fi
	/etc/init.d/univention-directory-listener "$@"
}
uuid () {
	local dn="$1"
	ldapsearch -b "$dn" -s base entryUUID | sed -ne 's/entryUUID: //p' | tee /dev/stderr
}
does_replication () {
	case "$(ucr get server/role)" in
	domaincontroller_backup) return 0 ;;
	domaincontroller_slave) return 0 ;;
	*) return 1 ;;
	esac
}

case "$(type -t main 2>/dev/null)" in
function)
	setup
	main
	;;
esac
