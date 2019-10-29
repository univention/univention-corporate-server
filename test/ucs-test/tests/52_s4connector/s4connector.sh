#######################################################
#
# Hints for the S4 connector tests:
#
# Most of the AD tests require an active-directory server
# to be configured prior to execution.
#
# It should be sufficient to use the qa-test-vms, for example
# Windows.2008.Server.UCS2-3-0 Win2k3 should also work, but
# Win2k probably won't work with this test.
#
# The Test uses 'connector' as configuration name, so you can
# use UMC for configuration which is probably easiest.
#
# In case the test fails, however, you should check, whether the
# server is reachable via connector/ad/ldap/host and
# connector/ad/ldap/port whether the server certificate is
# correctly installed in the path specified in
# connector/ad/ldap/certificate whether the correct ad-password
# is in the file specified in connector/ad/ldap/bindpw
# and whether the values in connector/ad/ldap/base and
# connector/ad/ldap/binddn are sane.
#
# Also note, that most of the tests assume the default mapping, so
# in case of changes in the mapping configuration they might fail
# although there's no error in the connector.
#
########################################################

#Should the test-cases fail when there are tracebacks in
#the connectors log files ? (True/False)
#They might be unrelated to the failing testcase but in
#general it's still a good thing to turn
#this on. If you don't turn it on, there'll still be
#warnings. You'll probably also want to turn on
#AD_DELETE_TRACEBACK_FILE
AD_CHECK_LOG_FOR_TRACEBACKS=False

#If the logs are checked for tracebacks (AD_CHECK_LOG_FOR_TRACEBACKS)
#should the tracebackfile
#be deleted after printing its contents to the testlog, in order for
#adjacent testcases to be able to succeed ? (True/False)
#This way the connector-tracebacks can be easily associated with
#the provoking testcase.
AD_DELETE_TRACEBACK_FILE=False

# Amount of time that the tests will reserve for computation
# that is necessary for the synchronisation done in one single
# poll. You should change this value if you suspect some tests
# are failing because of the test-systems being too slow to
# synchronize fast enough.
AD_ESTIMATED_MAX_COMPUTATION_TIME=3

########################################################
#
# This function waits for the synchronisation of an
# object to complete and for possible back-synchronisation
# effects to settle.
#
# Synchronizing ldap-objects is no
# atomic operation and the existance-test might be true
# before an object is fully synchronized. This is a problem because
# for example, an object might get deleted while its attributes are
# still being synced
# resulting in the object still existing but with partial attributes.
# Also there might be some back-synchronisation effects.
#
# This function should be called whenever one wants to be
# sure that there are no more outstanding synchronisations.
#
# The function returns 0 if it thinks that no more synchronizations will occur
# and 1 if it thinks, that the synchronisations might go on eternally or the
# AD-Connector indicates some error. Any other value indicates an internal error.
#
# You should check for the return value of this function in order to detect
# possible ping-pong synchronisation scenarios or other problems you might miss
# with the normal checks in your testcase.
#

. /usr/share/univention-lib/all.sh

ad_is_connector_running () {
	/etc/init.d/univention-s4-connector status >/dev/null 2>&1
}

