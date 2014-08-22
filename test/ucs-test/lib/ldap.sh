PYTHON=python2.7

scriptlet_error () {
	local function="$1"

	error "Python scriptlet in function $function terminated unexpectedly"
	info "Probably there was an uncaught exception, that should be visible above"
}

ldap_exists () {
	local dn=${1?:missing parameter: dn}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
if ldapconnection.exists('$dn'):
	sys.exit(42)
else:
	sys.exit(43)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		info "Object $dn exists"
		return 0
	elif [ $rc -eq 43 ]; then
		info "Object $dn doesn't exist"
		return 1
	else
		scriptlet_error "ldap_exists"
		return 2
	fi
}

ldap_delete () {
	local dn=${1?:missing parameter: dn}

	declare -a cmd=(ldapdelete -r -x -D "cn=admin,$ldap_base" -y /etc/ldap.secret "$dn")
	if log_and_execute "${cmd[@]}"; then
		info "Successfully deleted ldap object"
		return 0
	else
		info "Failed removing ldap-object"
		return 1
	fi
}

ldap_move () {
	local dn=${1?:missing parameter: dn}
	local newdn=${2?:missing parameter: new dn}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
ldapconnection.move('$dn', '$newdn')
sys.exit(42)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		info "Object $dn is now $newdn"
		return 0
	else
		scriptlet_error "ldap_move"
		return 2
	fi
}

ldap_set_attribute () {
	local dn=${1?:missing parameter: dn}
	local name=${2?:missing parameter: attribute name}
	local value=${3?:missing parameter: attribute value}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
ldapconnection.set_attribute('$dn', '$name', '$value')
sys.exit(42)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ldap_set_attribute"
		return 2
	fi
}

ldap_delete_attribute () {
	local dn=${1?:missing parameter: dn}
	local name=${2?:missing parameter: attribute name}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
ldapconnection.delete_attribute('$dn', '$name')
sys.exit(42)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ldap_delete_attribute"
		return 2
	fi
}

ldap_append_to_attribute () {
	local dn=${1?:missing parameter: dn}
	local name=${2?:missing parameter: attribute name}
	local value=${3?:missing parameter: attribute value}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
ldapconnection.append_to_attribute('$dn', '$name', '$value')
sys.exit(42)
"
	local rc="$?"
	if [ $rc -eq 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ldap_append_to_attribute"
		return 2
	fi
}

ldap_remove_from_attribute () {
	local dn=${1?:missing parameter: dn}
	local name=${2?:missing parameter: attribute name}
	local value=${3?:missing parameter: attribute value}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
ldapconnection.remove_from_attribute('$dn', '$name', '$value')
sys.exit(42)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		info "Object $dn modified"
		return 0
	else
		scriptlet_error "ldap_remove_from_attribute"
		return 2
	fi
}

ldap_get_attribute () {
	local dn=${1?:missing parameter: dn}
	local attribute=${2?:missing parameter: attribute name}

	"$PYTHON" -c "
import sys
sys.path.append('$TESTLIBPATH')
import ldap_glue
ldapconnection = ldap_glue.LDAPConnection()
for value in ldapconnection.get_attribute('$dn', '$attribute'):
	print value
sys.exit(42)
"
	local rc=$?
	if [ $rc -eq 42 ]; then
		return 0
	else
		scriptlet_error "ldap_get_attribute"
		return 2
	fi
}

ldap_verify_attribute () {
	local dn=${1?:missing parameter: dn}
	local attribute=${2?:missing parameter: attribute name}
	local expected_value=${3?:missing parameter: attribute value}

	info "${dn}: \"$attribute\" == \"$expected_value\" ??"

	local value
	value="$(ldap_get_attribute "$dn" "$attribute" "$configbase")"
	local rc=$?
	if [ $rc -ne 0 ]; then
		info "Unexpected return value ($rc) of ldap_get_attribute in ldap_verify_attribute"
		return 2
	fi
	if verify_value "$attribute" "$value" "$expected_value"; then
		info "Yes"
		return 0
	else
		return 1
	fi
}

ldap_verify_multi_value_attribute_contains () {
	local dn=${1?:missing parameter: dn}
	local attribute=${2?:missing parameter: attribute name}
	local expected_value=${3?:missing parameter: attribute value}

	info "${dn}: \"$expected_value\" in \"$attribute\" ??"

	local value
	value="$(ldap_get_attribute "$dn" "$attribute" "$configbase")"
	local rc=$?
	if [ $rc -ne 0 ]; then
		info "Unexpected return value ($rc) of ldap_get_attribute in ldap_verify_multi_value_attribute_contains"
		return 2
	fi
	if verify_value_contains_line "$attribute" "$value" "$expected_value"; then
		info "Yes"
		return 0
	else
		return 1
	fi
}

# vim: set filetype=sh ts=4:
