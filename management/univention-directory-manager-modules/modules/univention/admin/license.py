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

"""|UDM| wrapper around :py:mod:`univention.license` that translates error codes to exceptions"""

import collections
from logging import getLogger

from ldap.filter import filter_format

import univention.admin.filter
import univention.admin.license_data as licenses
import univention.admin.localization
import univention.admin.modules
import univention.admin.uexceptions
import univention.license
from univention.admin._ucr import configRegistry
from univention.lib.misc import custom_username


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention/admin')
_ = translation.translate

_license = None

LDAP_FILTER_normal_user_account = '(univentionObjectType=users/user)'
LDAP_FILTER_account_not_disabled = '(!(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'
LDAP_FILTER_managedclients = '(|(objectClass=univentionWindows)(objectclass=univentionUbuntuClient)(objectClass=univentionLinuxClient)(objectClass=univentionCorporateClient)(objectClass=univentionMacOSClient))'


def ldap_filter_not_objectflag(flag_string_list):
    ldap_filter_parts = []
    for flag_string in flag_string_list:
        ldap_filter_parts.append(filter_format('(univentionObjectFlag=%s)', [flag_string]))
    if not ldap_filter_parts:
        return ''
    elif len(ldap_filter_parts) == 1:
        return '(!%s)' % ''.join(ldap_filter_parts)
    else:
        return '(!(|%s))' % ''.join(ldap_filter_parts)


user_exclude_objectflags = ['temporary', 'functional', 'hidden']
managedclient_exclude_objectflags = []
if configRegistry.is_true('ad/member'):
    user_exclude_objectflags.append('synced')
    managedclient_exclude_objectflags.append('synced')


