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

import http.client
import io
import re
import socket
import ssl
import threading
import time
from dataclasses import dataclass
from email.message import Message
from typing import BinaryIO
from urllib.parse import quote, urlsplit


DEFAULT_PORT = 1344
INFECTION_HEADERS = ('x-infection-found', 'x-virus-id', 'x-virus-name', 'x-violations-found')
MAX_HEADER_SIZE = 65536
MAX_HEADERS = 100
MAX_LOOKUPS = 4
_lookup_slots = threading.BoundedSemaphore(MAX_LOOKUPS)
HOST_PATTERN = re.compile(r'[A-Za-z0-9._~%:-]+')
SERVICE_PATTERN = re.compile(r"[A-Za-z0-9._~!$&'()*+,;=:@%/-]+")
QUERY_PATTERN = re.compile(r"[A-Za-z0-9._~!$&'()*+,;=:@%/?-]*")


class ICAPError(Exception):
    """
    The ICAP server is not available or sent an unexpected response.

    :ivar int status: The ICAP status code of the response, if the server sent one.
    """

    def __init__(self, message: str, status: int | None = None) -> None:
        """
        Create the error.

        :param str message: Description of the error. It must not contain data from the server.
        :param int status: The ICAP status code of the response.
        """
        super().__init__(message)
        self.status = status

    @classmethod
    def from_status(cls, status: int) -> 'ICAPError':
        """
        Create the error for an ICAP status that isn't a scan result.

        :rfc:`3507` defines only the status codes 200 and 204 as result of a ``RESPMOD`` request.
        ICAP has no redirects, so 3xx codes are errors too.

        :param int status: The ICAP status code.
        :returns: The error.

        >>> str(ICAPError.from_status(404))
        'ICAP server rejected the request (status 404), check the service name in the URL'
        """
        if 400 <= status < 500:
            return cls(f'ICAP server rejected the request (status {status}), check the service name in the URL', status)
        if 500 <= status < 600:
            return cls(f'ICAP server could not scan the data (status {status})', status)
        return cls(f'Unexpected ICAP status {status}, only 200 and 204 are valid scan results', status)


@dataclass(frozen=True)
class ICAPTarget:
    """
    Location of an ICAP service.

    :ivar str host: Host name or IP address of the ICAP server.
    :ivar int port: TCP port of the ICAP server.
    :ivar str service: Name of the ICAP service, for example ``avscan``.
    :ivar bool tls: Use TLS (``icaps://``) for the connection.
    :ivar str query: Query of the URL with options for the service, without ``?``.
    """

    host: str
    port: int
    service: str
    tls: bool = False
    query: str = ''

    def __post_init__(self) -> None:
        """
        Check the values, because they become part of the ICAP request.

        :raises ValueError: If a value contains characters that are not valid in an ICAP URI.
        """
        if not HOST_PATTERN.fullmatch(self.host):
            raise ValueError(f'Invalid ICAP host: {self.host!r}')
        if not isinstance(self.port, int) or not 0 < self.port < 65536:
            raise ValueError(f'Invalid ICAP port: {self.port!r}')
        if not SERVICE_PATTERN.fullmatch(self.service):
            raise ValueError(f'Invalid ICAP service: {self.service!r}')
        if not QUERY_PATTERN.fullmatch(self.query):
            raise ValueError(f'Invalid ICAP query: {self.query!r}')

    @classmethod
    def from_url(cls, url: str) -> 'ICAPTarget':
        """
        Parse an ICAP URL.

        :param str url: URL in the form ``icap://host[:port]/service[?query]`` or ``icaps://host[:port]/service[?query]``.
        :returns: The parsed target.
        :raises ValueError: If the URL is not a valid ICAP URL.
            The URL must not contain control characters, because :func:`urllib.parse.urlsplit` removes some of them silently.

        >>> ICAPTarget.from_url('icap://antivir-icap/avscan')
        ICAPTarget(host='antivir-icap', port=1344, service='avscan', tls=False, query='')
        >>> ICAPTarget.from_url('icaps://[::1]:11344/srv_clamav?allow204=on')
        ICAPTarget(host='::1', port=11344, service='srv_clamav', tls=True, query='allow204=on')
        """
        url = url.strip()
        if not url.isprintable():
            raise ValueError(f'ICAP URL contains invalid characters: {url!r}')
        parts = urlsplit(url)
        if parts.scheme not in ('icap', 'icaps'):
            raise ValueError(f'Invalid ICAP URL scheme: {url!r}')
        if '#' in url:
            raise ValueError(f'ICAP URL must not contain a fragment: {url!r}')
        return cls(parts.hostname or '', parts.port or DEFAULT_PORT, parts.path.strip('/'), parts.scheme == 'icaps', parts.query)

    @property
    def netloc(self) -> str:
        """The ``host:port`` part of the URI. IPv6 addresses are enclosed in brackets."""
        host = f'[{self.host}]' if ':' in self.host else self.host
        return f'{host}:{self.port}'

    @property
    def uri(self) -> str:
        """The ICAP request URI."""
        query = f'?{self.query}' if self.query else ''
        return f'icap://{self.netloc}/{self.service}{query}'


