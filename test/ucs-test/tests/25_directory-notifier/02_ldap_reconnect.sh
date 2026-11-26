#!/usr/share/ucs-test/runner bash
# shellcheck shell=bash
## desc: Notifier survives a failed reconnect to slapd and keeps cn=translog complete
## roles: [domaincontroller_master]
## tags: [basic]
## packages:
##  - univention-directory-notifier
##  - univention-directory-listener
## exposure: dangerous

# shellcheck source=../../lib/base.sh
. "$TESTLIBPATH/base.sh" || exit 137
# shellcheck source=../../lib/user.sh
. "$TESTLIBPATH/user.sh" || exit 137

NOTIFIER=univention-directory-notifier
LISTENER=univention-directory-listener
TRANSACTION=/var/lib/univention-ldap/notify/transaction
LISTENER_PRIV=/var/lib/univention-ldap/listener/listener.priv
LISTENER_LOG=/var/log/univention/listener.log

USER_BOUND=$(user_randomname)
USER_QUEUED=$(user_randomname)
USER_STOPPED=$(user_randomname)

notifier_pid=

cleanup () {
	[ -n "$notifier_pid" ] && kill -CONT "$notifier_pid" 2>/dev/null
	systemctl start slapd
	systemctl start "$NOTIFIER"
	user_remove "$USER_STOPPED"
	user_remove "$USER_QUEUED"
	user_remove "$USER_BOUND"
}
trap cleanup EXIT

unit_prop () {
	systemctl show -p "$2" --value "$1"
}

last_transaction_id () {
	tail -n 1 "$TRANSACTION" | cut -d ' ' -f 1
}

translog_has () {
	ldapsearch -LLL -Q -Y EXTERNAL -H ldapi:/// -b cn=translog "(reqSession=$1)" dn | grep -q '^dn: '
}

check_translog_complete () { # <first transaction ID>
	local id last_id
	last_id=$(last_transaction_id)
	for id in $(seq "$1" "$last_id")
	do
		translog_has "$id" || fail_test 110 "transaction $id is missing from cn=translog"
	done
}

check_user_in_translog () { # <username>
	local id
	id=$(grep -F " $(user_dn "$1") a" "$TRANSACTION" | cut -d ' ' -f 1)
	[ -n "$id" ] || fail_test 110 "the creation of user $1 is missing from $TRANSACTION"
	[ -n "$id" ] && ! translog_has "$id" && fail_test 110 "the creation of user $1 ($id) is missing from cn=translog"
}

queue_while_slapd_down () { # <username>
	notifier_pid=$(unit_prop "$NOTIFIER" MainPID)
	kill -STOP "$notifier_pid"
	user_create "$1" || fail_fast 140 "cannot create user $1"
	systemctl stop slapd
	kill -CONT "$notifier_pid"
	notifier_pid=
}

wait_for_backlog () {
	for _ in $(seq 60)
	do
		[ -s "$LISTENER_PRIV" ] || break
		sleep 1
	done
	[ -s "$LISTENER_PRIV" ] && fail_test 110 "$NOTIFIER did not process $LISTENER_PRIV after slapd came back"
	wait_for_replication || fail_test 110 'replication did not finish after slapd came back'
}

systemctl is-active --quiet "$NOTIFIER" || fail_fast 140 "$NOTIFIER is not running"

# The bound connection makes the next failure go through the reconnect path, as after slapd's idle timeout, not the startup bind.
section 'Write one transaction so the notifier holds a bound LDAP connection'
user_create "$USER_BOUND" || fail_fast 140 "cannot create user $USER_BOUND"
wait_for_replication || fail_fast 140 'replication did not finish'

first_id=$(( $(last_transaction_id) + 1 ))
notifier_restarts=$(unit_prop "$NOTIFIER" NRestarts)
listener_pid=$(unit_prop "$LISTENER" MainPID)
listener_log_lines=$(wc -l <"$LISTENER_LOG")

# Freezing the notifier lets slapd record a real change before it stops, so the notifier wakes up to a write it cannot do.
# A notifier that aborts here (Issue #3755) is restarted by systemd and drops every connected listener.
section 'Queue a transaction while the notifier is frozen, then take slapd away'
queue_while_slapd_down "$USER_QUEUED"
sleep 10

if [ "$(unit_prop "$NOTIFIER" NRestarts)" != "$notifier_restarts" ] || ! kill -0 "$(unit_prop "$NOTIFIER" MainPID)" 2>/dev/null
then
	journalctl --no-pager -n 20 -u "$NOTIFIER"
	fail_test 110 "$NOTIFIER terminated while slapd was unreachable"
fi

# Listeners may only learn about transactions that are in cn=translog, so a notifier that skips the failed write leaves a gap here.
section 'Start slapd and wait for the notifier to flush its backlog'
systemctl start slapd
wait_for_backlog
check_user_in_translog "$USER_QUEUED"
check_translog_complete "$first_id"

[ "$(unit_prop "$LISTENER" MainPID)" = "$listener_pid" ] || fail_test 110 "$LISTENER was restarted"
if tail -n +"$((listener_log_lines + 1))" "$LISTENER_LOG" | grep -E 'Connection reset by peer while receiving from notifier|connection to notifier was closed'
then
	fail_test 110 "$LISTENER lost its connection to $NOTIFIER"
fi

# A notifier that removes listener.priv on shutdown loses the pending transaction from both the transaction file and cn=translog,
# which the gap check cannot see, so the user's transaction is looked up by DN.
section 'Stop the notifier while it retries; the next start must write the pending transaction'
first_id=$(( $(last_transaction_id) + 1 ))
queue_while_slapd_down "$USER_STOPPED"
sleep 5
timeout 20 systemctl stop "$NOTIFIER" || fail_test 110 "$NOTIFIER did not stop within 20 s while retrying"
[ -s "$LISTENER_PRIV" ] || fail_test 110 "$LISTENER_PRIV was removed although user $USER_STOPPED was not written to cn=translog"
systemctl start slapd
systemctl start "$NOTIFIER"
wait_for_backlog
check_user_in_translog "$USER_STOPPED"
check_translog_complete "$first_id"

exit "$RETVAL"
# vim: set filetype=sh ts=4 :
