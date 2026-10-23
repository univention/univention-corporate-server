#!/usr/share/ucs-test/runner python3
## desc: Shared control paths expand the current user when keywords are not shared
## tags: [apptest]
## exposure: dangerous
## packages:
##  - univention-mail-server
##  - univention-mail-dovecot
##  - univention-directory-manager-tools
## bugs: [59473]

# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
from pathlib import Path

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.config_registry import handler_set
from univention.testing import utils

from essential.mail import create_shared_mailfolder, get_dovecot_shared_folder_maildir, random_email


def main():
    with utils.AutoCallCommand(exit_cmd=['systemctl', 'restart', 'dovecot']):
        with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm:
            handler_set(['mail/dovecot/mailbox/share_keywords=no'])
            fqdn = '%(hostname)s.%(domainname)s' % ucr
            user_address = random_email()
            udm.create_user(set={
                'mailHomeServer': fqdn,
                'mailPrimaryAddress': user_address,
            })
            _folder_dn, folder_name, _folder_address = create_shared_mailfolder(
                udm, fqdn, mailAddress=True,
                user_permission=[f'"{user_address}" "all"'],
            )
            utils.wait_for_replication()
            subprocess.check_call(['systemctl', 'restart', 'dovecot'])

            control_path = subprocess.check_output([
                'doveadm', 'mailbox', 'path', '-u', user_address,
                '-t', 'control', folder_name,
            ], text=True).strip()
            expected_directory = Path(get_dovecot_shared_folder_maildir(folder_name)) / 'shared' / user_address
            assert Path(control_path).parent == expected_directory, (
                f'Expected control directory {expected_directory}, got {control_path}'
            )


if __name__ == '__main__':
    main()
