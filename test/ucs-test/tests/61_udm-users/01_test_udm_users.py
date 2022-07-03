#!/usr/share/ucs-test/runner pytest-3
# -*- coding: utf-8 -*-
## desc: Test users/user
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import base64
import pprint
import random
import subprocess
import time
from datetime import datetime, timedelta

import pytest

import univention.admin.modules as udm_modules
import univention.admin.uldap
import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils
from univention.admin.uldap import position
from univention.testing.umc import Client


@pytest.fixture
def stopped_s4_connector():
	# Since the S4 connector uses a object based synchronization,
	# it is a problem to change the same object in short intervals,
	# see https://forge.univention.org/bugzilla/show_bug.cgi?id=35336
	if utils.s4connector_present():
		utils.stop_s4connector()
	yield
	if utils.s4connector_present():
		utils.start_s4connector()


@pytest.fixture
def restart_slapd_after_test():
	yield
	utils.restart_slapd()


class Test_UserCreation(object):

	def test_user_creation(self, udm):
		"""Create users/user"""
		user = udm.create_user()[0]
		utils.verify_ldap_object(user)

	@pytest.mark.tags('apptest')
	def test_user_creation_person_option(self, udm):
		"""Create users/user with just the person-option set"""
		# bugs: [24351]

		user = udm.create_user(options=['person'])[0]  # FIXME
		utils.verify_ldap_object(user)

	@pytest.mark.tags('apptest')
	def test_user_creation_with_username_already_in_use(self, udm):
		"""Create users/user with username which is already in use"""
		first_user_container = udm.create_object('container/cn', name=uts.random_name())
		second_user_container = udm.create_object('container/cn', name=uts.random_name())

		username = udm.create_user(position=first_user_container)[1]

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_user(username=username, position=second_user_container)

	@pytest.mark.tags('apptest')
	def test_user_creation_with_mailPrimaryAddress_already_in_use(self, udm):
		"""Create users/user with mailPrimaryAddress which is already in use"""
		mailDomainName = '%s.%s' % (uts.random_name(), uts.random_name())
		emailaddr = uts.random_name()
		udm.create_object('mail/domain', name=mailDomainName)
		udm.create_user(mailPrimaryAddress='%s@%s' % (emailaddr, mailDomainName))
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_user(mailPrimaryAddress='%s@%s' % (emailaddr, mailDomainName))

	def test_user_creation_with_uidNumber_already_in_use(self, udm):
		"""Create users/user with uidNumber which is already in use"""
		uid_number = str(random.randint(3000, 4999))
		udm.create_user(uidNumber=uid_number)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_user(uidNumber=uid_number)


class Test_UserModification(object):

	def test_user_modification_set_pwdChangeNextLogin(self, udm):
		"""Mark the password of a user to be altered on next login"""
		user = udm.create_user()[0]
		udm.modify_object('users/user', dn=user, pwdChangeNextLogin='1')

		utils.verify_ldap_object(user, {'shadowMax': ['1']})

	@pytest.mark.tags('apptest')
	def test_user_modification_set_pwdChangeNextLogin_kerberos_option(self, udm):
		"""Mark the password of a kerberos user to be altered on next login"""
		date = time.gmtime(time.time())
		user = udm.create_user()[0]
		udm.modify_object('users/user', dn=user, pwdChangeNextLogin='1')

		utils.verify_ldap_object(user, {'krb5PasswordEnd': [time.strftime('%Y%m%d', date) + '000000Z']})

	@pytest.mark.tags('apptest')
	def test_user_modification_set_birthday(self, udm):
		"""Set userBirthday during users/user modification"""
		user = udm.create_user()[0]

		userBirthday = '2005-01-01'
		udm.modify_object('users/user', dn=user, birthday=userBirthday)

		utils.verify_ldap_object(user, {'univentionBirthday': [userBirthday]})

	def test_user_modification_set_jpegPhoto(self, udm):
		"""Set jpegPhoto during users/user modification"""
		user = udm.create_user()[0]

		with open('/usr/share/ucs-test/61_udm-users/example_user_jpeg_photo.jpg', "rb") as jpeg:
			jpeg_data = jpeg.read()

		udm.modify_object('users/user', dn=user, jpegPhoto=base64.b64encode(jpeg_data).decode('ascii'))
		utils.verify_ldap_object(user, {'jpegPhoto': [jpeg_data]})

	def test_user_creation_with_umlaut_in_username(self, udm):
		"""Create users/user with umlaut in username"""
		# bugs: [11415]
		user = udm.create_user(username='%säÄöÖüÜ%s' % (uts.random_name(length=4), uts.random_name(length=4)))[0]
		utils.verify_ldap_object(user)


