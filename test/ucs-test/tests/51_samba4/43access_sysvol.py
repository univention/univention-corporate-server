#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Accessing sysvol with smbclient"
## exposure: safe
## tags: [SKIP-UCSSCHOOL,apptest]
## packages:
##  - univention-samba4
## roles:
## - domaincontroller_master
## - domaincontroller_backup
## - domaincontroller_slave

import os
from subprocess import STDOUT, call, check_output

import pytest

from univention.testing import udm as _udm, utils


@pytest.fixture(scope='module')
def s4_domainname():
    return check_output("samba-tool domain info 127.0.0.1 | sed -n 's/^Domain *: //p'", shell=True).decode('UTF-8').strip()  # Samba's idea of spelling


@pytest.fixture(scope='module')
def user():
    with _udm.UCSTestUDM() as udm:
        _userdn, username = udm.create_user(password='univention', firstname='Max', lastname='Muster', organisation='firma.de_GmbH')  # mailPrimaryAddress='...@...'

        call(['univention-ldapsearch', f'uid={username}'])
        call(['univention-s4search', f'sAMAccountName={username}'])
        yield username


def test_put_a_file_on_sysvol_as_administrator(s4_domainname):
    account = utils.UCSTestDomainAdminCredentials()
    cmd = ['smbclient', '//localhost/sysvol', f"-U{account.username}%{account.bindpw}", '-c', f"put /etc/hosts {s4_domainname}/t1"]
    rc = call(cmd)
    assert rc == 0, cmd


def test_access_the_folder_policies_on_sysvol_as_a_user(user, s4_domainname):
    cmd = ['smbclient', '//localhost/sysvol', f"-U{user}%{'univention'}", '-c', f"ls {s4_domainname}/Policies"]
    rc = call(cmd)
    assert rc == 0, cmd


def test_put_a_file_in_the_folder_policies_on_sysvol_as_a_user(user, s4_domainname):
    cmd = ['smbclient', '//localhost/sysvol', f"-U{user}%{'univention'}", '-c', f"put /etc/hosts {s4_domainname}/t1"]
    rc = call(cmd)
    assert rc == 1, cmd


def test_replace_gpt_ini_of_the_default_domain_policies_as_a_user(s4_domainname, user):
    cmd = ['smbclient', '//localhost/sysvol', f"-U{user}%{'univention'}", '-c', f"cd {s4_domainname}/Policies/{{31B2F340-016D-11D2-945F-00C04FB984F9}};get GPT.INI /tmp/GPT.INI;put /tmp/GPT.INI GPT.INI"]
    rc = call(cmd)
    assert rc == 1, cmd


def test_remove_gpt_ini_of_the_default_domain_policies_as_a_user(s4_domainname, user):
    cmd = ['smbclient', '//localhost/sysvol', f"-U{user}%{'univention'}", '-c', f"cd {s4_domainname}/Policies/{{31B2F340-016D-11D2-945F-00C04FB984F9}};rm GPT.INI"]
    output = check_output(cmd, env=dict(os.environ, LANG='C'), stderr=STDOUT).decode('UTF-8', 'replace')
    assert "NT_STATUS_ACCESS_DENIED deleting remote file" in output, (cmd, output)


def test_put_a_file_in_the_machine_folder_of_the_default_domain_policies_as_a_user(s4_domainname, user):
    cmd = ['smbclient', '//localhost/sysvol', f"-U{user}%{'univention'}", '-c', f"put /etc/hosts {s4_domainname}/Policies/{{31B2F340-016D-11D2-945F-00C04FB984F9}}/MACHINE/hosts"]
    rc = call(cmd)
    assert rc == 1, cmd


def test_check_that_the_file_ownership_of_the_default_domain_policy_is_okay(s4_domainname):
    cmd = ['stat', '--printf', '%U', f"/var/lib/samba/sysvol/{s4_domainname}/Policies/{{31B2F340-016D-11D2-945F-00C04FB984F9}}"]
    output = check_output(cmd, stderr=STDOUT).decode('UTF-8', 'replace').strip()
    account = utils.UCSTestDomainAdminCredentials()
    assert account.username == output, cmd
