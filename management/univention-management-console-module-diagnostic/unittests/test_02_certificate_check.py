#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import os
import tempfile

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _create_test_cert(cn, san_names=None, days_valid=365):
    """Create a self-signed test certificate and return its path."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.UTC)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(1000)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=days_valid))
    )

    if san_names:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(name) for name in san_names]),
            critical=False,
        )

    cert = builder.sign(key, hashes.SHA256())

    fd, path = tempfile.mkstemp(suffix='.pem')
    with os.fdopen(fd, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
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
        with open(cert_internal, 'rb') as f:
            cert = x509.load_pem_x509_certificate(f.read())
        cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        assert cn_attrs[0].value == 'server.domain.local'

    def test_extracts_san(self, cert_external):
        with open(cert_external, 'rb') as f:
            cert = x509.load_pem_x509_certificate(f.read())

        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        names = san_ext.value.get_values_for_type(x509.DNSName)
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