@pytest.mark.tags('apptest')
def test_validate_that_simpleauthaccount_are_ignore_in_license(udm):
	"""Check whether a simple-auth-account appears in the license-check"""
	# bugs: [13721]
	license_before = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]
	with udm_test.UCSTestUDM() as udm:
		udm.create_ldap_user()
		license_after = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]

	assert license_before == license_after, 'The license before creating a simple-auth user differs from the license after creating the user'


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
def test_execute_udm_users_list_as_administrator(ucr):
	"""Execute "udm users/user list --filter uid=Administrator" as Administrator"""
	# bugs: [37331]

	# get the Administrator username translation if case of non English domain:
	admin_username = ucr.get('users/default/administrator') or "Administrator"
	print("Administrator username is:", admin_username)

	cmd = ('su', admin_username, '-c', '/usr/sbin/univention-directory-manager users/user list --filter uid=' + admin_username)
	udm = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	output = udm.communicate()[0].decode('utf-8', 'replace')

	assert udm.returncode == 0, 'UDM-CLI returned "%d" while trying to execute "%s" as Administrator. Returncode "0" was expected.' % (udm.returncode, cmd[3:])

	assert ('DN: uid=' + admin_username) in output, 'Could not find DN of "%s" user in the UDM-CLI output:\n%s' % (admin_username, output)


def test_user_removal(udm):
	"""Remove users/user"""
	user = udm.create_user()[0]
	udm.remove_object('users/user', dn=user)

	utils.verify_ldap_object(user, should_exist=False)


@pytest.mark.tags('apptest')
def test_ignore_user_with_functional_flag(stopped_s4_connector, udm):
	"""Create users/user and test "functional" object flag"""
	# bugs: [34395]
	license_before = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]

	# create user and check its existence
	user_dn = udm.create_user(check_for_drs_replication=False, wait_for=False)[0]
	utils.verify_ldap_object(user_dn)
	stdout = subprocess.Popen([udm_test.UCSTestUDM.PATH_UDM_CLI_CLIENT, 'users/user', 'list'], stdout=subprocess.PIPE).communicate()[0]
	assert user_dn.lower().encode('UTF-8') in stdout.lower(), 'Cannot find user DN %s in output of "udm users/user list":\n%s' % (user_dn, stdout)

	# perform a license check
	license_after = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]
	assert license_before != license_after, 'License check failed to detect normal user'

	# add 'functional' flag to user
	lo = utils.get_ldap_connection()
	lo.modify(user_dn, (('univentionObjectFlag', b'', b'functional'),))
	utils.wait_for_replication()
	stdout = subprocess.Popen([udm_test.UCSTestUDM.PATH_UDM_CLI_CLIENT, 'users/user', 'list'], stdout=subprocess.PIPE).communicate()[0]
	assert user_dn.lower().encode('UTF-8') not in stdout.lower(), '"udm users/user list" still finds user object with functional flag'

	# perform a license check
	license_after = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]
	assert license_before == license_after, 'License check detected to "functional" user'

	# remove 'functional' flag to user
	lo.modify(user_dn, (('univentionObjectFlag', b'functional', b''),))
	utils.wait_for_replication()
	stdout = subprocess.Popen([udm_test.UCSTestUDM.PATH_UDM_CLI_CLIENT, 'users/user', 'list'], stdout=subprocess.PIPE).communicate()[0]
	assert user_dn.lower().encode('UTF-8') in stdout.lower(), 'Cannot find user DN %s in output of "udm users/user list" after removing flag:\n%s' % (user_dn, stdout)

	# perform a license check
	license_after = subprocess.Popen(['univention-license-check'], stdout=subprocess.PIPE).communicate()[0]
	assert license_before != license_after, 'License check failed to detect normal user'


