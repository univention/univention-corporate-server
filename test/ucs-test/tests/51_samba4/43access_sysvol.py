#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s
## desc: "Accessing sysvol with smbclient"
## exposure: safe
## tags: [SKIP-UCSSCHOOL,apptest]
## packages:
##  - univention-samba4
## roles:
## - domaincontroller_master
## - domaincontroller_backup
## - domaincontroller_slave

from subprocess import call, check_output

import pytest

from univention.testing import udm as _udm, utils


@pytest.fixture(scope='module')
def s4_domainname():
	return check_output("samba-tool domain info 127.0.0.1 | sed -n 's/^Domain *: //p'", shell=True).decode('UTF-8').strip()  # Samba's idea of spelling


@pytest.yield_fixture(scope='module')
def user():
	with _udm.UCSTestUDM() as udm:
		userdn, username = udm.create_user(password='univention', firstname='Max', lastname='Muster', organisation='firma.de_GmbH')  # mailPrimaryAddress='...@...'

		call(['univention-ldapsearch', 'uid=%s' % (username,)])
		call(['univention-s4search', 'sAMAccountName=%s' % (username,)])
		yield username


def test_put_a_file_on_sysvol_as_administrator(s4_domainname):
	account = utils.UCSTestDomainAdminCredentials()
	print('smbclient //localhost/sysvol -U"{}%{}" -c "put /etc/hosts {}/t1"'.format(account.username, account.bindpw, s4_domainname))
	rc = call('smbclient //localhost/sysvol -U"{}%{}" -c "put /etc/hosts {}/t1"'.format(account.username, account.bindpw, s4_domainname), shell=True)
	assert rc == 0, "Could not put file on sysvol as Administrator"


def test_access_the_folder_policies_on_sysvol_as_a_user(user, s4_domainname):
	rc = call('smbclient //localhost/sysvol -U"{}%{}" -c "ls {}/Policies"'.format(user, 'univention', s4_domainname), shell=True)
	assert rc == 0, "Could not access Policies on sysvol as a user"


def test_put_a_file_in_the_folder_policies_on_sysvol_as_a_user(user, s4_domainname):
	rc = call('smbclient //localhost/sysvol -U"{}%{}" -c "put /etc/hosts {}/t1"'.format(user, 'univention', s4_domainname), shell=True)
	assert rc == 1, "Successfully put a file on sysvol as a user"


def test_replace_gpt_ini_of_the_default_domain_policies_as_a_user(s4_domainname, user):
	cmd = 'smbclient //localhost/sysvol -U"%s%%%s" -c "cd %s/Policies/{31B2F340-016D-11D2-945F-00C04FB984F9};get GPT.INI /tmp/GPT.INI;put /tmp/GPT.INI GPT.INI"' % (user, 'univention', s4_domainname)
	rc = call(cmd, shell=True)
	assert rc == 1, "GPT.ini of the default domain policies could be replaced"


def test_remove_gpt_ini_of_the_default_domain_policies_as_a_user(s4_domainname, user):
	cmd = 'LANG=C smbclient //localhost/sysvol -U"%s%%%s" -c "cd %s/Policies/{31B2F340-016D-11D2-945F-00C04FB984F9};rm GPT.INI" 2>&1; true' % (user, 'univention', s4_domainname)
	output = check_output(cmd, shell=True).decode('UTF-8', 'replace')
	print(output)
	assert "NT_STATUS_ACCESS_DENIED deleting remote file" in output, "GPT.ini of the default domain policies could be removed"


def test_put_a_file_in_the_machine_folder_of_the_default_domain_policies_as_a_user(s4_domainname, user):
	cmd = 'smbclient //localhost/sysvol -U"%s%%%s" -c "put /etc/hosts %s/Policies/{31B2F340-016D-11D2-945F-00C04FB984F9}/MACHINE/hosts"' % (user, 'univention', s4_domainname)
	rc = call(cmd, shell=True)
	assert rc == 1, "Successfully put a file in the machines folder of the default domain policy as a user"


def test_check_that_the_file_ownership_of_the_default_domain_policy_is_okay(s4_domainname):
	cmd = 'stat --printf "%%U" "/var/lib/samba/sysvol/%s/Policies/{31B2F340-016D-11D2-945F-00C04FB984F9}" 2>&1' % (s4_domainname,)
	output = check_output(cmd, shell=True).decode('UTF-8', 'replace').strip()
	account = utils.UCSTestDomainAdminCredentials()
	assert account.username == output, "The file ownership of the default domain policy is not okay"
