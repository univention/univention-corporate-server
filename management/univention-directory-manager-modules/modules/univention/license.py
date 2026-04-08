# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Univention License Verification"""

import base64
import operator
from datetime import date
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from ldap.filter import filter_format

import univention.admin.uexceptions
import univention.admin.uldap
from univention.admin._ucr import configRegistry as ucr
from univention.admin.log import log


if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

log = log.getChild('license')

__all__ = ('check', 'free', 'getValue', 'select', 'selectDN')

_ATTR_PREFIX = 'univentionLicense'
_OBJECT_CLASS_FILTER = 'objectClass=univentionLicense'

LicenseData = dict[str, list[bytes]]

_PUBLIC_KEY_PEMS: list[bytes] = [
    # _MASTER-KEY
    b"""\
-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEA0jQVFvjqhr2mEUPsG5g2kQA58uq7QMb0gFYOfhAQsQgMuhp2sjXs
dkLG2QSLKhQf9RDZBbgZBffvU3DvRvafWVdX+iAR2AhYGy6pE5Mrj+iXgVcFrlxM
DpVK5PF1N4iGwQpkMS6dgjgfVl+0b4kr99BCU+bZoc/t/KlmGoXVrfPNEZMKa2fQ
bsHkPxTtGq2ylLP2JvGwlEOeUvsbm5H0iOUzDwl35fQYK3um19VKxCIMLvtV95fJ
ZvoZYJYb3sbI0bq3pJxUi/nLi0p1xGYzxSA5nUf5FK53qFN+w9j6OA37URXo19Yj
Ui0mrXNTr7ZiehGobPvKHBdBBtl7LuYLhQIDAQAB
-----END RSA PUBLIC KEY-----
""",
    # _MASTER-KEY2
    b"""\
-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEA06fyc7AmDJg3nzCEB4vPHDBhkTJcMof5fdhWsp049JgQxCcXnbkF
o10RBHT9TxlMjN4ZJ38QkMwh5E0wTc2A/CRqJkVjghTUllPY/MqciftcSyDI0bEf
QEi9rUluomMO615+spmLOWBGcnYH3JJUkHwFOF/TYYkqZeFVbBqVtiGBOUXlSWbG
BGAGVR15TfEuEUt0txjfQReIb+/d7/eiAbX/rgiaq0E1iHOT3Lbqi+sUId31ti6G
3WmuNVln+b5k0YruC9T5IIoOud/lz6A8XaaAIS3eujulP79Xmw6yP+KVIHSFz2KR
VGvSnWgKOyhuFR9/3hAyTeaSGFwRplENCQIDAQAB
-----END RSA PUBLIC KEY-----
""",
    # _OXAE-KEY
    b"""\
-----BEGIN RSA PUBLIC KEY-----
MIICCgKCAgEA5Nq/HNNreRc5L/wj3tP4c0M/QM/6dmHxlUP5CoYu5XP+28gC4X0b
bN9jSznJ9elYR7YSO+286mkYAvQd2yBVfnjr0/zlOp91X/95W2f4AEbF7sniCv32
P8o69QF9vDSP93ACZ2/CS/I0F8w7IYn1o9WQn77G4GmyJMXSP50OXHjH008gIpXw
bQkOdLj8QemuMf9etZNkLR87XFIrR1jdnBJ1MnH3wkKLvPXEGM35PimMrscU5Tdj
Y8ZOJsDohXOIY/32VPpDjp+3biYgj3/3aRh0Sf/rmIWZzNHpn9ux2PoLniAPeMh/
X6edpOaAG2huUSdayt7Do7cTtLql9whX/hUN2qxxIm3k56lOkCxSo6zyC3S3bOZJ
Yma4wGjK1vmfG8yOQ+XqYUddAywNIG9Ntx/l/ggAlOwu/KRFw7cANcqjCd3qPWlu
oYV4QYV0KoMznE4QItvFgYcwOx28xiYmS2r9pQQbIwlKS/ghn9Q4tUm0QRKcD8o/
mPcQtgBDA7SgLM/ZjSOqE51Ik46F8aEEKHOeT31Xe7i7tbUJvbnc/FYU+o0+eGEC
mTp+dauS/6Iy0plubIIljUiN8qsPdRSywmvzQvPNAhXYaRDVTVb6Lp9Gw0whMpN6
1hpXyf/hfsSFYffxeVFcM6JXUSypO8MH0mdwqKlOHNBhPBSfAZtdp4MCAwEAAQ==
-----END RSA PUBLIC KEY-----
""",
]


