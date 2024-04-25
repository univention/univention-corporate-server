#!/usr/share/ucs-test/runner python3
## desc: Checks if apps can be re-installed after uninstalling
## tags: [appuninstalltest]
## roles-not: [basesystem]
## packages:
##   - univention-directory-manager-tools
##   - univention-management-console-module-appcenter
## exposure: dangerous
## versions:
##  4.4-5: skip

# skip this, we now install the app via the cfg file

from univention.appcenter.actions import get_action
from univention.appcenter.log import log_to_stream
from univention.testing import utils

from appcenteruninstalltest import get_requested_apps


log_to_stream()
account = utils.UCSTestDomainAdminCredentials()
install = get_action('install')
info = get_action('info')

apps = []
for app in get_requested_apps():
    print('Checking', app)
    if not app._allowed_on_local_server():
        print('Not allowed ... skipping')
        continue
    apps.append(app)

if not install.call(app=apps, noninteractive=True, pwdfile=account.pwdfile, username=account.username):
    info.call()
    utils.fail('Failed to re-install apps')
