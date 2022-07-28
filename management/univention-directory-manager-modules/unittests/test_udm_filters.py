#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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

import pytest

import univention.admin.modules
univention.admin.modules.update()

BASE_FILTERS = {
	'users/user': '(&(univentionObjectType=users/user)(!(uidNumber=0))(!(univentionObjectFlag=functional))(%s))',
}


@pytest.mark.parametrize('module, property, udm_filter, expected_filter', [
	('users/user', 'username', 'username=*', 'uid=*'),
	('users/user', 'uidNumber', 'uidNumber=*', 'uidNumber=*'),
	('users/user', 'gidNumber', 'gidNumber=*', 'gidNumber=*'),
	('users/user', 'firstname', 'firstname=*', 'givenName=*'),
	('users/user', 'lastname', 'lastname=*', 'sn=*'),
	('users/user', 'gecos', 'gecos=*', 'gecos=*'),
	('users/user', 'displayName', 'displayName=*', 'displayName=*'),
	('users/user', 'title', 'title=*', 'title=*'),
	('users/user', 'initials', 'initials=*', 'initials=*'),
	('users/user', 'preferredDeliveryMethod', 'preferredDeliveryMethod=*', 'preferredDeliveryMethod=*'),
	('users/user', 'sambaPrivileges', 'sambaPrivileges=*', 'univentionSambaPrivilegeList=*'),
	('users/user', 'description', 'description=*', 'description=*'),
	('users/user', 'organisation', 'organisation=*', 'o=*'),
	('users/user', 'userexpiry', 'userexpiry=*', '|(shadowExpire=*)(krb5ValidEnd=*)(sambaKickoffTime=*)'),
	('users/user', 'passwordexpiry', 'passwordexpiry=*', 'passwordexpiry=*'),  # FIXME: not mapped
	('users/user', 'pwdChangeNextLogin', 'pwdChangeNextLogin=*', 'pwdChangeNextLogin=*'),
	('users/user', 'preferredLanguage', 'preferredLanguage=*', 'preferredLanguage=*'),
	('users/user', 'disabled', 'disabled=*', 'uid=*'),
	('users/user', 'accountActivationDate', 'accountActivationDate=*', 'krb5ValidStart=*'),
	('users/user', 'locked', 'locked=*', 'locked=*'),  # FIXME:
	('users/user', 'lockedTime', 'lockedTime=*', 'sambaBadPasswordTime=*'),
	('users/user', 'unlock', 'unlock=*', 'unlock=*'),  # FIXME: not mapped
	('users/user', 'unlockTime', 'unlockTime=*', 'unlockTime=*'),
	('users/user', 'password', 'password=*', 'password=*'),  # FIXME: not mapped
	('users/user', 'street', 'street=*', 'street=*'),
	('users/user', 'e-mail', 'e-mail=*', 'mail=*'),
	('users/user', 'postcode', 'postcode=*', 'postalCode=*'),
	('users/user', 'postOfficeBox', 'postOfficeBox=*', 'postOfficeBox=*'),
	('users/user', 'city', 'city=*', 'l=*'),
	('users/user', 'country', 'country=*', 'st=*'),  # FIXME: wrong attribute
	('users/user', 'phone', 'phone=*', 'telephoneNumber=*'),
	('users/user', 'employeeNumber', 'employeeNumber=*', 'employeeNumber=*'),
	('users/user', 'roomNumber', 'roomNumber=*', 'roomNumber=*'),
	('users/user', 'secretary', 'secretary=*', 'secretary=*'),
	('users/user', 'departmentNumber', 'departmentNumber=*', 'departmentNumber=*'),
	('users/user', 'employeeType', 'employeeType=*', 'employeeType=*'),
	('users/user', 'homePostalAddress', 'homePostalAddress=*', 'homePostalAddress=*'),
	('users/user', 'physicalDeliveryOfficeName', 'physicalDeliveryOfficeName=*', 'physicalDeliveryOfficeName=*'),
	('users/user', 'homeTelephoneNumber', 'homeTelephoneNumber=*', 'homePhone=*'),
	('users/user', 'mobileTelephoneNumber', 'mobileTelephoneNumber=*', 'mobile=*'),
	('users/user', 'pagerTelephoneNumber', 'pagerTelephoneNumber=*', 'pager=*'),
	('users/user', 'birthday', 'birthday=*', 'univentionBirthday=*'),
	('users/user', 'unixhome', 'unixhome=*', 'homeDirectory=*'),
	('users/user', 'shell', 'shell=*', 'loginShell=*'),
	('users/user', 'sambahome', 'sambahome=*', 'sambaHomePath=*'),
	('users/user', 'scriptpath', 'scriptpath=*', 'sambaLogonScript=*'),
	('users/user', 'profilepath', 'profilepath=*', 'sambaProfilePath=*'),
	('users/user', 'homedrive', 'homedrive=*', 'sambaHomeDrive=*'),
	('users/user', 'sambaRID', 'sambaRID=*', 'sambaRID=*'),
	('users/user', 'groups', 'groups=*', 'memberOf=*'),
	('users/user', 'primaryGroup', 'primaryGroup=*', 'gidNumber=*'),
	('users/user', 'mailHomeServer', 'mailHomeServer=*', 'univentionMailHomeServer=*'),
	('users/user', 'mailPrimaryAddress', 'mailPrimaryAddress=*', 'mailPrimaryAddress=*'),
	('users/user', 'mailAlternativeAddress', 'mailAlternativeAddress=*', 'mailAlternativeAddress=*'),
	('users/user', 'mailForwardAddress', 'mailForwardAddress=*', 'mailForwardAddress=*'),
	('users/user', 'mailForwardCopyToSelf', 'mailForwardCopyToSelf=*', 'mailForwardCopyToSelf=*'),
	('users/user', 'overridePWHistory', 'overridePWHistory=*', 'overridePWHistory=*'),
	('users/user', 'overridePWLength', 'overridePWLength=*', 'overridePWLength=*'),
	('users/user', 'homeShare', 'homeShare=*', 'homeShare=*'),
	('users/user', 'homeSharePath', 'homeSharePath=*', 'homeSharePath=*'),
	('users/user', 'sambaUserWorkstations', 'sambaUserWorkstations=*', 'sambaUserWorkstations=*'),
	('users/user', 'sambaLogonHours', 'sambaLogonHours=*', 'sambaLogonHours=*'),
	('users/user', 'jpegPhoto', 'jpegPhoto=*', 'jpegPhoto=*'),
	('users/user', 'userCertificate', 'userCertificate=*', 'userCertificate;binary=*'),
	('users/user', 'certificateIssuerCountry', 'certificateIssuerCountry=*', 'certificateIssuerCountry=*'),  # FIXME:
	('users/user', 'certificateIssuerState', 'certificateIssuerState=*', 'certificateIssuerState=*'),  # FIXME:
	('users/user', 'certificateIssuerLocation', 'certificateIssuerLocation=*', 'certificateIssuerLocation=*'),  # FIXME:
	('users/user', 'certificateIssuerOrganisation', 'certificateIssuerOrganisation=*', 'certificateIssuerOrganisation=*'),  # FIXME:
	('users/user', 'certificateIssuerOrganisationalUnit', 'certificateIssuerOrganisationalUnit=*', 'certificateIssuerOrganisationalUnit=*'),  # FIXME:
	('users/user', 'certificateIssuerCommonName', 'certificateIssuerCommonName=*', 'certificateIssuerCommonName=*'),  # FIXME:
	('users/user', 'certificateIssuerMail', 'certificateIssuerMail=*', 'certificateIssuerMail=*'),  # FIXME:
	('users/user', 'certificateSubjectCountry', 'certificateSubjectCountry=*', 'certificateSubjectCountry=*'),  # FIXME:
	('users/user', 'certificateSubjectState', 'certificateSubjectState=*', 'certificateSubjectState=*'),  # FIXME:
	('users/user', 'certificateSubjectLocation', 'certificateSubjectLocation=*', 'certificateSubjectLocation=*'),  # FIXME:
	('users/user', 'certificateSubjectOrganisation', 'certificateSubjectOrganisation=*', 'certificateSubjectOrganisation=*'),  # FIXME:
	('users/user', 'certificateSubjectOrganisationalUnit', 'certificateSubjectOrganisationalUnit=*', 'certificateSubjectOrganisationalUnit=*'),  # FIXME:
	('users/user', 'certificateSubjectCommonName', 'certificateSubjectCommonName=*', 'certificateSubjectCommonName=*'),  # FIXME:
	('users/user', 'certificateSubjectMail', 'certificateSubjectMail=*', 'certificateSubjectMail=*'),  # FIXME:
	('users/user', 'certificateDateNotBefore', 'certificateDateNotBefore=*', 'certificateDateNotBefore=*'),  # FIXME:
	('users/user', 'certificateDateNotAfter', 'certificateDateNotAfter=*', 'certificateDateNotAfter=*'),  # FIXME:
	('users/user', 'certificateVersion', 'certificateVersion=*', 'certificateVersion=*'),  # FIXME:
	('users/user', 'certificateSerial', 'certificateSerial=*', 'certificateSerial=*'),  # FIXME:
	('users/user', 'umcProperty', 'umcProperty=*', 'univentionUMCProperty=*'),
	('users/user', 'serviceSpecificPassword', 'serviceSpecificPassword=*', 'serviceSpecificPassword=*'),  # FIXME:
])
def test_presence_filters(module, property, udm_filter, expected_filter):
	check_expected_filter(module, property, udm_filter, expected_filter)


