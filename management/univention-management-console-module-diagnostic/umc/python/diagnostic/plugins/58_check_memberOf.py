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

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning, util


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check LDAP attribute memberOf')
description = _('Check whether the LDAP overlay memberOf is locally activated.')
warning_message = _('The "memberOf" group membership attribute is not available in the LDAP server on this host. This feature is activated by default in new installations since UCS version 4.3-0, and serveral services depend on it. This feature will be a prerequisite in future UCS releases. You may want to consider activating the memberOf feature for the LDAP server according to:')
links = [{
    'name': 'activateMemberOf',
    'href': _('https://help.univention.com/t/memberof-attribute-group-memberships-of-user-and-computer-objects/6439'),
    'label': _('Activate the memberOf LDAP overlay'),
}]


def run(_umc_instance: Instance) -> None:
    if util.is_service_active('LDAP') and not ucr.is_true('ldap/overlay/memberof'):
        MODULE.error(warning_message)
        raise Warning(description=warning_message)


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
