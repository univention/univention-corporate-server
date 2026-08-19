#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from __future__ import annotations

import argparse
import binascii
import datetime
import os
import sys
import tempfile
import uuid
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import TYPE_CHECKING

import ldap.modlist
import ldif

import univention.admin.license as udm_license
import univention.admin.uldap
import univention.logging
from univention.admin.log import log
from univention.config_registry import ucr
from univention.dn import DN
from univention.lib.i18n import Translation


if TYPE_CHECKING:
    from collections.abc import MutableMapping

_ = Translation('univention.admin').translate


def main():
    epilog = 'univention-license-import is a tool for importing license keys for UCS from file.'
    description = 'univention-license-import: import license key for UCS'

    parser = ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command')

    import_parser = subparsers.add_parser('license-import', help='Validate the installed UCS license')
    import_parser.set_defaults(func=import_license)
    import_parser.add_argument('--ldif', required=True)

    args = parser.parse_args()

    univention.logging.basicConfig('/dev/null')

    func = getattr(args, 'func', lambda a: 0)
    sys.exit(func(args))


def import_license(args: argparse.Namespace) -> int:
    lo, _po = univention.admin.uldap.getAdminConnection()
    with open(args.ldif, 'rb') as fd:
        try:
            importer = LicenseImport(fd)
            importer.check(DN(ucr.get('ldap/base', '')))
            existed = importer.write(lo)
            print('Replaced license.' if existed else 'Added license.')
        except LicenseImportError as exc:
            print(f'E: {exc}', file=sys.stderr)
            return 1
    return 0


class LicenseImportError(Exception):
    """Error during license import."""

    def __str__(self) -> str:
        return _('Importing the license failed: %s') % (super().__str__(),)


class LicenseImport(ldif.LDIFParser):
    """Import license from LDIF."""

    dn: DN
    license_base: str = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entries = []
        self.entry = None
        self.dn = None

    def handle(self, dn: str | None, entry: MutableMapping[str, list[bytes]]) -> None:
        """This method is invoked by LDIFParser.parse for each object in the LDIF file."""
        # if dn is None or dn == '':
        #     return
        self.entries.append((dn, entry))

    def check(self, base: DN) -> None:
        """Validate given license."""
        # call parse from ldif.LDIFParser
        try:
            self.parse()
        except binascii.Error:
            raise LicenseImportError(_('No license has been found.'))
        except ValueError as exc:
            # e.g. dn is duplicated
            raise LicenseImportError(_('Malformed license: %s') % (exc,))

        # there should be exactly one object in the LDIF file
        if len(self.entries) == 0:
            raise LicenseImportError(_('License file does not contain DN.'))
        elif len(self.entries) > 1:
            raise LicenseImportError(_('License file contains more than one DN.'))

        dn, entry = self.entries[0]
        self.dn = DN(dn)
        self.entry = entry

        # security check: we allowlist only, because "OBJECTLCASS", "objectClass" and "2.5.4.0" and other variants are possible
        if not {key for key in entry if not key.startswith(('univentionLicense', 'univentionUsedLicense'))}.issubset({'cn', 'objectClass', 'univentionObjectType', 'univentionObjectIdentifier'}):
            raise LicenseImportError(_('The LDAP license object contains invalid attributes.'))

        # security check: could be tricked with extensibleObject to create arbitrary objects
        if set(entry.get('objectClass', [])) != {b'top', b'univentionObject', b'univentionLicense'}:
            raise LicenseImportError(_('The LDAP license object contains invalid object classes.'))

        try:
            self.license_base = entry['univentionLicenseBaseDN'][0].decode('UTF-8')
        except KeyError:
            raise LicenseImportError(_('The LDAP license object is missing the univentionLicenseBaseDN attribute.'))

        entry['univentionObjectIdentifier'] = [str(uuid.uuid4()).encode('ASCII')]

        # a free license does not have the ldap base in its DN
        if not self.dn.endswith(base) and self.license_base.lower() in ('free for personal use edition', 'ucs core edition'):
            self.dn = DN('%s,%s' % (self.dn, base))

        # check whether DN matches the LDAP base
        if not self.dn.endswith(base):
            raise LicenseImportError(_('The LDAP base of the license does not match the LDAP base of the UCS domain (%s).') % (base,))

        subtree_base = DN('%s,%s' % ('cn=license,cn=univention', base))
        if not self.dn.endswith(subtree_base):
            raise LicenseImportError(_('The LDAP license object must be underneath of "%s".') % (subtree_base,))

        # check LDAP base
        if self.license_base.lower() not in [str(base).lower(), 'free for personal use edition', 'ucs core edition']:
            raise LicenseImportError(
                _('The license can not be applied. The LDAP base does not match (expected %(expected)s, found: %(found)s).') % {'expected': base, 'found': self.license_base},
            )

    def write(self, ldap_connection: univention.admin.uldap.access) -> bool:
        """Add or replace the license object."""
        ldap_con = ldap_connection.authz_connection.lo.lo

        try:
            result = ldap_con.search_s(str(self.dn), ldap.SCOPE_BASE, '(objectClass=*)', ['*'])
        except ldap.NO_SUCH_OBJECT:
            result = []

        exists = bool(result)

        if ldap_connection.authz.enabled:
            obj = univention.admin.modules.get('settings/license').object(None, ldap_connection, None, None, None, self.entry)
            obj.position.setDn(str(self.dn.parent))
            obj._exists = exists

            if exists:
                ldap_connection.authz.is_modify_allowed(obj)
            else:
                ldap_connection.authz.is_create_allowed(obj)

        if exists:
            old_dn, old_entry = result[0]

            _backup_license(old_dn, old_entry)

            modifications = ldap.modlist.modifyModlist(old_entry, self.entry)

            if modifications:
                try:
                    ldap_con.modify_s(str(self.dn), modifications)
                except ldap.LDAPError as exc:
                    # LDAPError e.g. LDIF contained non existing attributes
                    raise LicenseImportError(_('LDAP error: %s.') % (exc.args[0].get('info'),))

            log.info('Replaced license: %s', self.dn)

        else:
            try:
                ldap_con.add_s(str(self.dn), ldap.modlist.addModlist(self.entry))
            except ldap.LDAPError as exc:
                # LDAPError e.g. LDIF contained non existing attributes
                raise LicenseImportError(_('LDAP error: %s.') % (exc.args[0].get('info'),))
            log.info('Added license: %s', self.dn)

        # Update license count cache after successful import
        self._update_license_cache()
        return exists

    def _update_license_cache(self) -> None:
        """Update license count cache using admin credentials."""
        try:
            admin_lo, _ = univention.admin.uldap.getAdminConnection()
            udm_license.license.initialize(admin_lo)
            counts = udm_license.license.update_cache(admin_lo)
            log.info('License cache updated after import: %s', counts)
        except Exception as exc:
            log.warning('Failed to update license cache after import: %s', exc)


def _backup_license(dn, entry):
    backup_dir = Path('/var/univention-backup')
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    prefix = 'univention_license_replaced_at_{}_'.format(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

    fd, filename = tempfile.mkstemp(prefix=prefix, dir=str(backup_dir))

    try:
        with os.fdopen(fd, 'w') as stream:
            writer = ldif.LDIFWriter(stream)
            writer.unparse(dn, entry)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        os.unlink(filename)
        raise

    log.info('Previous license backed up to %s', filename)
    return filename


if __name__ == '__main__':
    sys.exit(main())
