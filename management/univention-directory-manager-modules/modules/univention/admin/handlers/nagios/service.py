#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

"""|UDM| module for nagios services"""

import re
from logging import getLogger
from typing import List  # noqa: F401

import ldap
from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
import univention.admin.uexceptions
from univention.admin import configRegistry
from univention.admin.layout import Group, Tab


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin.handlers.nagios')
_ = translation.translate

module = 'nagios/service'
help_link = _('https://docs.software-univention.de/manual/5.0/en/monitoring/nagios.html#nagios-general')
default_containers = ['cn=nagios']

childs = False
short_description = _('Nagios service')
object_name = _('Nagios service')
object_name_plural = _('Nagios services')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']


options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionNagiosServiceClass'],
    ),
}

property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Service name'),
        syntax=univention.admin.syntax.string_numbers_letters_dots,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description=_('Service description'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
    ),
    'checkCommand': univention.admin.property(
        short_description=_('Plugin command'),
        long_description=_('Command name of Nagios plugin'),
        syntax=univention.admin.syntax.string,
        required=True,
    ),
    'checkArgs': univention.admin.property(
        short_description=_('Plugin command arguments'),
        long_description=_('Arguments of used Nagios plugin'),
        syntax=univention.admin.syntax.string,
    ),
    'useNRPE': univention.admin.property(
        short_description=_('Use NRPE'),
        long_description=_('Use NRPE to check remote services'),
        syntax=univention.admin.syntax.boolean,
    ),
    'assignedHosts': univention.admin.property(
        short_description=_('Assigned hosts'),
        long_description=_('Check services on these hosts'),
        syntax=univention.admin.syntax.nagiosHostsEnabledDn,
        multivalue=True,
    ),
}


layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('General Nagios service settings'), layout=[
            ["name", "description"],
            ["checkCommand", "checkArgs"],
            "useNRPE",
        ]),
    ]),
    Tab(_('Hosts'), _('Assigned hosts'), layout=[
        Group(_('Assigned hosts'), layout=[
            "assignedHosts",
        ]),
    ]),
]


mapping = univention.admin.mapping.mapping()

mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('checkCommand', 'univentionNagiosCheckCommand', None, univention.admin.mapping.ListToString)
mapping.register('checkArgs', 'univentionNagiosCheckArgs', None, univention.admin.mapping.ListToString)
mapping.register('useNRPE', 'univentionNagiosUseNRPE', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module

    def open(self):
        super(object, self).open()
        _re = re.compile(r'^([^.]+)\.(.+?)$')
        # convert host FQDN to host DN
        hostlist = []
        hosts = self.oldattr.get('univentionNagiosHostname', [])
        for host in [x.decode('UTF-8') for x in hosts]:
            # split into relDomainName and zoneName
            if host and _re.match(host) is not None:
                (relDomainName, zoneName) = _re.match(host).groups()
                # find correct dNSZone entry
                res = self.lo.search(filter=filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=%s)(aRecord=*))', (zoneName, relDomainName)))
                if not res:
                    log.debug('service.py: open: could not find dNSZone of %s', host)
                else:
                    # found dNSZone
                    filter = '(&(objectClass=univentionHost)'
                    for aRecord in [x.decode('ASCII') for x in res[0][1]['aRecord']]:
                        filter += filter_format('(aRecord=%s)', [aRecord])
                    filter += filter_format('(cn=%s))', [relDomainName])

                    # find dn of host that is related to given aRecords
                    res = self.lo.search(filter=filter)
                    if res:
                        hostlist.append(res[0][0])  # type: List[str]

        self['assignedHosts'] = hostlist

        self.save()

    def _ldap_modlist(self):
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

        # save assigned hosts
        if self.hasChanged('assignedHosts'):
            hostlist = []
            for hostdn in self.info.get('assignedHosts', []):
                try:
                    host = self.lo.get(hostdn, ['associatedDomain', 'cn'], required=True)
                    cn = host['cn'][0]  # type: bytes
                except (univention.admin.uexceptions.noObject, ldap.NO_SUCH_OBJECT):
                    raise univention.admin.uexceptions.valueError(_('The host "%s" does not exists.') % (hostdn,), property='assignedHosts')
                except KeyError:
                    raise univention.admin.uexceptions.valueError(_('The host "%s" is invalid, it has no "cn" attribute.') % (hostdn,), property='assignedHosts')

                domain = host.get('associatedDomain', [configRegistry.get("domainname").encode('ASCII')])[0]  # type: bytes
                hostlist.append(b"%s.%s" % (cn, domain))

            ml.insert(0, ('univentionNagiosHostname', self.oldattr.get('univentionNagiosHostname', []), hostlist))

        return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
