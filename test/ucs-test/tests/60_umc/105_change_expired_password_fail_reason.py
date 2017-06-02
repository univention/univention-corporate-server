#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test detection of changing expired password failure reason
## exposure: dangerous
## packages: [univention-management-console-server]

import pytest
from univention.config_registry import handler_set
from univention.testing import utils
from univention.lib.umc import Unauthorized

samba4_installed = utils.package_installed('univention-samba4')


@pytest.yield_fixture()
def enabled_password_quality_checks(lo, ldap_base, ucr):
	# TODO: from 07_expired_password: only if univention-samba4 is not installed
	dn = 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,%s' % (ldap_base,)
	old = lo.getAttr(dn, 'univentionPWQualityCheck')
	new = ['TRUE']
	lo.modify(dn, [('univentionPWQualityCheck', old, new)])
	handler_set(['password/quality/credit/lower=1', 'password/quality/credit/upper=1', 'password/quality/credit/other=1', 'password/quality/credit/digits=1'])
	yield
	lo.modify(dn, [('univentionPWQualityCheck', new, old)])


def test_password_changing_failure_reason(options, new_password, reason, udm, Client, random_string, Unauthorized):
	if samba4_installed and options and ('posix' not in options or 'kerberos' not in options):
		pytest.skip('Objects without posix&kerberos &(objectClass=posixAccount)(objectClass=krb5Principal) are not synced to S4 and therefore cannot change their password via UMC.')
	if not samba4_installed and options == ['posix']:
		pytest.skip('Objects with only posix in S3 enviroments cannot change their password via UMC.')
	print 'test_password_changing_failure_reason(%r, %r, %r)' % (options, new_password, reason)
	password = random_string()
	userdn, username = udm.create_user(options=options, password=password, pwdChangeNextLogin=1)
	client = Client()
	print 'change password from %r to %r' % (password, new_password)
	with pytest.raises(Unauthorized) as msg:
		client.umc_auth(username, password, new_password=new_password)
	assert msg.value.message == reason


def pytest_generate_tests(metafunc):
	if metafunc.function.__name__ != 'test_password_changing_failure_reason':
		return

	REASON_TOO_SHORT = "Changing password failed. The password is too short."
	REASON_TOO_SHORT_AT_LEAST_CHARACTERS = "Changing password failed. The password is too short. The password must consist of at least 8 characters."
	REASON_TOO_SIMPLE = "Changing password failed. The password is too simple."
	REASON_PALINDROME = "Changing password failed. The password is a palindrome."
	REASON_DICTIONARY = "Changing password failed. The password is based on a dictionary word."

	reasons = {
		REASON_TOO_SHORT: [],
		REASON_TOO_SHORT_AT_LEAST_CHARACTERS: [],
		REASON_TOO_SIMPLE: [],
		REASON_PALINDROME: [],
		REASON_DICTIONARY: [],
	}
	# pam_unix
	for option in [
		pytest.mark.xfail(condition=samba4_installed, reason="Don't know. FIXME!?", raises=Unauthorized)([]),
		pytest.mark.xfail(reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=44582', raises=Unauthorized)(['posix'])
	]:
		reasons[REASON_TOO_SHORT_AT_LEAST_CHARACTERS if samba4_installed else REASON_TOO_SHORT].append([option, 'Test'])
		reasons[REASON_TOO_SHORT].append([option, 'ana'])

	for option in [['posix', 'samba']]:
		reasons[REASON_TOO_SHORT if samba4_installed else REASON_TOO_SIMPLE].append([option, 'Test'])
		reasons[REASON_TOO_SHORT if samba4_installed else REASON_PALINDROME].append([option, 'ana'])

	# pam_krb5
	for option in [['kerberos', 'person']]:
		reasons[REASON_TOO_SIMPLE if samba4_installed else REASON_TOO_SHORT].append([option, 'Test'])
		reasons[REASON_PALINDROME if samba4_installed else REASON_TOO_SHORT].append([option, 'ana'])

	for option in [
		pytest.mark.xfail(condition=samba4_installed, reason="Don't know. FIXME!?", raises=Unauthorized)([]),
		pytest.mark.xfail(reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=44582', raises=Unauthorized)(['posix', 'samba']),
		['kerberos', 'person'],
		pytest.mark.xfail(reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=44582', raises=Unauthorized)(['posix'])
	]:
		reasons[REASON_TOO_SIMPLE if samba4_installed else REASON_DICTIONARY].append([option, 'chocolate'])

	data = [y + [reason] for reason, x in reasons.iteritems() for y in x]
	data = [xfail(x) for x in data]
	metafunc.parametrize('options,new_password,reason', data)


def xfail(set_):
	fails = [x for x in set_ if isinstance(x, type(pytest.mark.xfail()))]
	if fails:
		data = [x.args[0] if isinstance(x, type(pytest.mark.xfail())) else x for x in set_]
		set_ = pytest.mark.xfail(**fails[0].kwargs)(data)
	return set_
