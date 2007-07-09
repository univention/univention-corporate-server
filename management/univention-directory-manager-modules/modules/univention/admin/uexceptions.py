# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  exceptions
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import exceptions
import univention.admin.localization

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate


class base(exceptions.Exception):
	pass

class objectExists(base):
	message=_('Object exists.')

class noObject(base):
	message=_('No such object.')

class permissionDenied(base):
	message=_('Permission denied.')

class ldapError(base):
	message=_('LDAP Error')

class insufficientInformation(base):
	message=_('Information provided is not sufficient.')

class noProperty(base):
	message=_('No such property.')

class valueError(base):
	pass

class valueMayNotChange(valueError):
	message=_('Value may not change.')

class valueInvalidSyntax(valueError):
	message=_('Invalid syntax.')

class valueRequired(valueError):
	message=_('Value is required.')

class valueMismatch(valueError):
	message=_('Values do not match.')

class noLock(base):
	message=_('Could not acquire lock.')

class authFail(base):
	message=_('Authentication Failed.')

class uidAlreadyUsed(base):
	message=_('The username is already in use.')

class groupNameAlreadyUsed(base):
	message=_('The groupname is already in use.')

class prohibitedUsername(base):
	message=_('Prohibited username.')

class ipAlreadyUsed(base):
	message=_('IP address is already in use.')

class invalidDhcpEntry(base):
	message=_('The DHCP entry for this host should contain the zone DN, the IP address and the MAC address.')

class nextFreeIp(base):
	message=_('Next IP address not found.')

class ipOverridesNetwork(base):
	message=_('The given IP address is not within the range of the selected network')

class macAlreadyUsed(base):
	message=_('The MAC address is already in use.')

class mailAddressUsed(base):
	message=_('The mail address is already in use.')

class dhcpServerAlreadyUsed(base):
	message=_('DHCP server name already used: ')

class kolabHomeServer(base):
	message=_('Default Kolab home server does not exist')

class primaryGroup(base):
	message=_('Default primary group does not exist')

class primaryGroupUsed(base):
	message=_('This is a primary group')

class homeShareUsed(base):
	message=''

class groupNotFound(base):
	message=_('The requested group not be found.')

class dhcpNotFound(base):
	message=_('The DHCP entry was not found.')

class dnsNotFound(base):
	message=_('The DNS entry was not found')

class commonNameTooLong(base):
	message=_('The FQDN of this object is too long, it must have less than 64 characters.')

class missingInformation(base):
	message=_('Not all needed information was entered.')

class policyFixedAttribute(base):
	message=_('Cannot overwrite a fixed attribute.')

class bootpXORFailover(base):
	message=_('Dynamic BOOTP leases are not compatible with failover.')

class licenseNotFound(base):
	message=_('No license found.')

class licenseInvalid(base):
	message=_('The license is invalid.')

class licenseExpired(base):
	message=_('The license is expired.')

class licenseWrongBaseDn(base):
	message=_('The license is invalid for the current base DN.')

class licenseGPLversion(base):
	message=_('The license check is disabled. Your are using the GPL version without any support or maintenance by Univention.')
class freeForPersonalUse(base):
	message=_('Free for personal use edition.')

class licenseAccounts(base):
	message=_('Too many user accounts')
class licenseClients(base):
	message=_('Too many client accounts')
class licenseDesktops(base):
	message=_('Too many desktop accounts')
class licenseGroupware(base):
	message=_('Too many groupware accounts')
class licenseDisableModify(base):
	message=_('During this session add and modify are disabled')

class pwalreadyused(base):
	message=_('Password has been used before. Please choose a different one.')

class passwordLength(base):
	message=_('The password is to short, at least 8 character!')

class rangeNotInNetwork(base):
	message=_('Network and IP range are incompatible.')

class rangeInNetworkAddress(base):
	message=_('The IP range contains its network address. That is not permitted!')

class rangeInBroadcastAddress(base):
	message=_('The IP range contains its broadcast address. That is not permitted!')

class rangesOverlapping(base):
	message=_('Overlapping IP ranges')

class invalidOptions(base):
	message=_('Invalid combination of options.')

class pwToShort(base):
	message=_('Password policy error: ')

class invalidOperation(base):
	message=_('This operation is not allowed on this object.')

class emptyPrinterGroup(base):
	message=_('Empty printer groups are not possible.')

class leavePrinterGroup(base):
	message=_('Printer groups with quota support can only have members with quota support.')

class notValidPrinter(base):
	message=_('Only printer objects can be members of a printer group.')

class notValidGroup(base):
	message=_('Only existing groups are allowed.')

class notValidUser(base):
	message=_('Only existing users are allowed.')

class templateSyntaxError(base):
	message=_('Invalid syntax in default value. Check these templates: %s.')
	def __init__(self, templates):
		self.templates = templates

class nagiosTimeperiodUsed(base):
	message=_('Timeperiod Object still in use!')

class nagiosARecordRequired(base):
	message=_('IP address entry required to assign nagios services!')

class nagiosDNSForwardZoneEntryRequired(base):
	message=_('DNS Forward Zone entry required to assign nagios services!')
