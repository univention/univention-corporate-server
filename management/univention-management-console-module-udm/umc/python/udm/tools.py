#!/usr/bin/python3
#
# Univention Management Console
#  module: manages UDM modules
#
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import urllib.request
from urllib.request import ProxyHandler, build_opener

import ldif

import univention.admin.license as udm_license
import univention.admin.uexceptions as udm_errors
import univention.admin.uldap
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE


_ = Translation('univention-management-console-module-udm').translate


class LicenseError(Exception):
    pass


def check_license(ldap_connection):
    try:
        try:
            ldap_connection.check_license()
        except (udm_errors.licenseAccounts, udm_errors.licenseUsers, udm_errors.licenseClients, udm_errors.licenseManagedClients, udm_errors.licenseCorporateClients):
            if udm_license.license.recheck(ldap_connection):
                return
            raise
    except udm_errors.freeForPersonalUse:
        return
    except udm_errors.licenseNotFound:
        raise LicenseError(_('License not found. During this session add and modify are disabled.'))
    except (udm_errors.licenseAccounts, udm_errors.licenseUsers):
        raise LicenseError(_('You have too many user accounts for your license. Add and modify are disabled. Disable or delete <a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'udm\', \'users/user\', {})"> user accounts</a> to re-enable editing.'))
    except udm_errors.licenseClients:
        raise LicenseError(_('You have too many client accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseServers:
        raise LicenseError(_('You have too many server accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseManagedClients:
        raise LicenseError(_('You have too many managed client accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseCorporateClients:
        raise LicenseError(_('You have too many corporate client accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseDesktops:  # UCS license v1
        raise LicenseError(_('You have too many desktop accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseGroupware:  # UCS license v1
        raise LicenseError(_('You have too many groupware accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseDVSUsers:  # UCS license v2
        raise LicenseError(_('You have too many DVS user accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseDVSClients:  # UCS license v2
        raise LicenseError(_('You have too many DVS client accounts for your license. During this session add and modify are disabled.'))
    except udm_errors.licenseExpired:
        raise LicenseError(_('Your license is expired. During this session add and modify are disabled.'))
    except udm_errors.licenseWrongBaseDn:
        raise LicenseError(_('Your license is not valid for your LDAP-Base. During this session add and modify are disabled.'))
    except udm_errors.licenseInvalid:
        raise LicenseError(_('Your license is not valid. During this session add and modify are disabled.'))
    except udm_errors.licenseDisableModify:
        raise LicenseError(_('Your license does not allow modifications. During this session add and modify are disabled.'))


# TODO: this should probably go into univention-lib
# and hide urllib.request completely
# i.e. it should be unnecessary to import them directly
# in a module
def install_opener(ucr):
    proxy_http = ucr.get('proxy/http')
    if proxy_http:
        proxy = ProxyHandler({'http': proxy_http, 'https': proxy_http})
        opener = build_opener(proxy)
        urllib.request.install_opener(opener)


def urlopen(request):
    # use this in __init__
    # to have the proxy handler installed globally
    return urllib.request.urlopen(request)  # noqa: S310


def dump_license():
    try:
        _lo, _pos = univention.admin.uldap.getMachineConnection(ldap_master=False)
        data = _lo.search('objectClass=univentionLicense')
        del _lo
        del _pos
        # just one license (should be always the case)
        # return the dictionary without the dn
        return ldif.CreateLDIF(data[0][0], data[0][1])
    except Exception as e:
        # no udm, no ldap, malformed return value, whatever
        MODULE.error('getting License from LDAP failed: %s', e)
        return None
