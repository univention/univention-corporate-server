#!/usr/bin/python3
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

import logging
import re
import socket

import paramiko

from univention.admin import modules, uldap
from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Critical, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('SSH connection to UCS server failed!')

FQDN = "%(hostname)s.%(domainname)s" % ucr
run_descr = ['This can be checked by running:  univention-ssh /etc/machine.secret "%s$@%s" echo OK' % (ucr["hostname"], FQDN)]


class IgnorePolicy(paramiko.MissingHostKeyPolicy):

    def missing_host_key(self, client, hostname, key,):
        pass


def run(_umc_instance: Instance,) -> None:
    # Now a workaround for paramico logging to connector-s4.log
    # because one of the diagnostic plugins instantiates s4connector.s4.s4()
    # which initializes univention.debug2, which initializes logging.basicConfig
    logger = logging.getLogger("paramiko")
    logger.setLevel(logging.CRITICAL)

    try:
        lo, position = uldap.getMachineConnection(ldap_master=False)
    except Exception as err:
        raise Warning(str(err))

    modules.update()
    ucs_hosts = []
    roles = [
        'computers/domaincontroller_backup',
        'computers/domaincontroller_master',
        'computers/domaincontroller_slave',
        'computers/memberserver']
    for role in roles:
        udm_obj = modules.get(role)
        modules.init(lo, position, udm_obj,)
        for host in udm_obj.lookup(None, lo, 'cn=*',):
            if 'docker' in host.oldattr.get('univentionObjectFlag', [],):
                continue
            if not host.get('ip'):
                continue
            host.open()
            ucs_hosts.append(host['name'])

    with open('/etc/machine.secret') as fd:
        password = fd.read().strip()

    gen_msg = _('The ssh connection to at least one other UCS server failed. ')
    gen_msg += _('The following list shows the affected remote servers and the reason for the failed ssh connection:')

    key_msg = _('Host key for server does not match')
    key_info = _('The ssh host key of the remote server has changed (maybe the host was reinstalled). ')
    key_info += _('Please repair the host key of the remote server in /root/.ssh/known_hosts on %(fqdn)s.')

    auth_msg = _('Machine authentication failed')
    auth_info = _('Login to the remote server with the uid %(uid)s and the password from /etc/machine.secret failed. ')
    auth_info += _('Please check /var/log/auth.log on the remote server for further information.')

    bad = {}
    key_failed = False
    auth_failed = False
    data = {
        "fqdn": FQDN,
        "uid": ucr['hostname'] + '$',
        "hostname": ucr['hostname'],
    }

    for host in ucs_hosts:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(IgnorePolicy())

        fqdn = host + '.' + ucr['domainname']
        try:
            client.connect(fqdn, port=22, username=ucr['hostname'] + '$', password=password, timeout=2, banner_timeout=2, allow_agent=False,)
            client.close()
        except paramiko.BadHostKeyException:
            bad[fqdn] = key_msg + '!'
            key_failed = True
        except paramiko.BadAuthenticationType:
            bad[fqdn] = auth_msg + '!'
            auth_failed = True
        except (paramiko.SSHException, socket.timeout):
            # ignore if host is not reachable and other ssh errors
            pass
        except Exception as err:
            bad[fqdn] = str(err)
    if bad:
        msg = gen_msg
        msg += '\n\n'
        for host in bad:
            msg += '%s - %s\n' % (host, bad[host])
        if key_failed:
            msg += '\n' + key_msg + ' - ' + key_info + '\n'
        if auth_failed:
            msg += '\n' + auth_msg + ' - ' + auth_info + '\n'
        msg += '\n'
        log_msg = msg.splitlines()
        for line in log_msg:
            if not re.match(r'^\s*$', line,):
                MODULE.error("%s" % line)
        MODULE.error("%s" % data)
        raise Critical(msg % data)


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