function ad_wait_for_synchronization () {
	let local min_wait_time="${1:-1}"
	local configbase="${2:-connector}"

	if ! ad_is_connector_running; then
		/etc/init.d/univention-s4-connector start
	fi

	#maybe there are ways be more sure whether synchronisation is
	#already complete:
	#See /var/log/univention/${configbase}-status.log
	#and univention-connector-list-rejected

	let local synctime="2 * ($(ucr get $configbase/s4/poll/sleep) + $AD_ESTIMATED_MAX_COMPUTATION_TIME)"
	if [ "$min_wait_time" -gt "$synctime" ]; then
		synctime="$min_wait_time"
	fi
	info "Waiting for full synchronisation (sleeping for $synctime seconds)"
	info "Hint: You might want to decrease this value during debugging of the tests"
	sleep "$synctime"

	#TODO: Implement (conservative) ping-pong detection (if possible at all)

	# TODO: -tracebacks.log has been removed in UCS 3.0
###	local tracebackfile="/var/log/univention/${configbase}-tracebacks.log"
###	info "Checking for existence of $tracebackfile ..."
###	if [ -f "$tracebackfile" ]; then
###		info "Found Tracebackfile!!"
###		if [ "$AD_CHECK_LOG_FOR_TRACEBACKS" == "True" ]; then
###			warning "Probably the testcases actions provoked a \
###traceback in the AD-Connector. If you believe, that the current testcase is unrelated to \
###the existence of the traceback-file, or you simply want to ignore that file you might want \
###to remove it, or set AD_CHECK_LOG_FOR_TRACEBACKS in s4connector.lib to False."
###			warning "-----Contents of the Traceback-file:-------"
###			warning "$(cat $tracebackfile)"
###			warning "-----End Contents of the Traceback-file----"
###			if [ "$AD_DELETE_TRACEBACK_FILE" == "True" ]; then
###				info "Deleting Tracebackfile because AD_DELETE_TRACEBACK_FILE is set to True"
###				rm -f "$tracebackfile"
###			else
###				warning "The following testcases will also fail because of the tracebackfile still \
###existing. If you want to avoid this, you should set AD_DELETE_TRACEBACK_FILE in s4connector.lib \
###to True. It's contents will still be printed here."
###			fi
###			return 1
###		else
###			warning "Ignoring Tracebackfile because AD_CHECK_LOG_FOR_TRACEBACKS is False."
###		fi
###	fi

	return 0
}

function scriptlet_error () {
	local function="$1"

	error "Python scriptlet in function $function terminated unexpectedly"
	info "Probably there was an uncaught exception, that should be visible above"
}

function ad_get_base () {
	local configbase="${1:-connector}"
	ucr get $configbase/s4/ldap/base
}

function ad_get_sync_mode () {
	local configbase="${1:-connector}"
	ucr get $configbase/s4/mapping/syncmode
}

function ad_set_sync_mode () {
	local mode="$1"
	local configbase="${2:-connector}"

	info "Setting S4 connector '$configbase' to ${mode}-mode"
	if [ "$mode" != "$(ad_get_sync_mode $configbase)" ]; then
		ucr set $configbase/s4/mapping/syncmode=$mode
		invoke-rc.d univention-s4-connector restart
		if ! ad_is_connector_running; then
			# try again
			sleep 3
			invoke-rc.d univention-s4-connector restart
		fi
	else
		info "Already in ${mode}-mode"
	fi
}

function ad_exists () {
	local dn="$1"
	local configbase="${2:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
if adconnection.exists ('$dn'):
	sys.exit (42)
else:
	sys.exit (43)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn exists"
		return 0
	elif [ "$retval" == 43 ]; then
		info "Object $dn doesn't exist"
		return 1
	else
		scriptlet_error "ad_exists"
		return 2
	fi
}

function ad_delete () {
	local dn="$1"
	local configbase="${2:-connector}"

	local pwfile="$(ucr get ${configbase}/ad/ldap/bindpw)"

	info "Recursively deleting $dn"

	ldbdel -H ldapi:///var/lib/samba/private/ldap_priv/ldapi -r "$dn"
	if [ $? = 0 ]; then
		return 0
	else
		return 1
	fi
}

function ad_move () {
	local dn="$1"
	local newdn="$2"
	local configbase="${3:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.move ('$dn', '$newdn')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn is now $newdn"
		return 0
	else
		scriptlet_error "ad_move"
		return 2
	fi
}

function ad_set_attribute () {
	local dn="$1"
	local name="$2"
	local value="$3"
	local configbase="${4:-connector}"
	local treat_value_as_base64="${5:-False}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
if $treat_value_as_base64:
	import base64
	value = base64.decodestring('$value')
else:
	value = '$value'
adconnection.set_attribute ('$dn', '$name', value)
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ad_set_attribute"
		return 2
	fi
}

function ad_delete_attribute () {
	local dn="$1"
	local name="$2"
	local configbase="${3:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.delete_attribute ('$dn', '$name')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ad_delete_attribute"
		return 2
	fi
}

function ad_append_to_attribute () {
	local dn="$1"
	local name="$2"
	local value="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.append_to_attribute ('$dn', '$name', '$value')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ad_append_to_attribute"
		return 2
	fi
}

function ad_remove_from_attribute () {
	local dn="$1"
	local name="$2"
	local value="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.remove_from_attribute ('$dn', '$name', '$value')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ad_remove_from_attribute"
		return 2
	fi
}