@dataclass(frozen=True)
class ScanResult:
    """
    Result of a malware scan.

    :ivar bool infected: The ICAP server found a threat in the data.
    :ivar str threat: Description of the threat, if the server reports one.
    """

    infected: bool
    threat: str | None = None


def _read_status(stream: BinaryIO, protocol: bytes) -> tuple[int, bytes]:
    """
    Read a status line like ``ICAP/1.0 204 No Content``.

    :param stream: The buffered socket stream.
    :param bytes protocol: The expected protocol, ``ICAP`` or ``HTTP``.
    :returns: The status code and the complete line.
    :raises ICAPError: If the line is missing or invalid.
    """
    line = stream.readline(MAX_HEADER_SIZE + 1)
    if not line:
        raise ICAPError('Connection closed by ICAP server')
    if not line.endswith(b'\n'):
        raise ICAPError(f'Invalid {protocol.decode()} status line')
    version, _sep, rest = line.rstrip(b'\r\n').partition(b' ')
    code = rest[:3]
    if not version.startswith(protocol + b'/') or not code.isdigit() or rest[3:4] not in (b'', b' '):
        raise ICAPError(f'Invalid {protocol.decode()} status line')
    return int(code), line.rstrip(b'\r\n')


def _read_headers(stream: BinaryIO) -> Message:
    """
    Read the header fields up to the empty line that ends them.

    The empty line is required, an incomplete header block is an error, so that a cut-off response is not
    accepted as a scan result. This applies to the ICAP header, the encapsulated HTTP header and the chunk trailer.
    The syntax of ICAP header fields is the same as in HTTP, so :func:`http.client.parse_headers` parses them.

    :param stream: The buffered socket stream.
    :returns: The header fields.
    :raises ICAPError: If the header is incomplete, too large or invalid.
    """
    lines = []
    while True:
        line = stream.readline(MAX_HEADER_SIZE + 1)
        if not line.endswith(b'\n'):
            raise ICAPError('Incomplete ICAP response header' if len(line) <= MAX_HEADER_SIZE else 'ICAP response header too large')
        if line in (b'\r\n', b'\n'):
            break
        lines.append(line)
        if len(lines) > MAX_HEADERS:
            raise ICAPError('Too many ICAP response headers')
    try:
        return http.client.parse_headers(io.BytesIO(b''.join(lines) + b'\r\n'))
    except http.client.HTTPException as exc:
        raise ICAPError(f'Invalid ICAP response header: {type(exc).__name__}') from exc