class _KeyStore:
    """Loads and caches RSA public keys from embedded PEM strings."""

    def __init__(self, pems: list[bytes]) -> None:
        self._keys: list[RSAPublicKey] = []
        for pem in pems:
            # cryptography supports "RSA PUBLIC KEY" (PKCS#1) via
            # load_der_public_key after stripping the PEM wrapper, but the
            # high-level load_pem_public_key only handles PKCS#8.
            # Use load_der_public_key with the decoded body instead.
            key = serialization.load_pem_public_key(
                # Re-wrap as PKCS#8 is not needed; the library handles PKCS#1
                # when we use the low-level backend.
                pem,
            )
            self._keys.append(key)  # type: ignore[arg-type]

    def verify(self, data: bytes, b64_signature: str) -> bool:
        """Verify *data* against the base64-encoded *b64_signature* using any of the stored public keys."""
        raw_sig = base64.b64decode(b64_signature)
        # The C code did SHA1(data) then RSA_verify(NID_sha1, hash, ...)
        # which is PKCS#1 v1.5 with a DigestInfo wrapper for SHA-1.
        for key in self._keys:
            try:
                key.verify(raw_sig, data, padding.PKCS1v15(), hashes.SHA1())  # noqa: S303
                return True
            except Exception:  # noqa: S112
                continue
        return False


_key_store = _KeyStore(_PUBLIC_KEY_PEMS)


