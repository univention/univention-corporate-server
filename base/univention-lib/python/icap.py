#!/usr/bin/python3
#
# Univention Common Python Library
#
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Minimal client for the Internet Content Adaptation Protocol (ICAP, :rfc:`3507`).

Use it to scan data for malware with an ICAP server, for example
`c-icap` with the ClamAV back end (service ``avscan``).

>>> result = scan(b'data', 'icap://antivir-icap:1344/avscan')  # doctest: +SKIP
>>> result.infected  # doctest: +SKIP
False
"""

import socket
import ssl
from dataclasses import dataclass
from typing import BinaryIO
from urllib.parse import urlsplit


DEFAULT_PORT = 1344
INFECTION_HEADERS = ('x-infection-found', 'x-virus-id', 'x-virus-name', 'x-violations-found')
BLOCKED_ERROR_CODES = ('file_type_blocked', 'file_extension_blocked')
MAX_HEADER_SIZE = 65536


class ICAPError(Exception):
    """The ICAP server is not available or sent an unexpected response."""


@dataclass(frozen=True)
class ICAPTarget:
    """
    Location of an ICAP service.

    Attributes:
        host: Host name or IP address of the ICAP server.
        port: TCP port of the ICAP server.
        service: Name of the ICAP service, for example ``avscan``.
        tls: Use TLS (``icaps://``) for the connection.
    """

    host: str
    port: int
    service: str
    tls: bool = False

    @classmethod
    def from_url(cls, url: str) -> 'ICAPTarget':
        """
        Parse an ICAP URL.

        Args:
            url: URL in the form ``icap://host[:port]/service`` or ``icaps://host[:port]/service``.

        Returns:
            The parsed target.

        Raises:
            ValueError: If the URL is not a valid ICAP URL.

        >>> ICAPTarget.from_url('icap://antivir-icap/avscan')
        ICAPTarget(host='antivir-icap', port=1344, service='avscan', tls=False)
        >>> ICAPTarget.from_url('icaps://[::1]:11344/srv_clamav')
        ICAPTarget(host='::1', port=11344, service='srv_clamav', tls=True)
        """
        parts = urlsplit(url.strip())
        if parts.scheme not in ('icap', 'icaps'):
            raise ValueError(f'Invalid ICAP URL scheme: {url!r}')
        service = parts.path.strip('/')
        if not parts.hostname or not service:
            raise ValueError(f'ICAP URL requires a host and a service: {url!r}')
        return cls(parts.hostname, parts.port or DEFAULT_PORT, service, parts.scheme == 'icaps')

    @property
    def uri(self) -> str:
        """The ICAP request URI."""
        host = f'[{self.host}]' if ':' in self.host else self.host
        return f'icap://{host}:{self.port}/{self.service}'


@dataclass(frozen=True)
class ScanResult:
    """
    Result of a malware scan.

    Attributes:
        infected: The ICAP server found a threat in the data.
        threat: Description of the threat, if the server reports one.
    """

    infected: bool
    threat: str | None = None


def _read_headers(stream: BinaryIO) -> list[bytes]:
    """
    Read header lines up to the next empty line.

    Args:
        stream: The buffered socket stream.

    Returns:
        The header lines without line endings.

    Raises:
        ICAPError: If the connection closes early or the header is too large.
    """
    lines = []
    size = 0
    while True:
        line = stream.readline(MAX_HEADER_SIZE)
        if not line:
            raise ICAPError('Connection closed by ICAP server')
        size += len(line)
        if size > MAX_HEADER_SIZE:
            raise ICAPError('ICAP response header too large')
        line = line.rstrip(b'\r\n')
        if not line:
            return lines
        lines.append(line)


def _parse_response(stream: BinaryIO) -> ScanResult:
    """
    Parse the ICAP response and decide whether the data is infected.

    Args:
        stream: The buffered socket stream.

    Returns:
        The scan result.

    Raises:
        ICAPError: If the response is invalid or the server could not scan the data.
    """
    status_line, *header_lines = _read_headers(stream)
    try:
        version, code, *_reason = status_line.decode('latin-1').split(None, 2)
        status = int(code)
    except ValueError:
        raise ICAPError(f'Invalid ICAP status line: {status_line!r}')
    if not version.startswith('ICAP/'):
        raise ICAPError(f'Invalid ICAP status line: {status_line!r}')

    headers = {}
    for line in header_lines:
        name, _sep, value = line.decode('latin-1').partition(':')
        headers[name.strip().lower()] = value.strip()

    threat = next((headers[name] for name in INFECTION_HEADERS if headers.get(name)), None)
    if status == 204:
        return ScanResult(bool(threat), threat)
    if status == 200:
        if threat:
            return ScanResult(True, threat)
        if 'res-hdr=' in headers.get('encapsulated', ''):
            http_status, *_http_headers = _read_headers(stream) or [b'']
            if http_status.split()[1:2] == [b'403']:
                return ScanResult(True, http_status.decode('latin-1'))
        return ScanResult(False)
    if status == 500 and headers.get('x-error-code') in BLOCKED_ERROR_CODES:
        return ScanResult(True, headers['x-error-code'])
    raise ICAPError(f'ICAP server could not scan the data: {status_line.decode("latin-1")}')


def _build_request(target: ICAPTarget, data: bytes, filename: str) -> bytes:
    """
    Build an ICAP RESPMOD request that contains the data as HTTP response body.

    Args:
        target: The ICAP service.
        data: The data to scan.
        filename: Name of the file, used in the encapsulated HTTP request.

    Returns:
        The serialized request.
    """
    req_hdr = f'GET /{filename} HTTP/1.1\r\nHost: {target.host}\r\n\r\n'.encode()
    res_hdr = f'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(data)}\r\n\r\n'.encode('ascii')
    icap_hdr = (
        f'RESPMOD {target.uri} ICAP/1.0\r\n'
        f'Host: {target.host}:{target.port}\r\n'
        'User-Agent: Univention-ICAP-Client/1.0\r\n'
        'Allow: 204\r\n'
        f'Encapsulated: req-hdr=0, res-hdr={len(req_hdr)}, res-body={len(req_hdr) + len(res_hdr)}\r\n'
        '\r\n'
    ).encode()
    body = (b'%x\r\n%s\r\n' % (len(data), data) if data else b'') + b'0\r\n\r\n'
    return icap_hdr + req_hdr + res_hdr + body


def scan(data: bytes, url: str, timeout: float = 30.0, filename: str = 'upload') -> ScanResult:
    """
    Scan data for malware with an ICAP server.

    The client sends a ``RESPMOD`` request over TCP.
    This works with `c-icap` and ClamAV as used in openDesk.

    Args:
        data: The data to scan.
        url: URL of the ICAP service, for example ``icap://antivir-icap:1344/avscan``.
        timeout: Timeout in seconds for the connection and each network operation.
        filename: Name of the file, which some ICAP servers show in the report.

    Returns:
        The scan result.

    An invalid URL raises a :class:`ValueError` from :meth:`ICAPTarget.from_url`.

    Raises:
        ICAPError: If the ICAP server is not available or could not scan the data.
    """
    target = ICAPTarget.from_url(url)
    request = _build_request(target, data, filename.replace('/', '_').replace('\r', '').replace('\n', '').replace(' ', '_'))
    try:
        with socket.create_connection((target.host, target.port), timeout=timeout) as sock:
            conn = ssl.create_default_context().wrap_socket(sock, server_hostname=target.host) if target.tls else sock
            with conn, conn.makefile('rb') as stream:
                conn.sendall(request)
                return _parse_response(stream)
    except OSError as exc:
        raise ICAPError(f'Connection to ICAP server {target.host}:{target.port} failed: {exc}') from exc
