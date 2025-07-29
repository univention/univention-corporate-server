#
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.udm import UDM, NoObject


def handler(configRegistry, changes):
    if configRegistry.get('server/role') != "domaincontroller_master":
        print('self-service-links module can only run on role Primary Directory Node')
        return

    udm = UDM.machine().version(3)
    for key, (_old, new) in changes.items():
        activated = configRegistry.is_true(None, value=new)
        name = {
            'umc/self-service/profiledata/enabled': 'self-service-my-profile',
            'umc/self-service/protect-account/backend/enabled': 'self-service-protect-account',
            'umc/self-service/passwordreset/backend/enabled': 'self-service-password-forgotten',
            'umc/self-service/account-registration/backend/enabled': 'self-service-create-account',
            'umc/self-service/account-verification/backend/enabled': 'self-service-verify-account',
            'umc/self-service/service-specific-passwords/backend/enabled': 'self-service-service-specific-passwords',
        }.get(key)
        if not name:
            continue
        try:
            obj = udm.get('portals/entry').get_by_id(name)
        except NoObject:
            continue
        obj.props.activated = activated
        obj.save()
        print(obj.dn, 'active state set to', activated)
