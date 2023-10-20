#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test register() API of UCR modules
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## bugs: [30127]
## packages:
##   - univention-config

import json
import subprocess

from univention.testing.debian_package import DebianPackage
from univention.testing.strings import random_string, random_version
from univention.testing.ucr import UCSTestConfigRegistry


UCR_MODULE = '''
import json
def handler(configRegistry, changes):
    print('####' + json.dumps(changes) + '####')
'''

UCR_INFO = '''
Type: module
Module: %s.py
Variables: %s/.*$
'''


def test_ucr_register_api():
    package_name = random_string()
    package_version = random_version()
    package = DebianPackage(name=package_name, version=package_version)
    package.create_debian_file_from_buffer(f'/etc/univention/templates/modules/{package_name}.py', UCR_MODULE)
    package.create_debian_file_from_buffer(f'/etc/univention/templates/info/{package_name}.info', UCR_INFO % (package_name, package_name))
    try:
        package.build()
        package.install()

        with UCSTestConfigRegistry():
            subprocess.call(['ucr', 'set', f'{package_name}/foo=bar'])

            changes = json.loads(subprocess.check_output(['ucr', 'register', package_name]).split(b'####')[1])
            expected = {
                f'{package_name}/.*$': [None, None],
                f'{package_name}/foo': [None, 'bar'],
            }
            assert changes == expected, changes

            changes = json.loads(subprocess.check_output(['ucr', 'set', f'{package_name}/foo=blub']).split(b'####')[1])
            expected = {f'{package_name}/foo': ['bar', 'blub']}
            assert changes == expected, changes
    finally:
        package.uninstall()
        package.remove()


if __name__ == '__main__':
    test_ucr_register_api()