@pytest.mark.exposure('dangerous')
def test_script_lock_expired_accounts(stopped_s4_connector, udm):  # TODO: parametrize
	"""Check cron job script lock_expired_accounts"""
	# bugs: [35088]

	print(time.ctime())
	udm_modules.update()
	lo, position = univention.admin.uldap.getAdminConnection()
	udm_modules.init(lo, position, udm_modules.get('users/user'))

	def create_user(expiry_days_delta, locked_status):
		expiry_time = datetime.utcnow() + timedelta(days=expiry_days_delta)
		userdn, username = udm.create_user(userexpiry=expiry_time.strftime("%Y-%m-%d"), check_for_drs_replication=False, wait_for=False)
		if locked_status == '1':
			locktime = time.strftime("%Y%m%d%H%M%SZ", time.gmtime())
			subprocess.check_call(['/usr/bin/python3', '-m', 'univention.lib.account', 'lock', '--dn', userdn, '--lock-time', locktime])
		return username

	userdata = {}
	for delta, initial_state, expected_state in [
		[-9, '0', '0'],
		[-8, '0', '0'],
		# [-7, '0', '0'],  disabled due to bug #36210
		# [-6, '0', '1'],  disabled due to bug #36210
		[-5, '0', '1'],
		[-4, '0', '1'],
		[-3, '0', '1'],
		[-2, '0', '1'],
		[-1, '0', '1'],
		# [0, '0', '1'],  disabled due to bug #36210
		[1, '0', '0'],
		[2, '0', '0'],
		[-4, '1', '1'],
		# [0, '1', '1'],  disabled due to bug #36210
		[2, '1', '1'],
	]:
		userdata[create_user(delta, initial_state)] = [initial_state, expected_state]

	ldap_filter = '(|(uid=' + ')(uid='.join(userdata.keys()) + '))'

	results = udm_modules.lookup('users/user', None, lo, scope='sub', filter=ldap_filter)
	if len(results) != len(userdata):
		print('RESULTS: %r' % (pprint.PrettyPrinter(indent=2).pformat(results),))
		utils.fail('Did not find all users prior to script execution!')
	for entry in results:
		entry.open()
		assert entry['locked'] == userdata[entry['username']][0], 'uid=%s should not be locked for posix prior to script execution!' % (entry['username'],)

	print('Calling lock_expired_accounts...')
	subprocess.check_call(['/usr/share/univention-directory-manager-tools/lock_expired_accounts', '--only-last-week'])
	print('DONE')

	results = udm_modules.lookup('users/user', None, lo, scope='sub', filter=ldap_filter)
	if len(results) != len(userdata):
		print('RESULTS: %r' % (pprint.PrettyPrinter(indent=2).pformat(results),))
		utils.fail('Did not find all users after script execution!')
	for entry in results:
		entry.open()
		assert entry['locked'] == userdata[entry['username']][1], 'The account uid=%r is not in expected locking state: expected=%r  current=%r' % (entry['username'], userdata[entry['username']][1], entry['locked'])