class License:
    (ACCOUNT, CLIENT, DESKTOP, GROUPWARE) = range(4)
    (USERS, SERVERS, MANAGEDCLIENTS, CORPORATECLIENTS, VIRTUALDESKTOPUSERS, VIRTUALDESKTOPCLIENTS) = range(6)

    SYSACCOUNTS = 5

    def __init__(self):
        if _license:
            raise Exception('never create this object directly')
        self.new_license = False
        self.disable_add = 0
        self._expired = False
        self.endDate = None
        self.oemProductTypes = []
        self.licenseBase = None
        self.types = []
        self.version = '1'
        self.searchResult = None
        self.sysAccountNames = (
            custom_username('Administrator'),
            'krbkeycloak',
            'join-backup',
            'join-slave',
            'spam',
            'oxadmin',
            'krbtgt',
            'pcpatch',  # opsi app
            'opsiconfd',  # opsi app
            custom_username('Guest'),
            'dns-*',
            'http-%s' % configRegistry.get('hostname'),
            'http-proxy-%s' % configRegistry.get('hostname'),
            'zarafa-%s' % configRegistry.get('hostname'),
            custom_username('SBSMonAcct'),  # SBS account
            custom_username('Network Administrator'),  # SBS role
            custom_username('Standard User'),  # SBS role
            custom_username('WebWorkplaceTools'),  # SBS role "Standard User with administration links"
            'IUSR_WIN-*',  # IIS account
        )
        self.sysAccountsFound = 0
        self.licenses = {
            '1': {
                # Version 1 till UCS 3.1
                License.ACCOUNT: None, License.CLIENT: None,
                License.DESKTOP: None, License.GROUPWARE: None,
            },
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: None, License.SERVERS: None,
                License.MANAGEDCLIENTS: None, License.CORPORATECLIENTS: None,
            },
        }
        self.real = {
            '1': {
                # Version 1 till UCS 3.1
                License.ACCOUNT: 0, License.CLIENT: 0,
                License.DESKTOP: 0, License.GROUPWARE: 0,
            },
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: 0, License.SERVERS: 0,
                License.MANAGEDCLIENTS: 0, License.CORPORATECLIENTS: 0,
            },
        }
        self.names = {
            '1': {
                # Version 1 till UCS 3.1
                License.ACCOUNT: 'Accounts', License.CLIENT: 'Clients',
                License.DESKTOP: 'Desktops', License.GROUPWARE: 'Groupware Accounts',
            },
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: 'Users', License.SERVERS: 'Servers',
                License.MANAGEDCLIENTS: 'Managed Clients', License.CORPORATECLIENTS: 'Corporate Clients',
            },
        }
        self.keys = {
            '1': {
                # Version 1 till UCS 3.1
                License.ACCOUNT: 'univentionLicenseAccounts',
                License.CLIENT: 'univentionLicenseClients',
                License.DESKTOP: 'univentionLicenseuniventionDesktops',
                License.GROUPWARE: 'univentionLicenseGroupwareAccounts',
            },
            '2': {
                # Version 1 till UCS 3.1
                License.USERS: 'univentionLicenseUsers',
                License.SERVERS: 'univentionLicenseServers',
                License.MANAGEDCLIENTS: 'univentionLicenseManagedClients',
                License.CORPORATECLIENTS: 'univentionLicenseCorporateClients',
            },
        }
        self.filters = {
            '1': {
                # Version 1 till UCS 3.1
                License.ACCOUNT: '(&(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=sambaSamAccount))(!(uidNumber=0))(!(uid=*$))(!(&(shadowExpire=1)(krb5KDCFlags=254)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))))',
                License.CLIENT: '(|(objectClass=univentionThinClient)(objectClass=univentionClient)(objectClass=univentionMobileClient)(objectClass=univentionWindows)(objectClass=univentionMacOSClient))',
                License.DESKTOP: '(|(objectClass=univentionThinClient)(&(objectClass=univentionClient)(objectClass=posixAccount))(objectClass=univentionMobileClient))',
                License.GROUPWARE: '(&(objectclass=kolabInetOrgPerson)(kolabHomeServer=*)(!(&(shadowExpire=1)(krb5KDCFlags=254)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))))',
            },
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: '(&%s)' % ''.join([LDAP_FILTER_normal_user_account, ldap_filter_not_objectflag(user_exclude_objectflags), LDAP_FILTER_account_not_disabled]),
                License.SERVERS: '(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(!(univentionObjectFlag=docker)))',
                # Managed Clients, Windows Clients, Ubuntu Clients, Linux Clients, MaxOS X Clients
                License.MANAGEDCLIENTS: '(&%s)' % ''.join([LDAP_FILTER_managedclients, ldap_filter_not_objectflag(managedclient_exclude_objectflags)]),
                License.CORPORATECLIENTS: '(&(objectclass=univentionCorporateClient))',
            },
        }
        self.__selected = False

    def _load_license_via_c_module(self, module):
        return 0

    def _load_license_via_python(self, module, lo):
        # Try to set the version even if the license load was not successful
        self.searchResult = lo.search(filter=filter_format('(&(objectClass=univentionLicense)(univentionLicenseModule=%s))', [module]))
        if self.searchResult:
            self.version = self.searchResult[0][1].get('univentionLicenseVersion', [b'1'])[0].decode('ASCII')

    def select(self, module, lo=None):
        if not self.__selected:
            self.error = self._load_license_via_c_module(module)
            if self.error != 0 and lo:
                self._load_license_via_python(module, lo)
                self.set_values(lo, module)

            self.__raiseException()
            self.__selected = True

    def isValidFor(self, module):
        log.debug('LICENSE: check license for module %s, %r', module, self.types)
        if module in licenses.modules:
            mlics = licenses.modules[module]
            log.debug('LICENSE: module license: %r', mlics)
            # empty list -> valid
            return mlics.valid(self.types)
        # unknown modules are always valid (e.g. customer modules)
        return True

    def modifyOptions(self, mod):
        if mod in licenses.modules:
            opts = licenses.modules[mod].options(self.types)
            if opts:
                module = univention.admin.modules.modules[mod]
                if module and hasattr(module, 'options'):
                    log.debug('modifyOptions: %r', opts)
                    for opt, val in opts:
                        if callable(val):
                            val = val(self)
                        if isinstance(val, collections.Sequence):
                            module.options[opt].disabled, module.options[opt].default = val
                        log.debug('modifyOption: %s, %d, %d', opt, module.options[opt].disabled, module.options[opt].default)

    def checkModules(self):
        deleted_mods = []
        for mod in univention.admin.modules.modules.keys():
            # remove module if valid license is missing
            if self.isValidFor(mod):
                log.debug('update: License is valid for module %s!!', mod)
                # check module options according to given license type
                self.modifyOptions(mod)
            else:
                log.debug('update: License is NOT valid for module %s!!', mod)
                del univention.admin.modules.modules[mod]
                deleted_mods.append(mod)

        # remove child modules that were deleted because of an invalid license
        for mod in univention.admin.modules.modules.values():
            if hasattr(mod, 'childmodules'):
                new = []
                for child in mod.childmodules:
                    if child in deleted_mods:
                        continue
                    new.append(child)
                mod.childmodules = new

        # remove operations for adding or modifying if license is expired
        if self._expired:
            for mod in univention.admin.modules.modules.values():
                if hasattr(mod, 'operations'):
                    try:
                        mod.operations.remove('add')
                    except Exception:
                        pass
                    try:
                        mod.operations.remove('edit')
                    except Exception:
                        pass

    def __cmp(self, x, y):
        """
        Replacement for built-in function cmp that was removed in Python 3

        Compare the two objects x and y and return an integer according to
        the outcome. The return value is negative if x < y, zero if x == y
        and strictly positive if x > y.
        """
        return (x > y) - (x < y)

    def __cmp_gt(self, val1, val2):
        return self.compare(val1, val2) == 1

    def __cmp_eq(self, val1, val2):
        return self.compare(val1, val2) == 0

    def compare(self, val1, val2):
        if val1 == 'unlimited' and val2 == 'unlimited':
            return 0
        if val1 == 'unlimited':
            return 1
        if val2 == 'unlimited':
            return -1
        return self.__cmp(int(val1), int(val2))

    def set_values(self, lo, module):
        self.__readLicense()
        disable_add = 0
        self.__countSysAccounts(lo)

        if self.new_license:
            lic = None
            real = None
            if self.version == '1':
                self.__countObject(License.ACCOUNT, lo)
                self.__countObject(License.CLIENT, lo)
                self.__countObject(License.DESKTOP, lo)
                self.__countObject(License.GROUPWARE, lo)
                lic = (
                    self.licenses[self.version][License.ACCOUNT],
                    self.licenses[self.version][License.CLIENT],
                    self.licenses[self.version][License.DESKTOP],
                    self.licenses[self.version][License.GROUPWARE])
                real = (
                    self.real[self.version][License.ACCOUNT],
                    self.real[self.version][License.CLIENT],
                    self.real[self.version][License.DESKTOP],
                    self.real[self.version][License.GROUPWARE])
            elif self.version == '2':
                self.__countObject(License.USERS, lo)
                self.__countObject(License.SERVERS, lo)
                self.__countObject(License.MANAGEDCLIENTS, lo)
                self.__countObject(License.CORPORATECLIENTS, lo)

                lic = (
                    self.licenses[self.version][License.USERS],
                    self.licenses[self.version][License.SERVERS],
                    self.licenses[self.version][License.MANAGEDCLIENTS],
                    self.licenses[self.version][License.CORPORATECLIENTS])
                real = (
                    self.real[self.version][License.USERS],
                    self.real[self.version][License.SERVERS],
                    self.real[self.version][License.MANAGEDCLIENTS],
                    self.real[self.version][License.CORPORATECLIENTS])
                self.licenseKeyID = self.__getValue('univentionLicenseKeyID', '')
                self.licenseSupport = self.__getValue('univentionLicenseSupport', '0')
                self.licensePremiumSupport = self.__getValue('univentionLicensePremiumSupport', '0')
            disable_add = self.checkObjectCounts(lic, real)
            self.licenseBase = self.__getValue('univentionLicenseBaseDN', '')
            if disable_add:
                self._expired = True
            elif not disable_add and self.licenseBase in ('Free for personal use edition', 'UCS Core Edition'):
                disable_add = 5

        # check modules list for validity and accepted operations
        self.checkModules()

        return disable_add

    def init_select(self, lo, module):
        self.select(module, lo)
        return self.set_values(lo, module)

    def checkObjectCounts(self, lic, real):
        disable_add = 0
        if self.version == '1':
            lic_account, lic_client, lic_desktop, lic_groupware = lic
            real_account, real_client, real_desktop, real_groupware = real
            if lic_client and lic_account:
                if self.__cmp_gt(lic_account, lic_client) and self.__cmp_gt(real_client, lic_client):
                    disable_add = 1
                elif self.__cmp_gt(lic_client, lic_account) and self.__cmp_gt(int(real_account) - max(License.SYSACCOUNTS, self.sysAccountsFound), lic_account):
                    disable_add = 2
                elif self.__cmp_eq(lic_client, lic_account):
                    if self.__cmp_gt(real_client, lic_client):
                        disable_add = 1
                    elif self.__cmp_gt(int(real_account) - max(License.SYSACCOUNTS, self.sysAccountsFound), lic_account):
                        disable_add = 2
            else:
                if lic_client and self.__cmp_gt(real_client, lic_client):
                    disable_add = 1
                if lic_account and self.__cmp_gt(int(real_account) - max(License.SYSACCOUNTS, self.sysAccountsFound), lic_account):
                    disable_add = 2
            if lic_desktop and real_desktop and self.__cmp_gt(real_desktop, lic_desktop):
                log.debug('LICENSE: 3')
                disable_add = 3
            if lic_groupware and real_groupware and self.__cmp_gt(real_groupware, lic_groupware):
                log.debug('LICENSE: 4')
                disable_add = 4
        elif self.version == '2':
            lic_users, _lic_servers, lic_managedclients, lic_corporateclients, = lic
            real_users, _real_servers, real_managedclients, real_corporateclients, = real
            if lic_users and self.__cmp_gt(int(real_users) - self.sysAccountsFound, lic_users):
                disable_add = 6
            # The license should be valid even if we have more servers than the license allowed
            # if lic_servers and self.__cmp_gt( real_servers, lic_servers ):
            #    disable_add = 7
            if lic_managedclients and self.__cmp_gt(real_managedclients, lic_managedclients):
                disable_add = 8
            if lic_corporateclients and self.__cmp_gt(real_corporateclients, lic_corporateclients):
                disable_add = 9
        return disable_add

    def __countSysAccounts(self, lo):
        version = self.version
        if version not in self.licenses:
            version = '2'
        if self.licenses[version][License.USERS] == 'unlimited':
            self.sysAccountsFound = 0
            return

        userfilter = [univention.admin.filter.expression('uid', account) for account in self.sysAccountNames]
        filter = univention.admin.filter.conjunction('&', [
            univention.admin.filter.conjunction('|', userfilter),
            self.filters[version][License.USERS]])
        try:
            self.sysAccountsFound = len(lo.searchDn(filter=str(filter)))
        except univention.admin.uexceptions.noObject:
            pass
        log.debug('LICENSE: Univention sysAccountsFound: %d', self.sysAccountsFound)

    def __countObject(self, obj, lo):
        version = self.version
        if version not in self.licenses:
            version = '2'
        if self.licenses[version][obj] and self.licenses[version][obj] != "unlimited":
            result = lo.searchDn(filter=self.filters[version][obj])
            if result is None:
                self.real[version][obj] = 0
            else:
                self.real[version][obj] = len(result)
            log.debug('LICENSE: Univention %s real %d', self.names[version][obj], self.real[version][obj])
        else:
            self.real[version][obj] = 0

    def __raiseException(self):
        if self.error != 0:
            if self.error == -1:
                raise univention.admin.uexceptions.licenseNotFound()
            elif self.error == 2:
                raise univention.admin.uexceptions.licenseExpired()
            elif self.error == 4:
                raise univention.admin.uexceptions.licenseWrongBaseDn()
            else:
                raise univention.admin.uexceptions.licenseInvalid()

    def __getValue(self, key, default, name='', errormsg=''):
        name = name or key
        try:
            value = univention.license.getValue(key)
            self.new_license = True
            log.debug('LICENSE: Univention %r allowed %r', name, value)
        except (KeyError, Exception):
            if self.searchResult:
                value = self.searchResult[0][1].get(key, [default])
                value = [x.decode('ASCII') if isinstance(x, bytes) else x for x in value]
                if not isinstance(default, list):
                    value = value[0]
                self.new_license = True
            else:
                log.debug('LICENSE: %r: %s', name, errormsg)
                value = default

        log.debug('LICENSE: %r = %r', name, value)
        return value

    def __readLicense(self):
        self.version = self.__getValue('univentionLicenseVersion', '1', 'Version', None)
        if self.version == '1':
            self.licenses[self.version][License.ACCOUNT] = self.__getValue(self.keys[self.version][License.ACCOUNT], None, 'Accounts', 'Univention Accounts not found')
            self.licenses[self.version][License.CLIENT] = self.__getValue(self.keys[self.version][License.CLIENT], None, 'Clients', 'Univention Clients not found')
            self.licenses[self.version][License.DESKTOP] = self.__getValue(self.keys[self.version][License.DESKTOP], 2, 'Desktops', 'Univention Desktops not found')
            self.licenses[self.version][License.GROUPWARE] = self.__getValue(self.keys[self.version][License.GROUPWARE], 2, 'Groupware Accounts', 'Groupware not found')
            # if no type field is found it must be an old UCS license (<=1.3-0)
            self.types = self.__getValue('univentionLicenseType', ['UCS'], 'License Type', 'Type attribute not found')
            if not isinstance(self.types, list | tuple):
                self.types = [self.types]
            self.types = list(self.types)
            # handle license type "OXAE" the same way as license type "UCS"
            if 'OXAE' in self.types and 'UCS' not in self.types:
                self.types.append('UCS')
        elif self.version == '2':
            self.licenses[self.version][License.USERS] = self.__getValue(self.keys[self.version][License.USERS], None, 'Users', 'Users not found')
            self.licenses[self.version][License.SERVERS] = self.__getValue(self.keys[self.version][License.SERVERS], None, 'Servers', 'Servers not found')
            self.licenses[self.version][License.MANAGEDCLIENTS] = self.__getValue(self.keys[self.version][License.MANAGEDCLIENTS], None, 'Managed Clients', 'Managed Clients not found')
            self.licenses[self.version][License.CORPORATECLIENTS] = self.__getValue(self.keys[self.version][License.CORPORATECLIENTS], None, 'Corporate Clients', 'Corporate Clients not found')
            self.types = self.__getValue('univentionLicenseProduct', ['Univention Corporate Server'], 'License Product', 'Product attribute not found')
            if not isinstance(self.types, list | tuple):
                self.types = [self.types]
            self.types = list(self.types)

        self.oemProductTypes = self.__getValue('univentionLicenseOEMProduct', [], 'License Type', 'univentionLicenseOEMProduct attribute not found')
        if not isinstance(self.oemProductTypes, list | tuple):
            self.oemProductTypes = [self.oemProductTypes]
        self.types.extend(self.oemProductTypes)
        self.endDate = self.__getValue('univentionLicenseEndDate', None, 'License end date', 'univentionLicenseEndDate attribute not found')


_license = License()

# for compatibility
select = _license.select
init_select = _license.init_select
is_valid_for = _license.isValidFor
