# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| wrapper around :py:mod:`univention.license` that translates error codes to exceptions"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from univention.admin.uldap import access

import ldap
from ldap.filter import filter_format

import univention.admin.localization
import univention.admin.modules
import univention.admin.uexceptions
import univention.license
from univention.admin._ucr import configRegistry
from univention.admin.log import log
from univention.lib.misc import custom_username


translation = univention.admin.localization.translation('univention/admin')
_ = translation.translate

log = log.getChild('LICENSE')

_license = None

LDAP_FILTER_license_module = '(&(objectClass=univentionLicense)(univentionLicenseModule=%s))'
LDAP_FILTER_normal_user_account = '(univentionObjectType=users/user)'
LDAP_FILTER_account_not_disabled = '(!(&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))))'
LDAP_FILTER_managedclients = '(|(objectClass=univentionWindows)(objectclass=univentionUbuntuClient)(objectClass=univentionLinuxClient)(objectClass=univentionCorporateClient)(objectClass=univentionMacOSClient))'


def ldap_filter_not_objectflag(flag_string_list):
    ldap_filter_parts = [filter_format('(univentionObjectFlag=%s)', [flag_string]) for flag_string in flag_string_list]
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
    """Non public interface for license handling."""

    (ACCOUNT, CLIENT, DESKTOP, GROUPWARE) = range(4)
    (USERS, SERVERS, MANAGEDCLIENTS) = range(3)

    SYSACCOUNTS = 5

    def __init__(self):
        if _license:
            raise RuntimeError('never create this object directly')
        self.new_license = False
        self.disable_add = 0
        self._expired = False
        self.endDate = None
        self.oemProductTypes = []
        self.licenseBase = None
        self.types = []
        self.version = '2'
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
            'sys-idp-user',  # Keycloak
        )
        self.sysAccountsFound = 0
        self.licenses = {
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: None,
                License.SERVERS: None,
                License.MANAGEDCLIENTS: None,
            },
        }
        self.real = {
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: 0,
                License.SERVERS: 0,
                License.MANAGEDCLIENTS: 0,
            },
        }
        self.names = {
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: 'Users',
                License.SERVERS: 'Servers',
                License.MANAGEDCLIENTS: 'Managed Clients',
            },
        }
        self.keys = {
            '2': {
                # Version 1 till UCS 3.1
                License.USERS: 'univentionLicenseUsers',
                License.SERVERS: 'univentionLicenseServers',
                License.MANAGEDCLIENTS: 'univentionLicenseManagedClients',
            },
        }
        self.filters = {
            '2': {
                # Version 2 since UCS 3.1
                License.USERS: '(&%s)' % ''.join([LDAP_FILTER_normal_user_account, ldap_filter_not_objectflag(user_exclude_objectflags), LDAP_FILTER_account_not_disabled]),
                License.SERVERS: '(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(!(univentionObjectFlag=docker)))',
                # Managed Clients, Windows Clients, Ubuntu Clients, Linux Clients, MaxOS X Clients
                License.MANAGEDCLIENTS: '(&%s)' % ''.join([LDAP_FILTER_managedclients, ldap_filter_not_objectflag(managedclient_exclude_objectflags)]),
            },
        }
        self.__selected = False
        self.use_cache = True
        self.module = 'admin'

    def init_select(self, lo, module, use_cache: bool = True):
        self.use_cache = use_cache
        self.select(module, lo)
        return self.set_values(lo)

    def select(self, module, lo=None):
        if not self.__selected:
            self.module = module
            self.error = univention.license.select(module)
            if self.error != 0 and lo:
                # Try to set the version even if the license load was not successful
                self.searchResult = lo.authz_connection.search(filter=filter_format(LDAP_FILTER_license_module, [self.module]))
                self.set_values(lo)

            try:
                if int(self.version) < 2:
                    raise ValueError()
            except ValueError:
                raise univention.admin.uexceptions.licenseInvalid()

            if self.error != 0:
                if self.error == -1:
                    raise univention.admin.uexceptions.licenseNotFound()
                elif self.error & 2 == 2:
                    raise univention.admin.uexceptions.licenseExpired()
                elif self.error & 4 == 4:
                    raise univention.admin.uexceptions.licenseWrongBaseDn()
                else:  # 1 == invalid signature
                    raise univention.admin.uexceptions.licenseInvalid()

            self.__selected = True

    def set_values(self, lo):
        self.version = version = self.__getValue('univentionLicenseVersion', '2', 'Version', None)
        self.licenses[version][License.USERS] = self.__getValue(self.keys[version][License.USERS], None, 'Users', 'Users not found')
        self.licenses[version][License.SERVERS] = self.__getValue(self.keys[version][License.SERVERS], None, 'Servers', 'Servers not found')
        self.licenses[version][License.MANAGEDCLIENTS] = self.__getValue(self.keys[version][License.MANAGEDCLIENTS], None, 'Managed Clients', 'Managed Clients not found')
        self.types = [self.__getValue('univentionLicenseProduct', 'Univention Corporate Server', 'License Product', 'Product attribute not found')]

        oem_types = self.__getValue('univentionLicenseOEMProduct', None, 'License Type', 'univentionLicenseOEMProduct attribute not found')
        self.oemProductTypes = [oem_types] if oem_types else []
        self.types.extend(self.oemProductTypes)
        self.endDate = self.__getValue('univentionLicenseEndDate', None, 'License end date', 'univentionLicenseEndDate attribute not found')

        userfilter = '(|%s)' % ''.join(filter_format('(uid=%s)', [account]) for account in self.sysAccountNames)
        self.sysAccountsFound = len(lo.authz_connection.searchDn(filter='(&%s%s)' % (userfilter, self.filters['2'][License.USERS])))
        log.debug('system accounts found', count=self.sysAccountsFound)

        disable_add = 0
        if self.new_license:
            self.licenseKeyID = self.__getValue('univentionLicenseKeyID', '')
            self.licenseSupport = self.__getValue('univentionLicenseSupport', '0')
            self.licensePremiumSupport = self.__getValue('univentionLicensePremiumSupport', '0')
            self.licenseBase = self.__getValue('univentionLicenseBaseDN', '')

            self.real[version][License.USERS] = self.__countObject(License.USERS, lo)
            self.real[version][License.SERVERS] = self.__countObject(License.SERVERS, lo)
            self.real[version][License.MANAGEDCLIENTS] = self.__countObject(License.MANAGEDCLIENTS, lo)

            lic_users = self.licenses[version][License.USERS]
            real_users = self.real[version][License.USERS]
            if lic_users and self.__cmp_gt(int(real_users) - self.sysAccountsFound, lic_users):
                disable_add = 6

            # The license should be valid even if we have more servers than the license allowed
            # if lic_servers and self.__cmp_gt(real_servers, lic_servers):
            #    disable_add = 7

            lic_managedclients = self.licenses[version][License.MANAGEDCLIENTS]
            real_managedclients = self.real[version][License.MANAGEDCLIENTS]
            if lic_managedclients and self.__cmp_gt(real_managedclients, lic_managedclients):
                disable_add = 8

            if disable_add:
                self._expired = True
            elif not disable_add and self.licenseBase in ('Free for personal use edition', 'UCS Core Edition'):
                disable_add = 5

            log.debug('Univention License', users=real_users, clients=real_managedclients)

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

        return disable_add

    def __getValue(self, key, default, name='', errormsg=''):
        name = name or key
        try:
            value = univention.license.getValue(key)
            self.new_license = True
            log.debug('Univention License allowed', license=name, value=value)
        except (KeyError, Exception):
            if self.searchResult:
                value = self.searchResult[0][1].get(key, [default])[0]
                if isinstance(value, bytes):
                    value = value.decode('ASCII')
                self.new_license = True
            else:
                log.debug('get value failed', license=name, error=errormsg)
                return default

        log.debug('get license value:', license=name, value=value)
        return value

    def __cmp_gt(self, val1, val2):
        return self.compare(val1, val2) == 1

    def compare(self, val1, val2):
        if val1 == 'unlimited' and val2 == 'unlimited':
            return 0
        if val1 == 'unlimited':
            return 1
        if val2 == 'unlimited':
            return -1
        return self.__cmp(int(val1), int(val2))

    def __cmp(self, x, y):
        """
        Replacement for built-in function cmp that was removed in Python 3

        Compare the two objects x and y and return an integer according to
        the outcome. The return value is negative if x < y, zero if x == y
        and strictly positive if x > y.
        """
        return (x > y) - (x < y)

    def __countObject(self, obj, lo):
        licenses = lo.authz_connection.search(filter=filter_format(LDAP_FILTER_license_module, [self.module]), attr=['modifyTimestamp', 'univentionUsedLicenseUsers', 'univentionUsedLicenseServers', 'univentionUsedLicenseManagedClients'])
        try:
            _, attrs = licenses[0]
        except IndexError:
            attrs = {}

        version = self.version
        usedkey = self.keys[version][obj].replace('univentionLicense', 'univentionUsedLicense')
        value = int(attrs.get(usedkey, [b'0'])[0].decode('ASCII'))

        # Return cached value if cache is within TTL
        if self.use_cache and value and self._check_cache_ttl(attrs.get('modifyTimestamp', [b''])[0].decode('ASCII')):
            self.real[version][obj] = value
            return value

        self.real[version][obj] = len(lo.authz_connection.searchDn(filter=self.filters[version][obj]))
        return self.real[version][obj]

    def recheck(self, lo) -> bool:
        res = lo.authz_connection.search(
            filter=filter_format(LDAP_FILTER_license_module, [self.module]),
            attr=['modifyTimestamp'],
        )
        attrs = res[0][1] if res else {}
        return not self._check_cache_ttl(attrs.get('modifyTimestamp', [b''])[0].decode('ASCII'))

    def _check_cache_ttl(self, modify_timestamp) -> int:
        cache_ttl = min(max(0, configRegistry.get_int('directory/manager/license-cache/ttl', 3600)), 86400)
        if cache_ttl > 0 and modify_timestamp:
            dt = datetime.strptime(modify_timestamp, "%Y%m%d%H%M%SZ").replace(tzinfo=UTC)
            return datetime.now(UTC) - dt < timedelta(seconds=cache_ttl)
        return False

    def update_cache(self, lo: 'access') -> dict:
        """
        Force update all license count caches.

        This performs expensive LDAP searches and should only be called by
        the cron job or after license import, not during UMC login.

        Returns dict with 'users', 'servers', 'clients' counts.
        """
        dns = lo.authz_connection.searchDn(filter=filter_format(LDAP_FILTER_license_module, [self.module]))
        if not dns:
            log.warning('No license object found, cannot update cache')
            return {'users': 0, 'servers': 0, 'clients': 0}
        dn = dns[0]

        version = self.version
        counts = {}
        for obj, name in [(License.USERS, 'users'), (License.SERVERS, 'servers'), (License.MANAGEDCLIENTS, 'clients')]:
            result = lo.authz_connection.searchDn(filter=self.filters[version][obj])
            count = len(result) if result else 0

            counts[name] = count
            self.real[version][obj] = count

            usedkey = self.keys[version][obj].replace('univentionLicense', 'univentionUsedLicense')
            try:
                lo.authz_connection.modify(dn, [(usedkey, [b'X'], [str(count).encode('ASCII')])], ignore_license=True)
            except (univention.admin.uexceptions.base, ldap.LDAPError) as exc:
                log.warning('Failed to update license cache for %s: %s', name, exc)

        log.info('License cache updated', **counts)
        return counts

    def _get_license_entry_uuid(self, lo):
        for dn, attr in lo.authz_connection.search(filter='(&(objectClass=univentionLicense)(univentionLicenseModule=admin))', attr=['entryUUID']):
            return attr['entryUUID'][0].decode('ASCII')
        return configRegistry.get('uuid/license', '00000000-0000-0000-000-0000000000000')