@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('delta,disabled,expected', [
	[-9, '0', 1],
	[-8, '0', 1],
	[-7, '0', 1],
	[-6, '0', 1],
	[-5, '0', 1],
	[-4, '0', 1],
	[-3, '0', 1],
	[-2, '0', 1],
	[-1, '0', 1],
	[1, '0', 0],
	[2, '0', 0],
	[-4, '1', 1],
	[2, '1', 1],
	[3, '1', 1],
])
def test_script_lock_expired_passwords(udm, ucr, delta, disabled, expected):
	"""Check if ldap auth is denied for expired passwords"""
	# bugs: [35088]
	assert ucr.is_true('ldap/shadowbind', True), 'UCR variable ldap/shadowbind is disabled (%s), test will not work' % ucr['ldap/shadowbind']

	print(time.ctime())
	lo, position = univention.admin.uldap.getAdminConnection()
	today = int(time.time() / 24 / 3600)

	dn, username = udm.create_user(disabled=disabled)
	oldattr = lo.get(dn)
	shadowMax = 7
	planned_expiry_day = today + delta
	shadowLastChange = planned_expiry_day - shadowMax
	print("testing: shadow password expiry in delta=%s days and account disabled=%s" % (delta, disabled))
	print("shadowLastChange: %s, today: %s, expires: %s" % (shadowLastChange, today, planned_expiry_day))
	lo.modify(dn, [
		['shadowMax', oldattr.get('shadowMax', []), [str(shadowMax).encode()]],
		['shadowLastChange', oldattr.get('shadowLastChange', []), [str(shadowLastChange).encode()]],
	])
	cmd = ['univention-ldapsearch', '-LLL', '-D', dn, '-x', '-w', 'univention', 'uid=dummy']
	print("Running: " " ".join(cmd))
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p.communicate()
	print("expecting: %s" % ("failure" if expected else "success"))
	print("result   : %s" % ("failure" if p.returncode else "success"))
	print(stdout.decode('utf-8', 'replace'))
	if expected == 0:
		assert p.returncode == 0, 'Login for account %s is expected to pass, but failed' % dn
	else:
		assert p.returncode != 0, 'Login for account %s is expected to fail, but passed' % dn


@pytest.mark.tags('apptest')
def test_country_names_uptodate():  # TODO: move into package unit test
	"""Test is list of country names in univention.admin.syntax.Country.choices is uptodate"""

	import pycountry

	import univention.admin.syntax as udm_syntax

	current_countries = sorted([(country.alpha_2, country.name) for country in pycountry.countries], key=lambda x: x[0])
	if dict(current_countries) != dict(udm_syntax.Country.choices):
		set_cc = set(current_countries)
		set_choices = set(udm_syntax.Country.choices)
		utils.fail("List in UDM and Debian differ: %r" % str(set_choices.symmetric_difference(set_cc)))


