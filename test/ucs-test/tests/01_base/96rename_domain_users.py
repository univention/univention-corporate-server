#!/usr/share/ucs-test/runner python3
## desc: Rename Domain Users
## tags:
##  - basic
##  - rename_default_account
##  - skip_admember
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
##  - domaincontroller_slave
##  - memberserver
## exposure: dangerous


import glob
import os
import re
import subprocess
import time

from ldap.dn import escape_dn_chars
from ldap.filter import filter_format

import univention.config_registry
import univention.testing.strings as uts
from univention.testing import utils
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.ucs_samba import wait_for_drs_replication
from univention.testing.utils import package_installed


def search_templates(old_group_name, new_group_name,):
    templates = glob.glob('/etc/univention/templates/info/*.info')
    file_content = []
    filter_pattern = re.compile('^(Multifile: |File: )')

    # find all template files by iterating over all referenced templates in the ucr *.info files
    for template in templates:
        with open(template) as content_file:
            # find all lines that start with File or Multifile and strip it to get the paths of the template files
            file_content += ['/' + filter_pattern.sub('', line,).strip() for line in content_file.readlines() if filter_pattern.match(line)]

    file_content = list(dict.fromkeys(file_content))
    for file in file_content:
        if not os.path.isfile(file):
            continue

        print(f'Checking template {file}')
        with open(file, 'rb',) as content_file:
            # /etc/security/limits.conf contains a comment about Domain Users which we will ignore.
            # But it must contain the new name of the default domainusers group
            content = content_file.read().decode('UTF-8', 'replace',)
            if file == "/etc/security/limits.conf":
                if new_group_name not in content:
                    print(content_file.read())
                    utils.fail(f'FAIL: New group name {new_group_name} not in security conffiles')
                continue
            if old_group_name in content:
                lines_containing = [line for line in content.splitlines() if old_group_name in line]
                print('\n'.join(lines_containing))
                utils.fail(f'FAIL: Old group name {old_group_name} still in file {file}')


def wait_for_ucr(iterations, group_name, ucr_test,):
    success = False
    for i in range(iterations):
        ucr_test.load()
        ucr_group = ucr_test.get('groups/default/domainusers', 'Domain Users',)
        if group_name != ucr_group:
            if i == iterations - 1:
                break
            time.sleep(15)
        else:
            print(f'UCR variable groups/default/domainusers is set correctly to {ucr_group}')
            success = True
            break
    return success, ucr_group


def test_rename_domain_users():
    with UCSTestConfigRegistry() as ucr_test:
        ucr_test.load()

        ldap_base = ucr_test.get('ldap/base')
        old_group_name = ucr_test.get('groups/default/domainusers', 'Domain Users',)
        old_group_dn = f"cn={escape_dn_chars(old_group_name)},cn=groups,{ldap_base}"

        new_group_name = uts.random_name()
        new_group_dn = f"cn={escape_dn_chars(new_group_name)},cn=groups,{ldap_base}"
        try:
            print('\n##################################################################')
            print(f'Renaming default domainusers group {old_group_name} to {new_group_name}')
            print('##################################################################\n')
            subprocess.call(['udm-test', 'groups/group', 'modify', '--dn=%s' % (old_group_dn), '--set', 'name=%s' % (new_group_name)])
            utils.wait_for_replication_and_postrun()

            # Check UCR Variable
            print('\n##################################################################')
            print(f'Checking if UCR Variable groups/default/domainusers is set to {new_group_name}')
            print('##################################################################\n')

            success, ucr_group = wait_for_ucr(10, new_group_name, ucr_test,)
            if not success:
                utils.fail(f'UCR variable groups/default/domainusers was set to {ucr_group} instead of {new_group_name}')

            # Search templates
            print('\n##################################################################')
            print('Search templates for old and new name of default domainusers group')
            print('##################################################################\n')
            search_templates(old_group_name, new_group_name,)
        finally:
            try:
                wait_for_drs_replication(filter_format('(sAMAccountName=%s)', (new_group_name,),))
            except Exception:
                # clean up even if the wait_for method fails and wait a bit if it terminated at the beginning
                time.sleep(10)
                pass
            if not package_installed('univention-samba4'):
                time.sleep(20)
            print('\n##################################################################')
            print('Cleanup')
            print('##################################################################\n')
            subprocess.call(['udm-test', 'groups/group', 'modify', '--dn=%s' % (new_group_dn), '--set', 'name=%s' % (old_group_name)])

            # wait until renaming is complete
            utils.wait_for_replication_and_postrun()
            success, ucr_group = wait_for_ucr(10, old_group_name, ucr_test,)
            if not success:
                univention.config_registry.handler_set(['groups/default/domainusers=Domain Users'])
                utils.fail(f'UCR variable groups/default/domainusers was set to {ucr_group} instead of {old_group_name}')


if __name__ == '__main__':
    test_rename_domain_users()
