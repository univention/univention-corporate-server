# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| licence data."""

UCS = ['UCS', 'Univention Corporate Server']


class Attributes:

    def __init__(self, required_license=None, options={}):
        self.required_license = required_license
        self._options = options

    def options(self, license_type):
        if not self._options:
            return ()
        if not isinstance(license_type, list):
            license_type = list(license_type)
        license_type.sort()

        for key in self._options.keys():
            skey = sorted(key)
            if license_type == skey:
                return self._options[key]

        return ()

    def valid(self, license_type):
        if not isinstance(license_type, list):
            license_type = list(license_type)

        if not self.required_license:
            return True

        if isinstance(self.required_license, list):
            return any(rl in license_type for rl in self.required_license)
        else:
            return self.required_license in license_type


def moreGroupware(license):
    return False, (license.compare(license.licenses[license.ACCOUNT], license.licenses[license.GROUPWARE]) != 1)


# Examples:
#    'computers/ipmanagedclient': Attributes( UCS + [ 'OEM1'] ),
#    'computers/domaincontroller_master': Attributes( UCS + ['OEM2'] ,options =
#                {
#                    ( UCS, ) : ( ( 'nagios', (False, False) ), ),
#                    ( OEM2 ) : ( ( 'nagios', (True, False) ), ),
#                    ( UCS + ['OEM2'] ) : ( ( 'nagios', (False, False) ), ),
#                } ),


modules = {}