class _License:
    """Holds the currently selected license."""

    def __init__(self) -> None:
        self._license: tuple[str | None, LicenseData | None] = (None, None)
        self._lo: univention.admin.uldap.access | None = None

    @property
    def lo(self) -> univention.admin.uldap.access:
        if self._lo is None:
            self._lo, _ = univention.admin.uldap.getMachineConnection()

        return self._lo

    @property
    def base_dn(self) -> str | None:
        return ucr['ldap/base']

    @property
    def current(self) -> tuple[str | None, LicenseData | None]:
        return self._license

    @current.setter
    def current(self, value: tuple[str | None, LicenseData | None]) -> None:
        self._license = value

    def select(self, module: str) -> int:
        """
        Search for a valid license of type *module* in all configured search
        paths and activate it globally.

        :returns:
            * ``-1`` - no license object found at all
            * ``0`` - valid license found and selected
            * ``1`` - signature check failed (bitmask)
            * ``2`` - date check failed (bitmask)
            * ``4`` - base DN check failed (bitmask)
        """
        base_dn = self.base_dn
        if not base_dn:
            log.error('Cannot determine LDAP base DN')
            return -1

        search_paths = self._get_search_paths()
        if not search_paths:
            return -1

        self.current = (None, None)
        validity = -1

        for path in search_paths:
            for dn, candidate in self._search_licenses(path, module):
                validity = self._validate_license(candidate, base_dn)

                self.current = (dn, candidate)
                if validity == 0:
                    log.debug('Valid license selected', path=path, module=module)
                    return 0

                log.error('Invalid license skipped', path=path, validity=validity)

            if self.current:
                break

        if self.current is None:
            log.info('No valid license found', module=module, paths=search_paths)

        return validity

    def selectDN(self, license_dn: str) -> int:
        """
        Load and validate the license object at *license_dn*.

        :returns: ``0`` on success, ``1`` on any failure.
        """
        base_dn = self.base_dn
        if not base_dn:
            log.error('Cannot determine LDAP base DN')
            return 1

        candidate = self._fetch_license_by_dn(license_dn)
        if candidate is None:
            log.error('No license found', dn=license_dn)
            return 1

        if self._validate_license(candidate, base_dn) != 0:
            log.error('License at DN is invalid', dn=license_dn)
            return 1

        self.current = (license_dn, candidate)
        return 0

    def getValue(self, attr: str) -> str | tuple[str, ...]:
        """
        Return the value(s) of the attribute from the currently selected license.

        :returns:
            A single string if there is exactly one value, or a tuple of strings
            for multiple values.
        :raises KeyError: if *attr* is not present in the current license.
        """
        _dn, attrs = self.current
        if not attrs:
            log.error('No license selected')
            raise KeyError(attr)

        values = [x.decode('UTF-8') for x in attrs.get(attr, [])]
        if not values:
            log.warning('Key not found in license', attr=attr)
            raise KeyError(attr)

        if len(values) == 1:
            return values[0]
        return tuple(values)

    def check(self, object_dn: str) -> int:
        """
        Validate the license object at *object_dn* without changing the globally
        selected license.

        :returns:
            * ``-1`` - object not found or not a license object
            * ``0`` - license is valid
            * ``1`` - signature check failed (bitmask)
            * ``2`` - date check failed (bitmask)
            * ``4`` - base DN check failed (bitmask)
            * ``8`` - object not in the configured search path (disabled, always 0)
        """
        base_dn = self.base_dn
        if not base_dn:
            return -1

        candidate = self._fetch_license_by_dn(object_dn)
        if candidate is None:
            return -1

        return self._validate_license(candidate, base_dn)

    def free(self) -> bool:
        """Release the currently selected license and drop the LDAP connection."""
        self._license = None
        self._lo = None
        return True

    def _fetch_license_by_dn(self, dn: str) -> LicenseData | None:
        """Fetch a single license object from LDAP by its exact DN."""
        try:
            return self.lo.search(
                filter=_OBJECT_CLASS_FILTER,
                base=dn,
                scope='base',
                timeout=3,
            )[0][1]
        except univention.admin.uexceptions.noObject:
            return None

    def _search_licenses(self, search_base: str, license_type: str) -> list[tuple[str, LicenseData]]:
        """Search for a license of *license_type* under *search_base*."""
        ldap_filter = filter_format('(&(objectClass=univentionLicense)(univentionLicenseModule=%s))', [license_type])
        try:
            return self.lo.search(
                filter=ldap_filter,
                base=search_base,
                scope='one',
                timeout=3,
            )
        except univention.admin.uexceptions.noObject:
            return []

    def _get_search_paths(self) -> list[str]:
        """Return the list of license search paths from the directory."""
        directory_dn = f'cn=default containers,cn=univention,{self.base_dn}'
        paths = self.lo.authz_connection.get(directory_dn, ['univentionLicenseObject']).get('univentionLicenseObject', [])
        if not paths:
            log.error('No license paths found', directory_dn=directory_dn)
        return [path.decode('UTF-8') for path in paths]

    def _validate_license(self, data: LicenseData, base_dn: str) -> int:
        """
        Run all three checks and return a bitmask (0 = valid).
        Bit 0 (1): bad signature
        Bit 1 (2): expired
        Bit 2 (4): wrong base DN
        """
        result = 0
        if not self._check_signature(data):
            result |= 1
        if not self._check_enddate(data):
            result |= 2
        if not self._check_basedn(data, base_dn):
            result |= 4
        return result

    def _check_signature(self, data: LicenseData) -> bool:
        """Verify the RSA/SHA1 signature stored inside *data*."""
        signature = data.get('univentionLicenseSignature', [b''])[0].decode('ASCII')
        if not signature:
            log.error('License signature attribute missing')
            return False

        # qsort license key/value pairs lexicographically (primary: key, secondary: value)
        parts = sorted([
            (key, value)
            for key, values in data.items()
            for value in values
            if key.startswith(_ATTR_PREFIX) and key != 'univentionLicenseSignature'
        ], key=operator.itemgetter(0, 1))
        payload = b''.join(b'%s\n' % (value,) for key, value in parts)

        ok = _key_store.verify(payload, signature)
        if not ok:
            log.error('License signature verification failed')
        return ok

    def _check_enddate(self, data: LicenseData) -> bool:
        """
        Check that the license has not expired.
        Date format: ``DD.MM.YYYY`` or the literal string ``unlimited``.
        """
        date_str = data.get('univentionLicenseEndDate', [b''])[0].decode('ASCII')
        if not date_str:
            log.error('License lacks univentionLicenseEndDate attribute')
            return False

        if date_str == 'unlimited':
            return True

        try:
            day, month, year = (int(x) for x in date_str.split('.'))
            end = date(year, month, day)
        except (ValueError, TypeError):
            log.error('Cannot parse license end date', value=date_str)
            return False

        today = date.today()
        if end >= today:
            return True

        log.info('License expired', end_date=date_str, today=today.strftime('%d.%m.%Y'))
        return False

    def _check_basedn(self, data: LicenseData, base_dn: str) -> bool:
        """Check that the license base DN matches the LDAP server's base DN."""
        license_base = data.get('univentionLicenseBaseDN', [b''])[0].decode('ASCII')
        if not license_base or not base_dn:
            log.error('Cannot check base DN', base_dn=base_dn, license_base_dn=license_base)
            return False

        # core/free editions are always valid regardless of base DN
        if license_base in ('UCS Core Edition', 'Free for personal use edition'):
            return True

        if univention.admin.uldap.access.compare_dn(license_base.lower(), base_dn.lower()):
            return True

        log.error('License base DN mismatch', license_base_dn=license_base, system_base_dn=base_dn)
        return False


_state = _License()
select = _state.select
selectDN = _state.selectDN
getValue = _state.getValue
check = _state.check
free = _state.free


if __name__ == '__main__':
    print(select('admin'))
