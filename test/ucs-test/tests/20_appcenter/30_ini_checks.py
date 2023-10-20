#!/usr/share/ucs-test/runner python3
## desc: Checks if inis have meaningful/non-conflicting values
## tags: [basic,apptest]
## roles: [domaincontroller_master]
## exposure: safe

import subprocess
import sys
from configparser import NoOptionError, NoSectionError

from univention.appcenter.app_cache import Apps
from univention.appcenter.ini_parser import read_ini_file


returncode = 100

codes = {}
for app in Apps(locale='en').get_every_single_app():
    if app.id.endswith('-test'):
        print(f'Ignoring test App {app}')
        continue
    else:
        print('Checking %r' % app)
    # codes
    code = app.code
    if code:
        if code in codes:
            if codes[code] != app.id:
                print(f' FAIL: Code {code!r} has already been taken by {codes[code]!r}!')
                returncode = 1
        else:
            codes[code] = app.id
    # logo files
    if app.is_installed():
        ini_parser = read_ini_file(app.get_ini_file())
        for logo_attr in [
                'ApplianceLogo',
                'ApplianceBootsplashLogo',
                'ApplianceUmcHeaderLogo',
                'ApplianceWelcomeScreenLogo',
        ]:
            try:
                logo_name = ini_parser.get('Application', logo_attr)
            except (NoSectionError, NoOptionError):
                continue
            url = f'{app.get_server()}/meta-inf/{app.get_ucs_version()}/{app.id}/{logo_name}'
            stdout = subprocess.check_output(['curl', '-Is', url])
            if b'HTTP/1.1 200 OK' not in stdout.splitlines():
                print(f'FAIL: Could not find {url}')
                returncode = 1

sys.exit(returncode)
