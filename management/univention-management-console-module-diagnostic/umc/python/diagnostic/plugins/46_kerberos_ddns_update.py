#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2023 Univention GmbH
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

import contextlib
import subprocess
from typing import Iterator, Optional

import univention.lib.admember
from univention.config_registry import ucr_live as config_registry
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, util


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check kerberos authenticated DNS updates')
description = _('No errors occurred.')
run_descr = ['Checks if kerberos authenticated DNS updates']


class UpdateError(Exception):
    pass


class KinitError(UpdateError):
    def __init__(self, principal: str, keytab: Optional[str], password_file: Optional[str],) -> None:
        super(KinitError, self,).__init__(principal, keytab, password_file,)
        self.principal = principal
        self.keytab = keytab
        self.password_file = password_file

    def __str__(self) -> str:
        if self.keytab:
            msg = _('`kinit` for principal {princ} with keytab {tab} failed.')
        else:
            msg = _('`kinit` for principal {princ} with password file {file} failed.')
        return msg.format(princ=self.principal, tab=self.keytab, file=self.password_file,)


class NSUpdateError(UpdateError):
    def __init__(self, details: str, domainname: str,) -> None:
        super(NSUpdateError, self,).__init__(details, domainname,)
        self.details = details
        self.domainname = domainname

    def __str__(self) -> str:
        msg = _('`nsupdate` check for domain {domain} failed ({details}).')
        return msg.format(domain=self.domainname, details=self.details,)


@contextlib.contextmanager
def kinit(principal: str, keytab: Optional[str] = None, password_file: Optional[str] = None,) -> Iterator[None]:
    auth = '--keytab={tab}' if keytab else '--password-file={file}'
    cmd = ('kinit', auth.format(tab=keytab, file=password_file,), principal)
    MODULE.process('Running: %s' % (' '.join(cmd)))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        raise KinitError(principal, keytab, password_file,)
    else:
        yield
        subprocess.call(('kdestroy',))


def nsupdate(server: str, domainname: str,) -> None:
    process = subprocess.Popen(('nsupdate', '-g', '-t', '15'), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,)
    cmd_template = 'server {server}\nprereq yxdomain {domain}\nsend\nquit\n'
    cmd = cmd_template.format(server=server, domain=domainname,)
    MODULE.process("Running: 'echo %s | nsupdate -g -t 15'" % (cmd,))

    process.communicate(cmd.encode("utf-8"))
    if process.poll() != 0:
        MODULE.error('NS Update Error at %s %s' % (server, domainname))
        raise NSUpdateError(server, domainname,)


def get_dns_server(active_services: str,) -> Optional[str]:
    if config_registry.is_true('ad/member'):
        ad_domain_info = univention.lib.admember.lookup_adds_dc()
        server = ad_domain_info.get('DC IP')
    else:
        if set(active_services) >= {'Samba 4', 'DNS'}:
            server = "%(hostname)s.%(domainname)s" % config_registry
        else:
            # TODO: Memberserver in Samba 4 domain
            server = None
    return server


def check_dns_machine_principal(server: str, hostname: str, domainname: str,) -> None:
    with kinit(f'{hostname}$', password_file='/etc/machine.secret',):
        nsupdate(server, domainname,)


def check_dns_server_principal(hostname: str, domainname: str,) -> None:
    with kinit(f'dns-{hostname}', keytab='/var/lib/samba/private/dns.keytab',):
        nsupdate(hostname, domainname,)


def check_nsupdate(server: str,):
    hostname = config_registry.get('hostname')
    domainname = config_registry.get('domainname')

    try:
        check_dns_machine_principal(server, hostname, domainname,)
    except UpdateError as error:
        yield error

    if config_registry.get('samba4/role') == 'DC':
        try:
            check_dns_server_principal(hostname, domainname,)
        except UpdateError as error:
            yield error


def run(_umc_instance: Instance,) -> None:
    active_services = util.active_services()
    if not set(active_services) & {'Samba 4', 'Samba 3'}:
        return  # ddns updates are not possible

    try:
        server = get_dns_server(active_services)
        if not server:
            return
    except NSUpdateError:
        return  # ddns updates are not possible

    problems = list(check_nsupdate(server))
    if problems:
        ed = [_('Errors occurred while running `kinit` or `nsupdate`.')]
        ed.extend(str(error) for error in problems)
        MODULE.error('\n'.join(ed))
        raise Critical(description='\n'.join(ed))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
