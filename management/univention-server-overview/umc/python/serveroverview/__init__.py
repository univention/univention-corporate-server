#!/usr/bin/python3
#
# Univention Management Console module server-overview
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.modules as udm_modules
from univention.management.console.base import Base
from univention.management.console.config import ucr
from univention.management.console.ldap import get_machine_connection
from univention.management.console.modules.decorators import simple_response


class Instance(Base):

    @simple_response
    def query(self):
        udm_modules.update()
        lo, _po = get_machine_connection()
        servers = udm_modules.lookup('computers/computer', None, lo, filter='(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(!(univentionObjectFlag=docker)))', base=ucr['ldap/base'], scope='sub')

        result = [{
            "dn": i.dn,
            "hostname": i.info.get('name'),
            "domain": i.info.get('domain'),
            "ip": i.info.get('ip'),
            "version": i.info.get('operatingSystemVersion'),
            "serverRole": i.info.get('serverRole'),
        } for i in servers]
        return result