def _header(headers: Message, name: str) -> str:
    """
    Get a header value with folded lines joined.

    :param headers: The header fields.
    :param str name: The name of the header field.
    :returns: The value, or an empty string.
    """
    return ' '.join(headers.get(name, '').split())


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    """
    Read exactly the given number of bytes.

    :param stream: The buffered socket stream.
    :param int size: Number of bytes to read.
    :returns: The bytes.
    :raises ICAPError: If the server closes the connection before.
    """
    data = stream.read(size)
    if len(data) != size:
        raise ICAPError('Connection closed by ICAP server')
    return data


def _parse_encapsulated(value: str) -> dict[str, int]:
    """
    Parse the ``Encapsulated`` header of a ``RESPMOD`` response.

    :param str value: The header value, for example ``res-hdr=0, res-body=64``.
    :returns: The offset of each encapsulated part.
    :raises ICAPError: If the header is invalid.

    >>> _parse_encapsulated('res-hdr=0, res-body=64')
    {'res-hdr': 0, 'res-body': 64}
    """
    offsets = {}
    for item in value.split(','):
        name, _sep, offset = item.strip().partition('=')
        if name not in ('req-hdr', 'res-hdr', 'res-body', 'null-body') or not offset.isdigit() or name in offsets:
            raise ICAPError('Invalid ICAP Encapsulated header')
        offsets[name] = int(offset)
    values = list(offsets.values())
    if 'res-hdr' not in offsets or list(offsets)[-1] not in ('res-body', 'null-body') or values != sorted(values) or values[0] != 0:
        raise ICAPError('Invalid ICAP Encapsulated header')
    return offsets


def _read_chunked_body(stream: BinaryIO, limit: int) -> bytes:
    """
    Read an ICAP message body with chunked transfer coding.

    :param stream: The buffered socket stream.
    :param int limit: Maximum size of the body.
    :returns: The body.
    :raises ICAPError: If the body is invalid or larger than the limit.
    """
    body = b''
    while True:
        line = stream.readline(MAX_HEADER_SIZE + 1)
        size = line.split(b';', 1)[0].strip()
        if not line.endswith(b'\n') or not size or size.strip(b'0123456789abcdefABCDEF'):
            raise ICAPError('Invalid ICAP chunk size')
        size = int(size, 16)
        if size == 0:
            _read_headers(stream)
            return body
        if len(body) + size > limit:
            raise ICAPError('ICAP server sent more data than submitted')
        body += _read_exact(stream, size)
        if _read_exact(stream, 2) != b'\r\n':
            raise ICAPError('Invalid ICAP chunk')


def _parse_unchanged_response(stream: BinaryIO, headers: Message, data: bytes) -> ScanResult:
    """
    Parse an ICAP 200 response without infection header.

    The server either blocks the data with an encapsulated HTTP 403 response or returns the complete data unchanged.
    Any other response is an error, because it does not show that the server scanned all data.

    :param stream: The buffered socket stream.
    :param headers: The ICAP header fields.
    :param bytes data: The submitted data.
    :returns: The scan result.
    :raises ICAPError: If the response does not contain a valid scan result.
    """
    offsets = _parse_encapsulated(_header(headers, 'Encapsulated'))
    if offsets['res-hdr'] > MAX_HEADER_SIZE:
        raise ICAPError('Invalid ICAP Encapsulated header')
    _read_exact(stream, offsets['res-hdr'])
    http_status, http_status_line = _read_status(stream, b'HTTP')
    _read_headers(stream)
    if http_status == 403:
        return ScanResult(True, http_status_line.decode('latin-1'))
    if http_status != 200:
        raise ICAPError(f'ICAP server returned the encapsulated HTTP status {http_status}')
    body = _read_chunked_body(stream, len(data)) if 'res-body' in offsets else b''
    if body != data:
        raise ICAPError('ICAP server returned changed or incomplete data')
    return ScanResult(False)