@pytest.mark.parametrize('module, property, udm_filter, expected_filter', [
	# all disabled combinations
	('users/user', 'disabled', 'disabled=1', '&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))'),
	('users/user', 'disabled', 'disabled=0', '&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'),
	('users/user', 'disabled', 'disabled=none', '&(!(shadowExpire=1))(!(krb5KDCFlags:1.2.840.113556.1.4.803:=128))(!(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ])))'),
	('users/user', 'disabled', 'disabled=all', '&(shadowExpire=1)(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags=[ULD       ]))'),
	('users/user', 'disabled', 'disabled=posix', 'shadowExpire=1'),
	('users/user', 'disabled', 'disabled=kerberos', '&(krb5KDCFlags:1.2.840.113556.1.4.803:=128)'),
	('users/user', 'disabled', 'disabled=windows', '|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ])'),
	('users/user', 'disabled', 'disabled=windows_kerberos', '&(krb5KDCFlags:1.2.840.113556.1.4.803:=128)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ]))'),
	('users/user', 'disabled', 'disabled=windows_posix', '&(shadowExpire=1)(|(sambaAcctFlags=[UD       ])(sambaAcctFlags==[ULD       ]))'),
	('users/user', 'disabled', 'disabled=posix_kerberos', '&(shadowExpire=1)(krb5KDCFlags=254)'),
	('users/user', 'disabled', 'disabled=foo', 'disabled=foo'),  # TODO: raise invalidFilter

	# all locked combinations
	('users/user', 'locked', 'locked=1', '|(krb5KDCFlags:1.2.840.113556.1.4.803:=131072)(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])'),
	('users/user', 'locked', 'locked=0', '&(!(krb5KDCFlags:1.2.840.113556.1.4.803:=131072))(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))'),
	# ('users/user', 'locked', 'locked=posix', ''),
	('users/user', 'locked', 'locked=windows', '|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])'),
	('users/user', 'locked', 'locked=all', '|(sambaAcctFlags=[UL       ])(sambaAcctFlags=[ULD       ])'),
	('users/user', 'locked', 'locked=none', '&(!(sambaAcctFlags=[UL       ]))(!(sambaAcctFlags=[ULD       ]))'),
	('users/user', 'locked', 'locked=foo', 'locked=foo'),  # TODO: raise invalidFilter

	# all userexpiry combinations
	('users/user', 'userexpiry', 'userexpiry=2021-04-14', '|(shadowExpire=18732)(krb5ValidEnd=20210414000000Z)(sambaKickoffTime=1618358400)'),  # 1618351200 in Europe/Berlin
	('users/user', 'userexpiry', 'userexpiry=18731', '|(shadowExpire=18731)(krb5ValidEnd=18731)(sambaKickoffTime=18731)'),
	('users/user', 'userexpiry', 'userexpiry=20210414000000Z', '|(shadowExpire=20210414000000Z)(krb5ValidEnd=20210414000000Z)(sambaKickoffTime=20210414000000Z)'),
	('users/user', 'userexpiry', 'userexpiry=1618351200', '|(shadowExpire=1618351200)(krb5ValidEnd=1618351200)(sambaKickoffTime=1618351200)'),

	# test every other properties
	('users/user', 'uidNumber', 'uidNumber=foo', 'uidNumber=foo'),
	('users/user', 'gidNumber', 'gidNumber=foo', 'gidNumber=foo'),
	('users/user', 'firstname', 'firstname=foo', 'givenName=foo'),
	('users/user', 'lastname', 'lastname=foo', 'sn=foo'),
	('users/user', 'gecos', 'gecos=foo', 'gecos=foo'),
	('users/user', 'displayName', 'displayName=foo', 'displayName=foo'),
	('users/user', 'title', 'title=foo', 'title=foo'),
	('users/user', 'initials', 'initials=foo', 'initials=foo'),
	('users/user', 'preferredDeliveryMethod', 'preferredDeliveryMethod=physical', 'preferredDeliveryMethod=physical'),
	('users/user', 'sambaPrivileges', 'sambaPrivileges=foo', 'univentionSambaPrivilegeList=foo'),
	('users/user', 'description', 'description=foo', 'description=foo'),
	('users/user', 'organisation', 'organisation=foo', 'o=foo'),
	('users/user', 'userexpiry', 'userexpiry=foo', '|(shadowExpire=foo)(krb5ValidEnd=foo)(sambaKickoffTime=foo)'),
	('users/user', 'passwordexpiry', 'passwordexpiry=foo', 'passwordexpiry=foo'),  # FIXME: not mapped
	('users/user', 'pwdChangeNextLogin', 'pwdChangeNextLogin=1', 'pwdChangeNextLogin=1'),  # FIXME
	('users/user', 'pwdChangeNextLogin', 'pwdChangeNextLogin=0', 'pwdChangeNextLogin=0'),  # FIXME
	('users/user', 'preferredLanguage', 'preferredLanguage=foo', 'preferredLanguage=foo'),
	pytest.param('users/user', 'accountActivationDate', 'accountActivationDate=2006-06-09 02:43 Europe/Berlin', 'krb5ValidStart=20060609004300Z', marks=pytest.mark.xfail(reason='Bug #53830')),
	pytest.param('users/user', 'lockedTime', 'lockedTime=foo', 'sambaBadPasswordTime=foo', marks=pytest.mark.xfail()),
	('users/user', 'lockedTime', 'lockedTime=20220728135807Z', 'sambaBadPasswordTime=133034902870000000'),
	('users/user', 'unlock', 'unlock=1', 'unlock=1'),  # FIXME: should raise invalidFilter
	('users/user', 'unlockTime', 'unlockTime=foo', 'unlockTime=foo'),
	('users/user', 'password', 'password={crypt}$6$lkbnfJcMqcFPrz7n$kUzMEuuYNREVEpLMVm75iZ/FVAEuojkp4VANzsKD94IuD.cgy2FYZ6mmvDj5coqAmi/O3CvaphFWq1dFkdVf71', 'password={crypt}$6$lkbnfJcMqcFPrz7n$kUzMEuuYNREVEpLMVm75iZ/FVAEuojkp4VANzsKD94IuD.cgy2FYZ6mmvDj5coqAmi/O3CvaphFWq1dFkdVf71'),  # FIXME: should raise invalidFilter?!
	('users/user', 'street', 'street=foo', 'street=foo'),
	('users/user', 'e-mail', 'e-mail=foo', 'mail=foo'),
	('users/user', 'postcode', 'postcode=12345', 'postalCode=12345'),
	('users/user', 'postOfficeBox', 'postOfficeBox=foo', 'postOfficeBox=foo'),
	('users/user', 'city', 'city=foo', 'l=foo'),
	('users/user', 'country', 'country=foo', 'st=foo'),
	pytest.param('users/user', 'state', 'country=foo', 'st=foo', marks=pytest.mark.xfail(reason='Bug #50073')),
	pytest.param('users/user', 'country', 'country=foo', 'c=foo', marks=pytest.mark.xfail(reason='Bug #50073')),
	('users/user', 'phone', 'phone=+49 1234', 'telephoneNumber=+49 1234'),
	('users/user', 'employeeNumber', 'employeeNumber=foo', 'employeeNumber=foo'),
	('users/user', 'roomNumber', 'roomNumber=foo', 'roomNumber=foo'),
	('users/user', 'secretary', 'secretary=cn=foo', 'secretary=cn=foo'),
	('users/user', 'departmentNumber', 'departmentNumber=foo', 'departmentNumber=foo'),
	('users/user', 'employeeType', 'employeeType=foo', 'employeeType=foo'),
	('users/user', 'homePostalAddress', 'homePostalAddress=foo', 'homePostalAddress=foo'),
	('users/user', 'physicalDeliveryOfficeName', 'physicalDeliveryOfficeName=foo', 'physicalDeliveryOfficeName=foo'),
	('users/user', 'homeTelephoneNumber', 'homeTelephoneNumber=foo', 'homePhone=foo'),
	('users/user', 'mobileTelephoneNumber', 'mobileTelephoneNumber=foo', 'mobile=foo'),
	('users/user', 'pagerTelephoneNumber', 'pagerTelephoneNumber=foo', 'pager=foo'),
	('users/user', 'birthday', 'birthday=foo', 'univentionBirthday=foo'),
	('users/user', 'birthday', 'birthday=2006-06-09', 'univentionBirthday=2006-06-09'),
	('users/user', 'unixhome', 'unixhome=foo', 'homeDirectory=foo'),
	('users/user', 'shell', 'shell=foo', 'loginShell=foo'),
	('users/user', 'sambahome', 'sambahome=foo', 'sambaHomePath=foo'),
	('users/user', 'scriptpath', 'scriptpath=foo', 'sambaLogonScript=foo'),
	('users/user', 'profilepath', 'profilepath=foo', 'sambaProfilePath=foo'),
	('users/user', 'homedrive', 'homedrive=foo', 'sambaHomeDrive=foo'),
	('users/user', 'sambaRID', 'sambaRID=foo', 'sambaRID=foo'),
	('users/user', 'groups', 'groups=foo', 'memberOf=foo'),
	('users/user', 'primaryGroup', 'primaryGroup=5000', 'gidNumber=5000'),
	pytest.param('users/user', 'primaryGroup', 'primaryGroup=cn=Domain Users,cn=users,dc=base', 'gidNumber=5000', marks=pytest.mark.xfail(reason='Bug #53808')),
	('users/user', 'mailHomeServer', 'mailHomeServer=foo', 'univentionMailHomeServer=foo'),
	('users/user', 'mailPrimaryAddress', 'mailPrimaryAddress=foo', 'mailPrimaryAddress=foo'),
	('users/user', 'mailAlternativeAddress', 'mailAlternativeAddress=foo', 'mailAlternativeAddress=foo'),
	('users/user', 'mailForwardAddress', 'mailForwardAddress=foo', 'mailForwardAddress=foo'),
	('users/user', 'mailForwardCopyToSelf', 'mailForwardCopyToSelf=1', 'mailForwardCopyToSelf=1'),  # FIXME
	('users/user', 'overridePWHistory', 'overridePWHistory=1', 'overridePWHistory=1'),  # FIXME
	('users/user', 'overridePWLength', 'overridePWLength=1', 'overridePWLength=1'),  # FIXME
	('users/user', 'homeShare', 'homeShare=foo', 'homeShare=foo'),
	('users/user', 'homeSharePath', 'homeSharePath=foo', 'homeSharePath=foo'),
	('users/user', 'sambaUserWorkstations', 'sambaUserWorkstations=foo', 'sambaUserWorkstations=foo'),
	pytest.param('users/user', 'sambaLogonHours', 'sambaLogonHours=137', 'sambaLogonHours=000000000000000000000000000000000002000000', marks=pytest.mark.xfail(reason='Bug #53807')),
	pytest.param('users/user', 'jpegPhoto', 'jpegPhoto=foo', 'jpegPhoto=foo', marks=pytest.mark.xfail()),
	pytest.param('users/user', 'userCertificate', 'userCertificate=foo', 'userCertificate;binary=foo', marks=pytest.mark.xfail()),
	('users/user', 'certificateIssuerCountry', 'certificateIssuerCountry=foo', 'certificateIssuerCountry=foo'),  # FIXME:
	('users/user', 'certificateIssuerState', 'certificateIssuerState=foo', 'certificateIssuerState=foo'),  # FIXME:
	('users/user', 'certificateIssuerLocation', 'certificateIssuerLocation=foo', 'certificateIssuerLocation=foo'),  # FIXME:
	('users/user', 'certificateIssuerOrganisation', 'certificateIssuerOrganisation=foo', 'certificateIssuerOrganisation=foo'),  # FIXME:
	('users/user', 'certificateIssuerOrganisationalUnit', 'certificateIssuerOrganisationalUnit=foo', 'certificateIssuerOrganisationalUnit=foo'),  # FIXME:
	('users/user', 'certificateIssuerCommonName', 'certificateIssuerCommonName=foo', 'certificateIssuerCommonName=foo'),  # FIXME:
	('users/user', 'certificateIssuerMail', 'certificateIssuerMail=foo', 'certificateIssuerMail=foo'),  # FIXME:
	('users/user', 'certificateSubjectCountry', 'certificateSubjectCountry=foo', 'certificateSubjectCountry=foo'),  # FIXME:
	('users/user', 'certificateSubjectState', 'certificateSubjectState=foo', 'certificateSubjectState=foo'),  # FIXME:
	('users/user', 'certificateSubjectLocation', 'certificateSubjectLocation=foo', 'certificateSubjectLocation=foo'),  # FIXME:
	('users/user', 'certificateSubjectOrganisation', 'certificateSubjectOrganisation=foo', 'certificateSubjectOrganisation=foo'),  # FIXME:
	('users/user', 'certificateSubjectOrganisationalUnit', 'certificateSubjectOrganisationalUnit=foo', 'certificateSubjectOrganisationalUnit=foo'),  # FIXME:
	('users/user', 'certificateSubjectCommonName', 'certificateSubjectCommonName=foo', 'certificateSubjectCommonName=foo'),  # FIXME:
	('users/user', 'certificateSubjectMail', 'certificateSubjectMail=foo', 'certificateSubjectMail=foo'),  # FIXME:
	('users/user', 'certificateDateNotBefore', 'certificateDateNotBefore=foo', 'certificateDateNotBefore=foo'),  # FIXME:
	('users/user', 'certificateDateNotAfter', 'certificateDateNotAfter=foo', 'certificateDateNotAfter=foo'),  # FIXME:
	('users/user', 'certificateVersion', 'certificateVersion=foo', 'certificateVersion=foo'),  # FIXME:
	('users/user', 'certificateSerial', 'certificateSerial=foo', 'certificateSerial=foo'),  # FIXME:
	pytest.param('users/user', 'umcProperty', 'umcProperty=foo bar', 'univentionUMCProperty=foo=bar', marks=pytest.mark.xfail(reason='Bug #53808')),
	('users/user', 'umcProperty', 'umcProperty=foo=bar', 'univentionUMCProperty=foo=bar'),
	('users/user', 'serviceSpecificPassword', 'serviceSpecificPassword=foo', 'serviceSpecificPassword=foo'),  # FIXME:
])
def test_udm_filter(module, property, udm_filter, expected_filter):
	check_expected_filter(module, property, udm_filter, expected_filter)


def check_expected_filter(module, property, udm_filter, expected_filter):
	expected_filter = BASE_FILTERS[module] % expected_filter
	mod = univention.admin.modules.get(module)
	mod.property_descriptions[property]
	actual_filter = mod.lookup_filter(udm_filter, None)
	assert expected_filter == str(actual_filter)
