#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

import cgi
import json
import re
import subprocess
import traceback

from ldif import LDIFParser

from univention.config_registry import ucr


LICENSE_UPLOAD_PATH = '/var/cache/univention-system-activation/license.ldif'

reg_exp_app_key = re.compile(r'^appliance/apps/(?P<id>[^/]*)/(?P<key>.*)$')


class LicenseLDIF(LDIFParser):

    def __init__(self, input, ucr):
        LDIFParser.__init__(self, input)
        self.ucr = ucr
        self.uuid = '00000000-0000-0000-0000-000000000000'

    def handle(self, dn, entry):
        if dn == f'cn=admin,cn=license,cn=univention,{self.ucr.get("ldap/base")}' and 'univentionLicenseKeyID' in entry and len(entry['univentionLicenseKeyID']) > 0:
            self.uuid = entry['univentionLicenseKeyID'][0].decode('utf-8')


class LdapLicenseFetchError(Exception):
    pass


def get_installed_apps():
    notify_apps = set()
    apps = []
    for key, value in ucr.items():
        m = reg_exp_app_key.match(key)
        if m:
            ucr_key = m.group('key')
            app_id = m.group('id')
            if ucr_key == 'notifyVendor' and ucr.is_true(key):
                notify_apps.add(app_id)
            elif ucr_key == 'version':
                apps.append([app_id, value])

    # only return apps that will notify the vendor
    apps = [iapp for iapp in apps if iapp[0] in notify_apps]
    return apps


def clean_license_output(out):
    # the output might contain the message of the day, as well
    # ... let's clean up that!
    ldif = []
    for line in out.split('\n'):
        if ldif and not line:
            # first empty line after the LDIF -> stop
            break
        matchesLdifStart = line.startswith('dn:')
        if not ldif and not matchesLdifStart:
            # we have not yet found the beginning of the LDIF -> inspect next line
            continue
        # this line is part of the LDIF -> append to LDIF ldifput
        ldif.append(line)
    return '\n'.join(ldif)


def application(environ, start_response):
    def _error(message, trace=None):
        return {
            'status': 500,
            'message': message,
            'traceback': trace,
            'location': '',
        }

    def _log(msg):
        print(msg, file=environ['wsgi.errors'])

    def _finish(status='200 OK', data=''):
        data = json.dumps(data).encode('UTF-8')
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(data))),
        ]
        start_response(status, headers)
        return [data]

    # output the license upon GET request
    if environ.get('REQUEST_METHOD') == 'GET':
        cmd = ['/usr/bin/sudo', '/usr/bin/univention-ldapsearch', '-LLL', 'objectClass=univentionLicense']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            out, _err = proc.communicate()
            if proc.returncode:
                raise LdapLicenseFetchError(f'{" ".join(cmd)} exited with {proc.returncode}:\n{out}')
            out = clean_license_output(out.decode('UTF-8'))
            return _finish(data=out)
        except subprocess.CalledProcessError as exc:
            _log(f'Failed to read license data from LDAP:\n{exc}')
            return _finish('500 Internal Server Error', _error(f'Failed to read license data from LDAP:\n{exc}'))
        except Exception as exc:
            return _finish('500 Internal Server Error', data=_error(str(exc), traceback.format_exc()))

    # block uploads that are larger than 1MB
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
    except (ValueError):
        request_body_size = -1
    if request_body_size < 0:
        return _finish('411 Length Required', {
            'success': False,
            'message': 'The content length was not specified.',
        })
    if request_body_size > 1024 * 100:
        return _finish('413 Request Entity Too Large', {
            'success': False,
            'message': 'The uploaded data is too large for a license file.',
        })

    # make sure the 'license' field exists in the request
    formdata = cgi.FieldStorage(environ=environ, fp=environ['wsgi.input'])
    if 'license' not in formdata:
        # no license has been uploaded :(
        return _finish('400 Bad Request', {
            'success': False,
            'message': 'No license information specified in request',
        })

    # the program logic below is oriented at the import function of the
    # UMC's UDM module
    with open(LICENSE_UPLOAD_PATH, 'w') as license_file:
        # Replace non-breaking space with a normal space
        # https://forge.univention.org/bugzilla/show_bug.cgi?id=30098
        license_data = formdata.getvalue('license', b'').decode('UTF-8').replace(chr(160), ' ')
        license_file.write(license_data)

    # import the uploaded license file
    try:
        subprocess.check_output(['/usr/bin/sudo', '/usr/sbin/univention-license-import', LICENSE_UPLOAD_PATH], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        _log(f'Failed to import the license:\n{exc.output}\n{exc}')
        return _finish('400 Bad Request', {
            'success': False,
            'message': exc.output.decode('utf-8', 'replace'),
        })

    ucr.load()

    # get uuid from ldif file, ucr['uuid/license'] is not yet up-to-date at this point
    license_ldif = LicenseLDIF(open(LICENSE_UPLOAD_PATH, 'rb'), ucr)
    license_ldif.parse()

    system_uuid = ucr.get('uuid/system')

    # disable system activation service (stop is executed with a small delay)
    # and answer request
    apps = get_installed_apps()
    subprocess.Popen(['/usr/bin/sudo', '/usr/sbin/univention-system-activation', 'stop'], stderr=subprocess.STDOUT)
    return _finish('200 OK', {
        'success': True,
        'uuid': license_ldif.uuid,
        'systemUUID': system_uuid,
        'apps': apps,
    })


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8398, application)
    srv.serve_forever()