class LicenseWrapper:
    """Licence interface."""

    def initialize(self, lo: 'access') -> None:
        """Initialize license check. Call this before accessing license data."""
        try:
            _license.init_select(lo, 'admin')
        except univention.admin.uexceptions.licenseError:
            pass  # the license signature is invalid, expired, etc but not the limits are reached, (could not be found?)

    def update_cache(self, lo: 'access') -> dict:
        """
        Force update the license count cache.

        This performs expensive LDAP searches to count users, servers, and clients,
        then updates the cache attributes on the license object.

        Should be called by:
        - The cron job (hourly by default)
        - After license import
        - When quota is exceeded and admin re-logs in
        """
        return _license.update_cache(lo)

    def recheck(self, lo) -> bool:
        """
        Force-update the license cache and re-check quota.
        Only runs if the cache is stale (older than TTL), so fresh-cache over-quota
        logins are fast. Returns True if now within quota.
        """
        if not _license.recheck(lo):
            return False
        log.info('Cache is stale and quota exceeded, force-updating license cache...')

        try:
            admin_lo, _ = univention.admin.uldap.getAdminConnection()
        except OSError:
            return False

        self.initialize(admin_lo)
        self.update_cache(admin_lo)
        try:
            lo.check_license()
        except univention.admin.uexceptions.licenseError:
            log.info('Still over quota after cache update')
            return False

        return True

    def get_user_limit(self) -> int | None:
        limit = _license.licenses[_license.version][License.USERS]
        if limit == 'unlimited':
            return None
        return int(limit or 0)

    def get_server_limit(self) -> int | None:
        limit = _license.licenses[_license.version][License.SERVERS]
        if limit == 'unlimited':
            return None
        return int(limit or 0)

    def get_client_limit(self) -> int | None:
        limit = _license.licenses[_license.version][License.MANAGEDCLIENTS]
        if limit == 'unlimited':
            return None
        return int(limit or 0)

    def get_user_total(self) -> int:
        return _license.real[_license.version][License.USERS]

    def get_server_total(self) -> int:
        return _license.real[_license.version][License.SERVERS]

    def get_client_total(self) -> int:
        return _license.real[_license.version][License.MANAGEDCLIENTS]

    def get_system_accounts(self):
        return _license.sysAccountsFound

    def get_key_id(self, lo):
        return _license.licenseKeyID or _license._get_license_entry_uuid(lo)

    def get_license_data(self):
        def tryint(val, default=-1):
            try:
                return int(val or 0)
            except ValueError:
                return default

        license_data = {}
        license_data['version'] = _license.version
        license_data['limits'] = {
            'user': self.get_user_limit(),
            'server': self.get_server_limit(),
            'client': self.get_client_limit(),
        }
        license_data['used'] = {
            'user': self.get_user_total(),
            'server': self.get_server_total(),
            'client': self.get_client_total(),
        }
        license_data['key_id'] = _license.licenseKeyID
        license_data['support'] = tryint(_license.licenseSupport)
        license_data['premium_support'] = tryint(_license.licensePremiumSupport)
        license_data['license_types'] = _license.types
        license_data['oem_product_types'] = _license.oemProductTypes
        license_data['end_date'] = _license.endDate
        license_data['base_dn'] = _license.licenseBase
        free_license = ''
        if license_data['base_dn'] in ('Free for personal use edition', 'UCS Core Edition'):
            free_license = 'core'
            license_data['base_dn'] = configRegistry.get('ldap/base', '')
        license_data['free_license'] = free_license
        license_data['system_accounts_total'] = _license.sysAccountsFound
        return license_data


_license = License()
license = LicenseWrapper()
del LicenseWrapper

# for compatibility
select = _license.select
init_select = _license.init_select
