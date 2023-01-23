#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention SSL
"""SSL listener module."""
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
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

from __future__ import absolute_import, annotations

import grp
import os
import subprocess
from errno import ENOENT
from shutil import rmtree
from typing import Dict, List

import univention.debug as ud

from listener import configRegistry, setuid, unsetuid


description = 'Generate new Certificates'
filter = '(|%s)' % ''.join('(objectClass=%s)' % oc for oc in set(configRegistry['ssl/host/objectclass'].split(',')))
modrdn = "1"


SSLDIR = '/etc/univention/ssl'

_delay = None


def domain(info: Dict[str, List[bytes]]) -> str:
    """
    Return domain name of machine account.

    :param info: LDAP attribute values.
    """
    try:
        return info['associatedDomain'][0].decode('ASCII')
    except LookupError:
        return configRegistry['domainname']


def wildcard_certificate(info: Dict[str, List[bytes]]) -> bool:
    """
    Check if a wildcard certificate should be created for the host.

    :param info: LDAP attribute values.
    :returns: `True` for a wildcard name, `False` otherwise.
    """
    return b'Wildcard Certificate' in info.get('univentionService', [])


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], command: str = '') -> None:
    """
    Handle changes to 'dn'.

    :param dn: Distinguished name.
    :param new: Current LDAP attribute values.
    :param old: Previous LDAP attribute values.
    :param command: LDAp transaction type.
    """
    if configRegistry['server/role'] != 'domaincontroller_master':
        return

    setuid(0)
    try:
        global _delay
        if _delay:
            (old_dn, old) = _delay
            if command != 'a' or old['entryUUID'] != new['entryUUID']:
                ud.debug(ud.LISTENER, ud.WARN, 'CERTIFICATE: Non-consecutive move %s -> %s', old_dn, dn)
                (old_dn, old) = (None, None)
        _delay = None

        old_cn = old['cn'][0].decode('UTF-8') if old else ""
        new_cn = new['cn'][0].decode('UTF-8') if new else ""
        if new and not old:
            # changeType: add
            create_certificate(new_cn, domain(new))
            if wildcard_certificate(new):
                create_certificate('*.%s' % new_cn, domain(new))
        elif old and not new:
            # changeType: delete
            if command == 'r':
                _delay = (dn, old)
            else:
                remove_certificate(old_cn, domainname=domain(old))
                remove_certificate('*.%s' % old_cn, domainname=domain(old))
        elif old and new:
            # changeType: modify
            old_domain = domain(old)
            new_domain = domain(new)

            if new_domain != old_domain:
                remove_certificate(old_cn, old_domain)
                create_certificate(new_cn, new_domain)
                remove_certificate('*.%s' % old_cn, old_domain)
                if wildcard_certificate(new):
                    create_certificate('*.%s' % new_cn, new_domain)
            else:
                if wildcard_certificate(new) and not wildcard_certificate(old):
                    create_certificate('*.%s' % new_cn, domain(new))
                if not wildcard_certificate(new) and wildcard_certificate(old):
                    remove_certificate('*.%s' % old_cn, domainname=domain(old))

        if new:
            # Reset permissions
            fqdn = "%s.%s" % (new_cn, domain(new))
            certpath = os.path.join(SSLDIR, fqdn)
            fix_permissions(certpath, dn, new)
            if wildcard_certificate(new):
                fqdn = "*.%s.%s" % (new_cn, domain(new))
                certpath = os.path.join(SSLDIR, fqdn)
                fix_permissions(certpath, dn, new)
    finally:
        unsetuid()


def fix_permissions(certpath: str, dn: str, new: Dict[str, List[bytes]]) -> None:
    """
    Set file permission on directory and files within.

    :param certpath: Base directory path.
    :param dn: Distinguished name.
    :param new: LDAP attribute values.
    """
    try:
        uidNumber = int(new.get('uidNumber', [b'0'])[0].decode('ASCII'))
    except (LookupError, TypeError, ValueError):
        uidNumber = 0

    try:
        ent = grp.getgrnam('DC Backup Hosts')
        gidNumber = int(ent.gr_gid)
    except (LookupError, TypeError, ValueError):
        ud.debug(ud.LISTENER, ud.WARN, 'CERTIFICATE: Failed to get groupID for "%s"' % dn)
        gidNumber = 0

    for directory, _dirnames, filenames in os.walk(certpath):
        ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Set permissions for = %s with owner/group %s/%s' % (directory, uidNumber, gidNumber))
        os.chown(directory, uidNumber, gidNumber)
        os.chmod(directory, 0o750)

        for fname in filenames:
            filename = os.path.join(directory, fname)
            if os.path.islink(filename):
                continue
            ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Set permissions for = %s with owner/group %s/%s' % (filename, uidNumber, gidNumber))
            os.chown(filename, uidNumber, gidNumber)
            os.chmod(filename, 0o640)


def create_certificate(hostname: str, domainname: str) -> None:
    """
    Create SSL host certificate.

    :param hostname: host name.
    :param domainname: domain name,
    """
    fqdn = '%s.%s' % (hostname, domainname)
    certpath = os.path.join(SSLDIR, fqdn)
    link_path = os.path.join(SSLDIR, hostname)

    if os.path.exists(certpath):
        ud.debug(ud.LISTENER, ud.WARN, 'CERTIFICATE: Certificate for host %s already exists' % (fqdn,))
        if os.path.islink(link_path):
            return
    else:
        if len(fqdn) > 64:
            ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: FQDN %r is longer than 64 characters, setting Common Name to hostname.' % fqdn)

        ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Creating certificate %s' % hostname)
        subprocess.call(('/usr/sbin/univention-certificate', 'new', '-name', fqdn))

    # Create symlink
    try:
        os.remove(link_path)
    except EnvironmentError as ex:
        if ex.errno != ENOENT:
            ud.debug(ud.LISTENER, ud.WARN, 'CERTIFICATE: Failed to remove %s: %s' % (link_path, ex))
    try:
        os.symlink(fqdn, link_path)
    except EnvironmentError as ex:
        ud.debug(ud.LISTENER, ud.WARN, 'CERTIFICATE: Failed to create %s: %s' % (link_path, ex))


def remove_certificate(hostname: str, domainname: str) -> None:
    """
    Remove SSL host certificate.

    :param hostname: host name.
    :param domainname: domain name,
    """
    fqdn = '%s.%s' % (hostname, domainname)
    ud.debug(ud.LISTENER, ud.INFO, 'CERTIFICATE: Revoke certificate %s' % (fqdn,))
    subprocess.call(('/usr/sbin/univention-certificate', 'revoke', '-name', fqdn))

    link_path = os.path.join(SSLDIR, hostname)
    if os.path.exists(link_path):
        os.remove(link_path)

    certpath = os.path.join(SSLDIR, fqdn)
    if os.path.exists(certpath):
        rmtree(certpath, ignore_errors=True)