@pytest.mark.exposure('dangerous')
def test_displayName_update(stopped_s4_connector, udm):
	"""Check automatic update of displayName"""
	# bugs: [38385]
	print('>>> create user with default settings')
	firstname = uts.random_string()
	lastname = uts.random_string()
	userdn = udm.create_user(firstname=firstname, lastname=lastname, check_for_drs_replication=False)[0]
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname, lastname)]})

	print('>>> change firstname and then lastname')
	firstname2 = uts.random_string()
	lastname2 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, firstname=firstname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname2, lastname)]})
	udm.modify_object('users/user', dn=userdn, lastname=lastname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname2, lastname2)]})

	print('>>> create user with default settings')
	firstname = uts.random_string()
	lastname = uts.random_string()
	userdn = udm.create_user(firstname=firstname, lastname=lastname, check_for_drs_replication=False)[0]
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname, lastname)]})

	print('>>> change firstname and lastname in one step')
	firstname2 = uts.random_string()
	lastname2 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, firstname=firstname2, lastname=lastname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname2, lastname2)]})

	print('>>> create user with default settings')
	lastname = uts.random_string()
	userdn = udm.create_user(firstname='', lastname=lastname, check_for_drs_replication=False)[0]
	utils.verify_ldap_object(userdn, {'displayName': [lastname]})

	print('>>> change lastname')
	lastname2 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, lastname=lastname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [lastname2]})

	print('>>> create user with custom displayName')
	firstname = uts.random_string()
	lastname = uts.random_string()
	displayName = uts.random_string()
	userdn = udm.create_user(firstname=firstname, lastname=lastname, displayName=displayName, check_for_drs_replication=False)[0]
	utils.verify_ldap_object(userdn, {'displayName': [displayName]})

	print('>>> change firstname and then lastname')
	firstname2 = uts.random_string()
	lastname2 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, firstname=firstname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [displayName]})
	udm.modify_object('users/user', dn=userdn, lastname=lastname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [displayName]})

	print('>>> create user with custom displayName')
	firstname = uts.random_string()
	lastname = uts.random_string()
	displayName = uts.random_string()
	userdn = udm.create_user(firstname=firstname, lastname=lastname, displayName=displayName, check_for_drs_replication=False)[0]
	utils.verify_ldap_object(userdn, {'displayName': [displayName]})

	print('>>> change firstname and lastname in one step')
	firstname2 = uts.random_string()
	lastname2 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, firstname=firstname2, lastname=lastname2, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [displayName]})

	print('>>> change firstname and lastname in one step and set displayName')
	firstname3 = uts.random_string()
	lastname3 = uts.random_string()
	displayName3 = uts.random_string()
	udm.modify_object(
		'users/user', dn=userdn,
		firstname=firstname3,
		lastname=lastname3,
		displayName=displayName3,
		check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [displayName3]})

	print('>>> change displayName back to default')
	displayName4 = '%s %s' % (firstname3, lastname3)
	udm.modify_object(
		'users/user', dn=userdn,
		displayName=displayName4,
		check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': [displayName4]})

	print('>>> change firstname and lastname in one step')
	firstname4 = uts.random_string()
	lastname4 = uts.random_string()
	udm.modify_object('users/user', dn=userdn, firstname=firstname4, lastname=lastname4, check_for_drs_replication=False)
	utils.verify_ldap_object(userdn, {'displayName': ['%s %s' % (firstname4, lastname4)]})


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_slave')
def test_simpleauthaccount_authentication(udm, ucr):
	"""Check whether a simple-auth-account can authenticate against LDAP and UMC"""
	password = 'univention'
	dn, username = udm.create_ldap_user(password=password)
	utils.verify_ldap_object(dn)

	print('created user %r with dn=%r' % (username, dn))
	lo = univention.admin.uldap.access(binddn=dn, bindpw=password)
	assert dn in lo.lo.lo.whoami_s()
	assert username == lo.get(dn)['uid'][0].decode('utf-8')
	print('successfully did LDAP bind.')

	client = Client(ucr['hostname'], username, password)
	ldap_base = client.umc_get('ucr', ['ldap/base']).result
	print(ldap_base)
	assert ldap_base, 'Could not do any random UMC request'
	print('successfully did UMC authentication')


def test_check_removal_of_additional_group_membership(udm):
	"""Create users/user"""
	pytest.skip('FIXME??? #45842: git:fdfd446587c')

	groupdn = udm.create_object('groups/group', name=uts.random_string())
	userdn, uid = udm.create_user(groups=[groupdn])

	utils.verify_ldap_object(groupdn, {'uniqueMember': [userdn]})
	utils.verify_ldap_object(groupdn, {'memberUid': [uid]})
	udm.modify_object('users/user', dn=userdn, remove={'groups': [groupdn]})
	utils.verify_ldap_object(groupdn, {'uniqueMember': []})
	utils.verify_ldap_object(groupdn, {'memberUid': []})


def test_check_univentionDefaultGroup_membership_after_create(udm):
	"""Check default primary group membership after users/user create"""
	# from users/user: lookup univentionDefaultGroup
	lo = utils.get_ldap_connection()
	pos = position(lo.base)
	searchResult = lo.search(filter='(objectClass=univentionDefault)', base='cn=univention,' + pos.getDomain(), attr=['univentionDefaultGroup'])
	assert searchResult and searchResult[0][1], 'Test system is broken: univentionDefaultGroup value not found'
	groupdn = searchResult[0][1]['univentionDefaultGroup'][0].decode('utf-8')

	# lookup previous members for comparison
	searchResult = lo.search(base=groupdn, scope='base', attr=['uniqueMember', 'memberUid'])
	assert searchResult and searchResult[0][1], 'Test system is broken: univentionDefaultGroup object missing: %s' % groupdn
	uniqueMember = searchResult[0][1]['uniqueMember']
	memberUid = searchResult[0][1]['memberUid']

	# now create users/user object
	userdn, uid = udm.create_user(primaryGroup=groupdn)

	# and check if the object has been added to univentionDefaultGroup
	uniqueMember.append(userdn.encode('utf-8'))
	memberUid.append(uid.encode('utf-8'))
	utils.verify_ldap_object(groupdn, {'uniqueMember': uniqueMember})
	utils.verify_ldap_object(groupdn, {'memberUid': memberUid})


@pytest.mark.xfail(reason='Bug #27160 git:6d60cb602d7')
def test_from_primary_group_removal(udm):
	"""Create users/user"""

	lo = utils.get_ldap_connection()
	groupdn = udm.create_object('groups/group', name=uts.random_string())
	groupdn2 = udm.create_object('groups/group', name=uts.random_string())
	sid = lo.getAttr(groupdn, 'sambaSID', required=True)
	user = udm.create_user(primaryGroup=groupdn, groups=[groupdn2])[0]
	utils.verify_ldap_object(user, {'sambaPrimaryGroupSID': sid})

	utils.verify_ldap_object(groupdn, {'uniqueMember': [user]})
	udm.modify_object('groups/group', dn=groupdn, remove={'users': [user]})
	utils.verify_ldap_object(groupdn, {'uniqueMember': []})
	utils.verify_ldap_object(user, {'sambaPrimaryGroupSID': []})  # This fails, Bug #27160


def test_user_creation_password_policy(udm):
	"""Create users/user"""
	# bugs: [42148]

	policy = udm.create_object('policies/pwhistory', **{'name': uts.random_string(), 'expiryInterval': '90'})
	cn = udm.create_object('container/cn', **{'name': uts.random_string(), 'policy_reference': policy})
	user = udm.create_user(pwdChangeNextLogin=1, position=cn)[0]
	utils.verify_ldap_object(user, {'sambaPwdLastSet': ['0']})

	user = udm.create_user(pwdChangeNextLogin=1, policy_reference=policy)[0]
	utils.verify_ldap_object(user, {'sambaPwdLastSet': ['0']})


@pytest.mark.tags('apptest')
def test_pwdChangeNextLogin_and_password_set(udm):
	"""combination of --set pwdChangeNextLogin=0 --set password=foobar"""
	# bugs: [42015]

	userdn = udm.create_user(pwdChangeNextLogin=1)[0]
	utils.verify_ldap_object(userdn, {'shadowMax': ['1']})
	udm.modify_object('users/user', dn=userdn, pwdChangeNextLogin='0', password=uts.random_string())
	utils.verify_ldap_object(userdn, {'shadowMax': [], 'krb5PasswordEnd': []})


def test_user_univentionLastUsedValue(udm, ucr):
	"""Create users/user and check univentionLastUsedValue"""

	# Please note: modification of uidNumber is not allowed according to users/user.py --> not tested here
	luv_dn = 'cn=uidNumber,cn=temporary,cn=univention,%s' % (ucr.get('ldap/base'),)
	lo = univention.uldap.getAdminConnection()

	lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	user_dn = udm.create_user()[0]
	utils.verify_ldap_object(user_dn)
	lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	assert lastUsedValue_old != lastUsedValue_new, 'Create user with automatic uidNumber: univentionLastUsedValue did not change, but it should!'

	lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	uidNumber = str(random.randint(100000, 200000))
	user_dn = udm.create_user(uidNumber=uidNumber)[0]
	utils.verify_ldap_object(user_dn, expected_attr={'uidNumber': [uidNumber]})
	lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	assert lastUsedValue_old == lastUsedValue_new, 'Create user with specified uidNumber: univentionLastUsedValue did change, but it should not!'


@pytest.mark.exposure('dangerous')
@pytest.mark.xfail(reason='31317,48956')
def test_secretary_reference_update(udm):
	"""Create users/user"""
	# bugs: [31317,48956]
	user = udm.create_user()[0]
	sec = udm.create_user(secretary=user)[0]
	utils.verify_ldap_object(sec, {'secretary': [user]})

	print('1. modrdn: change username', user)
	user = udm.modify_object('users/user', dn=user, username=uts.random_username())
	utils.verify_ldap_object(sec, {'secretary': [user]})

	print('2. move into container', user)
	cn = udm.create_object('container/cn', name='test')
	user = udm.move_object('users/user', dn=user, position=cn)
	utils.verify_ldap_object(sec, {'secretary': [user]})

	print('3. rename container', user)
	cn_new = udm.modify_object('container/cn', dn=cn, name='test2')
	assert cn != cn_new
	udm._cleanup['users/user'].remove(user)
	user = user.replace(cn, cn_new)
	udm._cleanup['users/user'].append(user)
	cn = cn_new
	utils.verify_ldap_object(sec, {'secretary': [user]})

	print('4. move container', user)
	cn_new = udm.create_object('container/cn', name='test3')
	cn_new = udm.move_object('container/cn', dn=cn, position=cn_new)
	udm._cleanup['users/user'].remove(user)
	user = user.replace(cn, cn_new)
	udm._cleanup['users/user'].append(user)
	cn = cn_new
	utils.verify_ldap_object(sec, {'secretary': [user]})

	print('5. remove user', user)
	udm.remove_object('users/user', dn=user)
	utils.verify_ldap_object(sec, {'secretary': []})


def test_lookup_with_pagination(udm):
	"""Test serverctrls of ldap server"""
	pytest.skip('FIXME???  Bug #49638: git:63ba30a2040')

	from ldap.controls import SimplePagedResultsControl
	from ldap.controls.sss import SSSRequestControl
	name = uts.random_username()
	dns = [udm.create_user(username=name + str(i), wait_for_replication=False, check_for_drs_replication=False, wait_for=False)[0] for i in range(1, 8)]
	print(('Created users:', dns))

	univention.admin.modules.update()

	lo = univention.uldap.getMachineConnection()
	res = {}
	page_size = 2
	pctrl = SimplePagedResultsControl(True, size=page_size, cookie='')
	sctrl = SSSRequestControl(ordering_rules=['uid:caseIgnoreOrderingMatch'])
	users = univention.admin.modules.get('users/user')
	ctrls = [sctrl, pctrl]
	entries = []

	while True:
		entries.append([x.dn for x in users.lookup(None, lo, 'username=%s*' % (name,), serverctrls=ctrls, response=res)])
		print(('Found', entries[-1]))
		for control in res['ctrls']:
			if control.controlType == SimplePagedResultsControl.controlType:
				pctrl.cookie = control.cookie
		if not pctrl.cookie:
			break

		assert len(entries[-1]) == page_size

	found = []
	for entry in entries:
		found.extend(entry)

	assert sorted(found) == sorted(dns)


@pytest.mark.exposure('dangerous')
@pytest.mark.tags('apptest')
def test_udm_users_user_bcrypt_password(restart_slapd_after_test, udm, ucr):
	"""Test users/user and users/ldap bcrypt password handling"""
	# bugs: [52693]
	ucr.handler_set(['ldap/pw-bcrypt=true'])
	ucr.handler_set(['password/hashing/bcrypt=true'])
	utils.restart_slapd()
	udm.stop_cli_server()

	for module in ['users/user', 'users/ldap']:
		lo = utils.get_ldap_connection()
		name = uts.random_username()
		attr = dict(password='univention', username=name, lastname='test')
		dn = udm.create_object(module, wait_for_replication=True, check_for_drs_replication=True, wait_for=True, **attr)

		ldap_o = lo.search('uid={}'.format(name), attr=['userPassword', 'pwhistory'])[0]
		assert ldap_o[1]['userPassword'][0].startswith(b'{BCRYPT}'), ldap_o
		assert ldap_o[1]['pwhistory'][0].split()[0].startswith(b'{BCRYPT}'), ldap_o

		# authentication
		univention.admin.uldap.access(binddn=dn, bindpw='univention')
		with pytest.raises(univention.admin.uexceptions.authFail):
			univention.admin.uldap.access(binddn=dn, bindpw='univention1')

		# password change
		udm.modify_object(module, dn=dn, password='univention1')
		ldap_o = lo.search('uid={}'.format(name), attr=['userPassword', 'pwhistory'])[0]
		assert ldap_o[1]['userPassword'][0].startswith(b'{BCRYPT}'), ldap_o
		assert ldap_o[1]['pwhistory'][0].split()[0].startswith(b'{BCRYPT}'), ldap_o
		assert ldap_o[1]['pwhistory'][0].split()[1].startswith(b'{BCRYPT}'), ldap_o
		univention.admin.uldap.access(binddn=dn, bindpw='univention1')

		# password history
		# TODO how can we check univention.admin.uexceptions.pwalreadyused?
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object(module, dn=dn, password='univention1')

		# mixed password history
		ucr.handler_set(['password/hashing/bcrypt=false'])
		udm.stop_cli_server()
		udm.modify_object(module, dn=dn, password='univention2')
		ldap_o = lo.search('uid={}'.format(name), attr=['userPassword', 'pwhistory'])[0]
		assert not ldap_o[1]['userPassword'][0].startswith(b'{BCRYPT}'), ldap_o
		assert ldap_o[1]['pwhistory'][0].split()[0].startswith(b'{BCRYPT}'), ldap_o
		assert ldap_o[1]['pwhistory'][0].split()[1].startswith(b'{BCRYPT}'), ldap_o
		assert not ldap_o[1]['pwhistory'][0].split()[2].startswith(b'{BCRYPT}'), ldap_o
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object(module, dn=dn, password='univention')
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object(module, dn=dn, password='univention1')
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object(module, dn=dn, password='univention2')

		# and back
		ucr.handler_set(['password/hashing/bcrypt=true'])
		udm.stop_cli_server()
		udm.modify_object(module, dn=dn, password='univention4')
		ldap_o = lo.search('uid={}'.format(name), attr=['userPassword', 'pwhistory'])[0]
		assert ldap_o[1]['userPassword'][0].startswith(b'{BCRYPT}'), ldap_o

		# disable
		univention.admin.uldap.access(binddn=dn, bindpw='univention4')
		udm.modify_object(module, dn=dn, disabled='1')
		with pytest.raises(univention.admin.uexceptions.authFail):
			univention.admin.uldap.access(binddn=dn, bindpw='univention4')
		udm.modify_object(module, dn=dn, disabled='0')
		univention.admin.uldap.access(binddn=dn, bindpw='univention4')

		# 2a variant and cost factor
		ucr.handler_set(['password/hashing/bcrypt/prefix=2a'])
		ucr.handler_set(['password/hashing/bcrypt/cost_factor=7'])
		udm.stop_cli_server()
		udm.modify_object(module, dn=dn, password='univention5')
		ldap_o = lo.search('uid={}'.format(name), attr=['userPassword', 'pwhistory'])[0]
		assert ldap_o[1]['userPassword'][0].startswith(b'{BCRYPT}$2a$07$'), ldap_o
		univention.admin.uldap.access(binddn=dn, bindpw='univention5')


@pytest.mark.tags('apptest')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('module', ['users/user', 'users/ldap'])
def test_udm_users_ldap_mspolicy(udm, ucr, module):
	# bugs: [52446]
	"""Test mspolicy password functionality"""
	ucr.handler_set(['password/quality/mspolicy=true'])
	attr = {'name': uts.random_username(), 'pwQualityCheck': 'TRUE'}
	pol_dn = udm.create_object('policies/pwhistory', wait_for_replication=True, check_for_drs_replication=True, wait_for=True, **attr)
	utils.wait_for_replication_and_postrun()

	name = "%s_test1" % (uts.random_username())
	attr = {'password': 'Univention.1', 'username': name, 'lastname': 'test', 'policy_reference': pol_dn}
	dn = udm.create_object(module, wait_for_replication=True, check_for_drs_replication=True, wait_for=True, **attr)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object(module, dn=dn, password='univention')

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object(module, dn=dn, password='Uni1%s' % (name,))

	if module == 'users/user':
		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object(module, dn=dn, password='Uni.1test1')


@pytest.mark.tags('apptest')
@pytest.mark.exposure('dangerous')
def test_user_username_case_modification(udm):
	"""Test modifying the case of a character in a user name with a single operation"""
	# bugs: [54673]
	name = uts.random_username().lower()
	user, uid = udm.create_user(username=name)
	name = name[0].upper() + name[1:]

	dn = udm.modify_object('users/user', dn=user, username=name)
	assert dn.startswith("uid={}".format(name)), "The dn returned by `modify_object` does not contain the updated name"
	utils.verify_ldap_object(user, {'uid' : [name]})