def _parse_response(stream: BinaryIO, data: bytes) -> ScanResult:
    """
    Parse the ICAP response and decide whether the data is infected.

    :param stream: The buffered socket stream.
    :param bytes data: The submitted data.
    :returns: The scan result.
    :raises ICAPError: If the response is invalid or the server could not scan the data.
    """
    status, _status_line = _read_status(stream, b'ICAP')
    headers = _read_headers(stream)

    threat = next((value for name in INFECTION_HEADERS if (value := _header(headers, name))), None)
    if status == 204:
        return ScanResult(bool(threat), threat)
    if status == 200:
        if threat:
            return ScanResult(True, threat)
        return _parse_unchanged_response(stream, headers, data)
    raise ICAPError.from_status(status)


def _build_request(target: ICAPTarget, data: bytes, filename: str) -> bytes:
    """
    Build an ICAP RESPMOD request that contains the data as HTTP response body.

    :param ICAPTarget target: The ICAP service.
    :param bytes data: The data to scan.
    :param str filename: Name of the file, used percent-encoded as path of the encapsulated HTTP request.
    :returns: The serialized request.
    """
    req_hdr = f'GET /{quote(filename, safe="")} HTTP/1.1\r\nHost: {target.netloc}\r\n\r\n'.encode('ascii')
    res_hdr = f'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(data)}\r\n\r\n'.encode('ascii')
    icap_hdr = (
        f'RESPMOD {target.uri} ICAP/1.0\r\n'
        f'Host: {target.netloc}\r\n'
        'User-Agent: Univention-ICAP-Client/1.0\r\n'
        'Allow: 204\r\n'
        f'Encapsulated: req-hdr=0, res-hdr={len(req_hdr)}, res-body={len(req_hdr) + len(res_hdr)}\r\n'
        '\r\n'
    ).encode()
    body = (b'%x\r\n%s\r\n' % (len(data), data) if data else b'') + b'0\r\n\r\n'
    return icap_hdr + req_hdr + res_hdr + body


def _resolve(target: ICAPTarget, deadline: float) -> list:
    """
    Resolve the host of the target within the deadline.

    Numeric addresses are used directly. Host names are looked up in a helper thread, because
    :func:`socket.getaddrinfo` can't be interrupted. At most :data:`MAX_LOOKUPS` lookups run at the same time,
    so that expired lookups don't accumulate threads.

    :param ICAPTarget target: The ICAP service.
    :param float deadline: Time from :func:`time.monotonic` until which the scan must finish.
    :returns: The addresses from :func:`socket.getaddrinfo`.
    :raises ICAPError: If the lookup fails or doesn't finish in time.
    """
    try:
        return socket.getaddrinfo(target.host, target.port, type=socket.SOCK_STREAM, flags=socket.AI_NUMERICHOST)
    except OSError:
        pass

    result: list = []

    def lookup() -> None:
        try:
            result.append(socket.getaddrinfo(target.host, target.port, type=socket.SOCK_STREAM))
        except OSError as exc:
            result.append(exc)
        finally:
            _lookup_slots.release()

    if not _lookup_slots.acquire(timeout=max(deadline - time.monotonic(), 0)):
        raise ICAPError(f'Could not resolve ICAP server {target.host} in time')
    thread = threading.Thread(target=lookup, name='icap_getaddrinfo', daemon=True)
    try:
        if deadline <= time.monotonic():
            raise ICAPError(f'Could not resolve ICAP server {target.host} in time')
        thread.start()
    except BaseException:
        _lookup_slots.release()
        raise
    thread.join(max(deadline - time.monotonic(), 0))
    if not result:
        raise ICAPError(f'Could not resolve ICAP server {target.host} in time')
    if isinstance(result[0], OSError):
        raise ICAPError(f'Could not resolve ICAP server {target.host}: {result[0]}') from result[0]
    return result[0]


