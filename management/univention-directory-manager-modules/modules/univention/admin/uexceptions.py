# -*- coding: utf-8 -*-
"""
|UDM| exceptions.
"""
# Copyright 2004-2019 Univention GmbH
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

from univention.admin import localization
from univention.admin import configRegistry

translation = localization.translation('univention/admin')
_ = translation.translate


class base(Exception):
	message = ''


class objectExists(base):
	message = _('Object exists.')


class noObject(base):
	message = _('No such object.')


class permissionDenied(base):
	message = _('Permission denied.')


class ldapError(base):
	message = _('LDAP Error')

	def __init__(self, *args, **kwargs):
		self.original_exception = kwargs.pop('original_exception', None)
		super(ldapError, self).__init__(*args, **kwargs)


class ldapTimeout(base):
	message = _('The specified timeout for the LDAP search has been exceeded.')


class ldapSizelimitExceeded(base):
	message = _('The specified size limit for the LDAP search has been exceeded.')


class insufficientInformation(base):
	message = _('Information provided is not sufficient.')


class noProperty(base):
	message = _('No such property.')


class valueError(base):

	def __init__(self, *args, **kwargs):
		self.property = kwargs.pop('property', None)
		super(valueError, self).__init__(*args, **kwargs)


class valueMayNotChange(valueError):
	message = _('Value may not change.')


class valueInvalidSyntax(valueError):
	message = _('Invalid syntax.')


class valueRequired(valueError):
	message = _('Value is required.')


class valueMismatch(valueError):
	message = _('Values do not match.')


class noLock(base):
	message = _('Could not acquire lock.')


class authFail(base):
	message = _('Authentication Failed.')


class uidAlreadyUsed(base):
	if configRegistry.is_true('directory/manager/user_group/uniqueness', True):
		message = _('The username is already in use as username or as groupname')
	else:
		message = _('The username is already in use')


class sidAlreadyUsed(base):
	message = _('The relative ID (SAMBA) is already in use.')


class groupNameAlreadyUsed(base):
	if configRegistry.is_true('directory/manager/user_group/uniqueness', True):
		message = _('The groupname is already in use as groupname or as username')
	else:
		message = _('The groupname is already in use')


class uidNumberAlreadyUsedAsGidNumber(base):
	message = _('The uidNumber is already in use as a gidNumber')


class gidNumberAlreadyUsedAsUidNumber(base):
	message = _('The gidNumber is already in use as a uidNumber')


class adGroupTypeChangeLocalToAny(base):
	message = _('The AD group type can not be changed from type local to any other type.')


class adGroupTypeChangeToLocal(base):
	message = _('The AD group type can not be changed to type local.')


class adGroupTypeChangeGlobalToUniversal(base):
	message = _('The AD group type can not be changed from global to universal, because the group is member of another global group.')


class adGroupTypeChangeDomainLocalToUniversal(base):
	message = _("The AD group type can not be changed from domain local to universal, because the group has another domain local group as member.")


class adGroupTypeChangeUniversalToGlobal(base):
	message = _("The AD group type can not be changed from universal to global, because the group has another universal group as member.")


class adGroupTypeChangeGlobalToDomainLocal(base):
	message = _("The AD group type can not be changed from global to domain local.")


class adGroupTypeChangeDomainLocalToGlobal(base):
	message = _("The AD group type can not be changed from domain local to global.")


class prohibitedUsername(base):
	message = _('Prohibited username.')


class ipAlreadyUsed(base):
	message = _('IP address is already in use.')


class dnsAliasAlreadyUsed(base):
	message = _('DNS alias is already in use.')


class invalidDhcpEntry(base):
	message = _('The DHCP entry for this host should contain the zone DN, the IP address and the MAC address.')


class invalidDNSAliasEntry(base):
	message = _('The DNS alias entry for this host should contain the zone name, the alias zone container DN and the alias.')


class InvalidDNS_Information(base):
	message = _('The provided DNS information are invalid.')


class nextFreeIp(base):
	message = _('Next IP address not found.')


class ipOverridesNetwork(base):
	message = _('The given IP address is not within the range of the selected network')


class macAlreadyUsed(base):
	message = _('The MAC address is already in use.')


class mailAddressUsed(base):
	message = _('The mail address is already in use.')


