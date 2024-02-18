# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

from vminstall.utils import copy_through_ssh, execute_through_ssh


class Test00Checks(object):

    def test_run_checks(self, ip_address, password):
        this_dir, _ = os.path.split(__file__)
        copy_through_ssh(password, os.path.join(this_dir, os.pardir, os.pardir, 'utils', 'utils.sh'), 'root@%s:/root/' % (ip_address,))
        execute_through_ssh(password, '. utils.sh && install_ucs_test', ip_address)
        execute_through_ssh(password, '. utils.sh && run_minimal_tests', ip_address)
        copy_through_ssh(password, 'root@%s:/root/test-reports' % (ip_address,), '.')