def _tls_context(cafile: str | None) -> ssl.SSLContext:
    """
    Create the TLS context that verifies the certificate of the ICAP server.

    :param str cafile: Path to a PEM file with the CA certificates, or `None` for the CA certificates of the system.
    :returns: The TLS context.
    :raises ICAPError: If the CA file can't be loaded.
    """
    try:
        return ssl.create_default_context(cafile=cafile or None)
    except (OSError, ssl.SSLError) as exc:
        raise ICAPError(f'Could not load the CA file {cafile} for the ICAP server: {exc}') from exc


def _connect(target: ICAPTarget, deadline: float, cafile: str | None = None) -> socket.socket:
    """
    Connect to the ICAP server within the deadline.

    All addresses of the host share the deadline. The TLS handshake gets the time that is left after the connection.

    :param ICAPTarget target: The ICAP service.
    :param float deadline: Time from :func:`time.monotonic` until which the scan must finish.
    :param str cafile: Path to a PEM file with the CA certificates for the TLS connection, see :func:`scan`.
    :returns: The connected socket, with TLS if the target requires it.
    :raises ICAPError: If no address is reachable in time, the CA file can't be loaded or the TLS handshake fails.
    """
    context = _tls_context(cafile) if target.tls else None
    error: OSError | None = None
    for family, socktype, proto, _canonname, address in _resolve(target, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sock = None
        try:
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(remaining)
            sock.connect(address)
        except OSError as exc:
            if sock is not None:
                sock.close()
            error = exc
            continue
        if not target.tls:
            return sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sock.close()
            break
        sock.settimeout(remaining)
        try:
            return context.wrap_socket(sock, server_hostname=target.host)
        except OSError as exc:
            sock.close()
            raise ICAPError(f'TLS handshake with ICAP server {target.netloc} failed: {exc}') from exc
    if error is None or deadline - time.monotonic() <= 0:
        raise ICAPError(f'Could not connect to ICAP server {target.netloc} in time')
    raise ICAPError(f'Connection to ICAP server {target.netloc} failed: {error}') from error


def scan(data: bytes, url: str, timeout: float = 30.0, filename: str = 'upload', cafile: str | None = None) -> ScanResult:
    """
    Scan data for malware with an ICAP server.

    The client sends a ``RESPMOD`` request over TCP.
    This works with `c-icap` and ClamAV as used in openDesk.

    :param bytes data: The data to scan.
    :param str url: URL of the ICAP service, for example ``icap://antivir-icap:1344/avscan``.
    :param float timeout: Timeout in seconds for the complete scan, including name resolution, connection and TLS handshake.
    :param str filename: Name of the file, which some ICAP servers show in the report.
    :param str cafile: Path to a PEM file with the CA certificates that signed the certificate of the ICAP server,
        for ``icaps://`` URLs. By default the CA certificates of the system are used. The certificate is always verified.
    :returns: The scan result.
    :raises ValueError: If the URL is not a valid ICAP URL or the timeout is negative.
    :raises ICAPError: If the ICAP server is not available, could not scan the data or the timeout expired.
    """
    if timeout < 0:
        raise ValueError('The timeout must not be negative')
    target = ICAPTarget.from_url(url)
    request = _build_request(target, data, filename)
    deadline = time.monotonic() + timeout
    expired = threading.Event()
    conn = _connect(target, deadline, cafile)

    def abort() -> None:
        expired.set()
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    watchdog = threading.Timer(max(deadline - time.monotonic(), 0), abort)
    watchdog.daemon = True
    watchdog.start()
    try:
        with conn, conn.makefile('rb') as stream:
            conn.sendall(request)
            result = _parse_response(stream, data)
    except (OSError, ICAPError) as exc:
        if expired.is_set():
            raise ICAPError(f'The ICAP server did not answer within {timeout:g} seconds') from exc
        if isinstance(exc, ICAPError):
            raise
        raise ICAPError(f'Connection to ICAP server {target.netloc} failed: {exc}') from exc
    finally:
        watchdog.cancel()
    if expired.is_set():
        raise ICAPError(f'The ICAP server did not answer within {timeout:g} seconds')
    return result