class dhcpServerAlreadyUsed(base):
	message = _('DHCP server name already used: ')


class kolabHomeServer(base):
	message = _('Default Kolab home server does not exist')


class primaryGroup(base):
	message = _('Default primary group does not exist')


class primaryGroupUsed(base):
	message = _('This is a primary group.')


class homeShareUsed(base):
	message = ''


class groupNotFound(base):
	message = _('The requested group not be found.')


class dhcpNotFound(base):
	message = _('The DHCP entry was not found.')


class dnsNotFound(base):
	message = _('The DNS entry was not found')


class commonNameTooLong(base):
	message = _('The FQDN of this object is too long, it must have less than 64 characters.')


class missingInformation(base):
	message = _('Not all needed information was entered.')


class policyFixedAttribute(base):
	message = _('Cannot overwrite a fixed attribute.')


class bootpXORFailover(base):
	message = _('Dynamic BOOTP leases are not compatible with failover.')


class licenseNotFound(base):
	message = _('No license found.')


class licenseInvalid(base):
	message = _('The license is invalid.')


class licenseExpired(base):
	message = _('The license is expired.')


class licenseWrongBaseDn(base):
	message = _('The license is invalid for the current base DN.')


class licenseCoreEdition(base):
	message = 'UCS Core Edition.'


class freeForPersonalUse(base):
	message = 'Free for personal use edition.'


class licenseAccounts(base):
	message = _('Too many user accounts')


class licenseClients(base):
	message = _('Too many client accounts')


class licenseDesktops(base):
	message = _('Too many desktop accounts')


class licenseGroupware(base):
	message = _('Too many groupware accounts')


class licenseUsers(base):
	message = _('Too many users')


class licenseServers(base):
	message = _('Too many servers')


class licenseManagedClients(base):
	message = _('Too many managed clients')


class licenseCorporateClients(base):
	message = _('Too many corporate clients')


class licenseDVSUsers(base):
	message = _('Too many DVS users')


class licenseDVSClients(base):
	message = _('Too many DVS clients')


class licenseDisableModify(base):
	message = _('During this session add and modify are disabled')


class pwalreadyused(base):
	message = _('Password has been used before. Please choose a different one.')


class passwordLength(base):
	message = _('The password is too short, at least 8 character!')


class rangeNotInNetwork(base):
	message = _('Network and IP range are incompatible.')


class rangeInNetworkAddress(base):
	message = _('The IP range contains its network address. That is not permitted!')


class rangeInBroadcastAddress(base):
	message = _('The IP range contains its broadcast address. That is not permitted!')


class rangesOverlapping(base):
	message = _('Overlapping IP ranges')


class invalidOptions(base):
	message = _('Invalid combination of options.')


class pwToShort(base):
	message = _('Password policy error: ')


class pwQuality(base):
	message = _('Password policy error: ')


class invalidOperation(base):
	message = _('This operation is not allowed on this object.')


class emptyPrinterGroup(base):
	message = _('Empty printer groups are not possible.')


class leavePrinterGroup(base):
	message = _('Printer groups with quota support can only have members with quota support.')


class notValidPrinter(base):
	message = _('Only printer objects can be members of a printer group.')


class notValidGroup(base):
	message = _('Only existing groups are allowed.')


class notValidUser(base):
	message = _('Only existing users are allowed.')


class templateSyntaxError(base):
	message = _('Invalid syntax in default value. Check these templates: %s.')

	def __init__(self, templates):
		self.templates = templates


class nagiosTimeperiodUsed(base):
	message = _('Timeperiod Object still in use!')


class nagiosARecordRequired(base):
	message = _('IP address entry required to assign Nagios services!')


class nagiosDNSForwardZoneEntryRequired(base):
	message = _('DNS Forward Zone entry required to assign Nagios services!')


class dnsAliasRecordExists(base):
	message = _('The DNS forward entry could not be created. Please remove existing alias records or comparable DNS objects with the same name as this host from the forward zone.')


class circularGroupDependency(base):
	message = _('Circular group dependency detected: ')


class invalidChild(base):
	pass


class primaryGroupWithoutSamba(base):
	message = _('Need a primary group with samba option to create a user with samba option')


class wrongObjectType(base):
	message = _('The object type of this object differs from the specified object type.')


class noKerberosRealm(base):
	message = _('There was no valid kerberos realm found.')