function ad_create_ConnectionPolicy() {
	local cn="$1"
	local printername="$2"
	local servername="$3"
	local uncname="$4"
	local printattributes="$5"
	local dn="$6"
	local configbase="${7:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection('$configbase')
attrs = {}
attrs['objectclass'] = ['top', 'msPrint-ConnectionPolicy']
attrs['cn'] = ['$cn']
attrs['uNCName'] = ['$uncname']
attrs['serverName'] = ['$servername']
attrs['printerName'] = ['$printername']
attrs['printAttributes'] = ['$printattributes']
dn = '$dn'
adconnection.create(dn, attrs)
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "ConnectionPolicy $cn created"
		return 0
	else
		scriptlet_error "ad_create_ConnectionPolicy"
		return 2
	fi
}

function ad_createuser () {
	local username="$1"
	local description="$2"
	local position="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.createuser ('$username', description='$description', position='$position')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "User $username created"
		return 0
	else
		scriptlet_error "ad_createuser"
		return 2
	fi
}

function ad_group_create () {
	local groupname="$1"
	local description="$2"
	local position="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.group_create ('$groupname', description='$description', position='$position')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Group $groupname created"
		return 0
	else
		scriptlet_error "ad_group_create"
		return 2
	fi
}

function ad_container_create () {
	local containername="$1"
	local description="$2"
	local position="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.container_create ('$containername', description='$description', position='$position')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Container $containername created"
		return 0
	else
		scriptlet_error "ad_container_create"
		return 2
	fi
}

function ad_createou () {
	local ouname="$1"
	local description="$2"
	local position="$3"
	local configbase="${4:-connector}"

	python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.createou ('$ouname', description='$description', position='$position')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		info "Ou $ouname created"
		return 0
	else
		scriptlet_error "ad_createou"
		return 2
	fi
}

function ad_get_attribute () {
	local dn="$1"
	local attribute="$2"
	local configbase="${3:-connector}"

python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
for value in adconnection.get_attribute ('$dn', '$attribute'):
	print value
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		return 0
	else
		scriptlet_error "ad_get_attribute"
		return 2
	fi
}

function ad_verify_attribute () {
	local dn="$1"
	local attribute="$2"
	local expected_value="$3"
	local configbase="${4:-connector}"
	local case_sensitive="${5:-false}"

	info "${dn}: \"$attribute\" == \"$expected_value\" ??"

	local value
	value="$(ad_get_attribute "$dn" "$attribute" "$configbase")"
	local retval="$?"
	if [ "$retval" != 0 ]; then
		info "Unexpected return value ($retval) of ad_get_attribute in ad_verify_attribute"
		return 2
	fi
	if $case_sensitive; then
		if verify_value_ignore_case "$attribute" "$value" "$expected_value"; then
			info "Yes"
			return 0
		else
			return 1
		fi
	else
		if verify_value "$attribute" "$value" "$expected_value"; then
			info "Yes"
			return 0
		else
			return 1
		fi
	fi
}

function ad_verify_multi_value_attribute_contains () {
	local dn="$1"
	local attribute="$2"
	local expected_value="$3"
	local configbase="${4:-connector}"

	info "${dn}: \"$expected_value\" in \"$attribute\" ??"

	local value
	value="$(ad_get_attribute "$dn" "$attribute" "$configbase")"
	local retval="$?"
	if [ "$retval" != 0 ]; then
		info "Unexpected return value ($retval) of ad_get_attribute in ad_verify_multi_value_attribute_contains"
		return 2
	fi
	if verify_value_contains_line_ignore_case "$attribute" "$value" "$expected_value"; then
		info "Yes"
		return 0
	else
		return 1
	fi
}

function ad_get_primary_group () {
	local user_dn="$1"
	local configbase="${2:-connector}"

python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
group = adconnection.getprimarygroup ('$user_dn')
if group:
	print group
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		return 0
	else
		scriptlet_error "ad_get_primary_group"
		return 2
	fi
}

function ad_set_primary_group () {
	local user_dn="$1"
	local group_dn="$2"
	local configbase="${3:-connector}"

python2.7 -c "
import sys
sys.path.append('$TESTLIBPATH')
import s4connector
adconnection = s4connector.S4Connection ('$configbase')
adconnection.setprimarygroup ('$user_dn', '$group_dn')
sys.exit (42)
"
	local retval="$?"
	if [ "$retval" == 42 ]; then
		return 0
	else
		scriptlet_error "ad_set_primary_group"
		return 2
	fi
}

