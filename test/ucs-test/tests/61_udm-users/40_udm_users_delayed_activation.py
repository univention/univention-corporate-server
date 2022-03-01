#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -s -l -v
# -*- coding: utf-8 -*-
## desc: Test users/user accountActivationDate
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - python3-univention-directory-manager (>= 15.0.11-18)
## bugs: [53631]

import subprocess
import time
from datetime import datetime, timedelta

import pytest

import univention.admin.uldap
import univention.testing.udm as udm_test
import univention.testing.utils as utils
from univention.config_registry import handler_set, handler_unset

ucrv = "directory/manager/user/accountactivation/cron"
expected_default_ucr_value = "*/15 * * * *"


def run_activation_script():
	subprocess.check_call(["/usr/share/univention-directory-manager-tools/univention-delayed-account-activation"])


@pytest.fixture
def disabled_cronjob():
	"""Disable cron to avoid race"""
	handler_set(['%s=%s' % (ucrv, "# disabled")])
	yield
	handler_unset(['%s' % (ucrv, )])


@pytest.mark.roles('domaincontroller_master')
def test_default_ucr_value(udm, ucr):
	"""Check default cron value"""

	value = ucr.get(ucrv)
	assert value == expected_default_ucr_value


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_disabled_user_creation_activation(disabled_cronjob, udm, ucr):
	"""Check cron based activation of users/user with accountActivationDate"""

	now = datetime.now()
	with open("/etc/timezone", "r") as tzfile:
		timezone = tzfile.read().strip()
	ts_later = (now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M " + timezone)
	userdn, username = udm.create_user(accountActivationDate=ts_later)
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectNotFound, utils.LDAPUnexpectedObjectFound):
		utils.fail("User creation failed")
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled, despite setting future accountActivationDate")

	# verify that account can't bind
	with pytest.raises(univention.admin.uexceptions.authFail):
		lo = univention.admin.uldap.access(binddn=userdn, bindpw="univention")
		lo.lo.lo.whoami_s()

	handler_set(['%s=%s' % (ucrv, "*/1 *  * * *")])

	time.sleep(2 * 60)

	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "0"})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is still disabled, after accountActivationDate")


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_disabled_user_creation(disabled_cronjob, udm):
	"""Create users/user with accountActivationDate"""
	now = datetime.now()
	with open("/etc/timezone", "r") as tzfile:
		timezone = tzfile.read().strip()
	ts_earlier = now.strftime("%Y-%m-%d %H:%M " + timezone)
	ts_later = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M " + timezone)
	userdn, username = udm.create_user(accountActivationDate=ts_later)
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectNotFound, utils.LDAPUnexpectedObjectFound):
		utils.fail("User creation failed")
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled, despite setting future accountActivationDate")

	# verify that account can't bind
	with pytest.raises(univention.admin.uexceptions.authFail):
		univention.admin.uldap.access(binddn=userdn, bindpw="univention")

	# Now that the accountActivationDate is still in the future, run the script
	run_activation_script()
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled any longer, after running univention-delayed-account-activation despite future accountActivationDate")

	# Now set the accountActivationDate a bit back, so the date has passed
	udm.modify_object('users/user', dn=userdn, accountActivationDate=ts_earlier)
	run_activation_script()
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "0"})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is still disabled, after running univention-delayed-account-activation after accountActivationDate")

	# verify that account can bind
	univention.admin.uldap.access(binddn=userdn, bindpw="univention")


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_disabled_and_expired_user_creation(disabled_cronjob, udm):
	"""Create users/user with accountActivationDate and userexpiry"""
	now = datetime.now()
	with open("/etc/timezone", "r") as tzfile:
		timezone = tzfile.read().strip()
	ts_earlier = now.strftime("%Y-%m-%d %H:%M " + timezone)
	ts_later = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M " + timezone)

	date_today_in_utc = datetime.utcnow().strftime("%Y-%m-%d")
	"""
	Note: If you ask date to show the "now" in localtime (default, without --utc), and you are in Europe/Berlin,
	for example, then at time "2021-08-17 23:30 UTC" it will output "2021-08-18", because it's already 0:30 (or 1:30 in summertime) in the local (Europe/Berlin) timezone.
	UDM userexpiry (at least with Bug #46349 open) will be interpreted as UTC and mapped to krb5ValidEnd YYYYmmdd000000Z.
	Thus, in the Europe/Berlin example it would write 20210818000000Z to krb5ValidEnd instead of 20210817000000Z.

	The univention-delayed-account-activation takes care not to activate accounts that are already expired at runtime (UTC), and the purpose of following test case is to verify that.

	Thus, the value of userexpiry needs to be given as UTC, to have:
		accountActivationDate="2021-08-17 23:00 UTC" and userexpiry="2021-08-17"
	instead of
		accountActivationDate="2021-08-17 23:00 UTC" and userexpiry="2021-08-18"
	"""

	userdn, username = udm.create_user(accountActivationDate=ts_later, userexpiry=date_today_in_utc)
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectNotFound, utils.LDAPUnexpectedObjectFound):
		utils.fail("User creation failed")
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled, despite setting future accountActivationDate")
	except AssertionError:
		print("User is not disabled, despite setting future accountActivationDate")
		utils.fail("User is not disabled, despite setting future accountActivationDate")

	# verify that account can't bind
	with pytest.raises(univention.admin.uexceptions.authFail):
		univention.admin.uldap.access(binddn=userdn, bindpw="univention")

	run_activation_script()
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled any longer, after running univention-delayed-account-activation despite future accountActivationDate")

	udm.modify_object('users/user', dn=userdn, accountActivationDate=ts_earlier)
	run_activation_script()
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User has been activated, even though it is set to expired")

	# Check expectation: accountActivationDate should be cleaned up
	try:
		utils.verify_ldap_object(userdn, {'accountActivationDate': []})
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("accountActivationDate has not been cleaned up on expired account")


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_access_to_accountActivationDate(disabled_cronjob, udm):
	"""Check access to accountActivationDate"""
	now = datetime.now()
	with open("/etc/timezone", "r") as tzfile:
		timezone = tzfile.read().strip()
	ts_earlier = now.strftime("%Y-%m-%d %H:%M " + timezone)
	ts_later = (now + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M " + timezone)
	userdn, username = udm.create_user(accountActivationDate=ts_later, password="univention")
	try:
		udm.verify_udm_object("users/user", userdn, {"disabled": "1"})
	except (utils.LDAPObjectNotFound, utils.LDAPUnexpectedObjectFound):
		utils.fail("User creation failed")
	except (utils.LDAPObjectValueMissing, utils.LDAPObjectUnexpectedValue):
		utils.fail("User is not disabled, despite setting future accountActivationDate")

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('users/user', dn=userdn, accountActivationDate=ts_earlier, binddn=userdn, bindpwd="univention")

	other_userdn, other_username = udm.create_user(password="univention")
	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('users/user', dn=userdn, accountActivationDate=ts_earlier, binddn=other_userdn, bindpwd="univention")
