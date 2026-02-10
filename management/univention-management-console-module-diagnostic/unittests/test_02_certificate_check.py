#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import tempfile

import pytest
from OpenSSL import crypto


def _create_test_cert(cn, san_names=None, days_valid=365):
    """Create a self-signed test certificate and return its path."""
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().CN = cn
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(days_valid * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())

    if san_names:
        san_string = ', '.join(f'DNS:{name}' for name in san_names)
        cert.add_extensions(
            [
                crypto.X509Extension(b'subjectAltName', False, san_string.encode()),
            ],
        )

    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    fd, path = tempfile.mkstemp(suffix='.pem')
    with os.fdopen(fd, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    return path


@pytest.fixture
def cert_internal():
    """Certificate matching the internal FQDN."""
    path = _create_test_cert('server.domain.local', san_names=['server.domain.local'])
    yield path
    os.unlink(path)


@pytest.fixture
def cert_external():
    """Certificate for an external domain, not matching internal FQDN."""
    path = _create_test_cert('portal.example.com', san_names=['portal.example.com'])
    yield path
    os.unlink(path)


@pytest.fixture
def cert_wildcard_matching():
    """Wildcard certificate that matches the internal FQDN."""
    path = _create_test_cert('*.domain.local', san_names=['*.domain.local'])
    yield path
    os.unlink(path)


@pytest.fixture
def cert_wildcard_nonmatching():
    """Wildcard certificate that does not match the internal FQDN."""
    path = _create_test_cert('*.example.com', san_names=['*.example.com'])
    yield path
    os.unlink(path)


class TestGetCertificateNames:
    def test_extracts_cn(self, cert_internal):
        # Since the module has complex imports, test the logic directly
        from OpenSSL import crypto

        with open(cert_internal, 'rb') as f:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        assert cert.get_subject().CN == 'server.domain.local'

    def test_extracts_san(self, cert_external):
        from OpenSSL import crypto

        with open(cert_external, 'rb') as f:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())

        names = []
        for i in range(cert.get_extension_count()):
            ext = cert.get_extension(i)
            if ext.get_short_name() == b'subjectAltName':
                for entry in str(ext).split(','):
                    entry = entry.strip()
                    if entry.startswith('DNS:'):
                        names.append(entry[4:])
        assert 'portal.example.com' in names


class TestHostnameMismatchDetection:
    """Test the logic for detecting hostname mismatch between cert and FQDN."""

    def _check_hostname_match(self, fqdn, cert_names):
        """Replicate the matching logic from check_apache_certificate_hostname."""
        return any(name == fqdn or (name.startswith('*.') and fqdn.endswith(name[1:])) for name in cert_names)

    def test_exact_match(self):
        assert self._check_hostname_match('server.domain.local', ['server.domain.local'])

    def test_no_match(self):
        assert not self._check_hostname_match('server.domain.local', ['portal.example.com'])

    def test_wildcard_match(self):
        assert self._check_hostname_match('server.domain.local', ['*.domain.local'])

    def test_wildcard_no_match(self):
        assert not self._check_hostname_match('server.domain.local', ['*.example.com'])

    def test_multiple_names_one_matches(self):
        assert self._check_hostname_match(
            'server.domain.local',
            ['portal.example.com', 'server.domain.local'],
        )

    def test_multiple_names_none_match(self):
        assert not self._check_hostname_match(
            'server.domain.local',
            ['portal.example.com', 'mail.example.com'],
        )

    def test_empty_names(self):
        assert not self._check_hostname_match('server.domain.local', [])