function ad_verify_user_primary_group_attribute () {
	local primarygroup_dn="$1"
	local user_dn="$2"
	local configbase="${3:-connector}"

	info "is $primarygroup_dn the primary group of $user_dn ?"

	local actual_primarygroup_dn
	actual_primarygroup_dn="$(ad_get_primary_group "$user_dn" "$configbase")"
	local retval="$?"
	if [ "$retval" != 0 ]; then
		info "Unexpected return value ($retval) of ad_get_primary_group \
in ad_verify_user_primary_group_attribute"
		return 2
	fi

	if [ "${actual_primarygroup_dn,,}" = "${primarygroup_dn,,}" ]; then
		info "Yes."
		return 0
	else
		info "No. \"$actual_primarygroup_dn\" is."
		return 1
	fi	
}

function ad_set_retry_rejected ()
{
	local retry=$1
	local retry_old="$(ucr get connector/s4/retryrejected)"
	if [ "$retry" != "$retry_old" ]; then
		ucr set connector/s4/retryrejected="$retry"
		invoke-rc.d univention-s4-connector restart
		if ! ad_is_connector_running; then
			# try again
			sleep 3
			invoke-rc.d univention-s4-connector restart
		fi
	fi
}

function connector_running_on_this_host ()
{
	is_ucr_true connector/s4/autostart
	return $?
}

function ad_connector_start ()
{
	invoke-rc.d univention-s4-connector start
	sleep 3 # wait a few seconds
}

function ad_connector_stop ()
{
	invoke-rc.d univention-s4-connector stop
	sleep 3 # wait a few seconds
}

function ad_connector_restart ()
{
	invoke-rc.d univention-s4-connector restart
	sleep 3 # wait a few seconds
}

function connector_mapping_adjust ()
{
	MAIN_FILE="/usr/lib/python2.7/dist-packages/univention/s4connector/s4/main.py"
	if [ -e "$MAIN_FILE" ]; then
		cp -f "$MAIN_FILE" "$MAIN_FILE".ucs-test-backup
		if [ -n "$3" ]; then
			sed -i "/^mapping = imp.*/a ucs_test_filter = mapping.s4_mapping['$1'].ignore_filter\nucs_test_filter = ucs_test_filter[0:len(ucs_test_filter)-1]\nucs_test_filter = ucs_test_filter + '(uid=$2))'\nmapping.s4_mapping['$1'].ignore_filter = ucs_test_filter" "$MAIN_FILE"
		else
			sed -i "/^mapping = imp.*/a mapping.s4_mapping['$1'].ignore_subtree = mapping.s4_mapping['$1'].ignore_subtree + ['$2']" "$MAIN_FILE"
		fi
	else
		MAIN_FILE="/usr/share/pyshared/univention/s4connector/s4/main.py"
		cp -f "$MAIN_FILE" "$MAIN_FILE".ucs-test-backup
		if [ -n "$3" ]; then
			sed -i "s/import mapping/import mapping\nucs_test_filter = mapping.s4_mapping ['$1'].ignore_filter\nucs_test_filter = ucs_test_filter[0:len(ucs_test_filter)-1]\nucs_test_filter=ucs_test_filter+'(uid=$2))'\nmapping.s4_mapping ['$1'].ignore_filter = ucs_test_filter/" "$MAIN_FILE"
		else
			sed -i "s/import mapping/import mapping\nmapping.s4_mapping ['$1'].ignore_subtree = mapping.s4_mapping ['$1'].ignore_subtree + ['$2']/" "$MAIN_FILE"
		fi
	fi

}


function connector_mapping_restore ()
{
	MAIN_FILE="/usr/lib/python2.7/dist-packages/univention/s4connector/s4/main.py"
	if [ ! -e "$MAIN_FILE" ]; then
		MAIN_FILE="/usr/share/pyshared/univention/s4connector/s4/main.py"
	fi
	mv -f "$MAIN_FILE".ucs-test-backup "$MAIN_FILE"
}


# vim:syntax=sh
# Local Variables:
# mode: sh
# End:
