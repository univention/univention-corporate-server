#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import errno
import shutil
import socket
import ssl
import subprocess
import threading
import time
from collections.abc import Iterator

import pytest


CLEAN = b'ICAP/1.0 204 No Content\r\nISTag: "test"\r\n\r\n'
INFECTED = (
    b'ICAP/1.0 200 OK\r\n'
    b'ISTag: "test"\r\n'
    b'X-Infection-Found: Type=0; Resolution=2; Threat=Eicar-Signature;\r\n'
    b'Encapsulated: res-hdr=0, res-body=42\r\n'
    b'\r\n'
    b'HTTP/1.0 403 Forbidden\r\nServer: C-ICAP\r\n\r\n'
)
FORBIDDEN = (
    b'ICAP/1.0 200 OK\r\n'
    b'Encapsulated: res-hdr=0, res-body=27\r\n'
    b'\r\n'
    b'HTTP/1.1 403 VirusFound\r\n\r\n'
)
UNMODIFIED = (
    b'ICAP/1.0 200 OK\r\n'
    b'Encapsulated: res-hdr=0, res-body=19\r\n'
    b'\r\n'
    b'HTTP/1.1 200 OK\r\n\r\n'
    b'2\r\nda\r\n2;ext=1\r\nta\r\n0\r\n\r\n'
)
C_ICAP_INFECTED = (
    b'ICAP/1.0 200 OK\r\n'
    b'Server: C-ICAP/0.6.4\r\n'
    b'X-Infection-Found: Type=0; Resolution=2; Threat=Eicar-Test-Signature;\r\n'
    b'X-Violations-Found: 1\r\n'
    b'\tjpegPhoto\r\n'
    b'\tEicar-Test-Signature\r\n'
    b'Encapsulated: res-hdr=0, res-body=42\r\n'
    b'\r\n'
    b'HTTP/1.0 403 Forbidden\r\nServer: C-ICAP\r\n\r\n'
    b'0\r\n\r\n'
)
FOLDED_THREAT = (
    b'ICAP/1.0 204 No Content\r\n'
    b'X-Violations-Found: 1\r\n'
    b'\tjpegPhoto\r\n'
    b'\tEicar-Test-Signature\r\n'
    b'\r\n'
)
TOO_MANY_HEADERS = b'ICAP/1.0 204 No Content\r\n' + b''.join(b'X-Header-%d: 1\r\n' % i for i in range(101)) + b'\r\n'
LONG_STATUS = b'ICAP/1.0 204 ' + b'x' * 70000 + b'\r\n\r\n'
BLOCKED = b'ICAP/1.0 500 Server Error\r\nX-Error-Code: file_type_blocked\r\n\r\n'
SERVER_ERROR = b'ICAP/1.0 500 Server Error\r\n\r\n'
NOT_FOUND = b'ICAP/1.0 404 Service Not Found\r\n\r\n'
UNMODIFIED_HEAD = b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, res-body=19\r\n\r\nHTTP/1.1 200 OK\r\n\r\n'


class FakeICAPServer:
    """ICAP server that stores one request and sends a fixed response."""

    def __init__(self, response: bytes) -> None:
        """
        Start the server on a free local port.

        :param bytes response: The raw bytes to send after the request was received.
        """
        self.response = response
        self.request = b''
        self.sock = socket.create_server(('127.0.0.1', 0))
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        """Receive one request and send the response."""
        conn, _addr = self.sock.accept()
        with conn:
            while not self.request.endswith(b'0\r\n\r\n'):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                self.request += chunk
            conn.sendall(self.response)

    @property
    def url(self) -> str:
        """URL of the ICAP service."""
        return f'icap://127.0.0.1:{self.port}/avscan'

    def close(self) -> None:
        """Stop the server."""
        self.thread.join(5)
        self.sock.close()


@pytest.fixture
def server(request: pytest.FixtureRequest) -> Iterator[FakeICAPServer]:
    srv = FakeICAPServer(request.param)
    yield srv
    srv.close()


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_sends_respmod_request(icap, server):
    data = b'\x00\x01binary\r\ndata'
    result = icap.scan(data, server.url, timeout=5, filename='my photo.jpg')
    assert result == icap.ScanResult(False)
    head, _sep, body = server.request.partition(b'\r\n\r\n')
    lines = head.split(b'\r\n')
    assert lines[0] == f'RESPMOD icap://127.0.0.1:{server.port}/avscan ICAP/1.0'.encode()
    assert b'Allow: 204' in lines
    req_hdr = f'GET /my%20photo.jpg HTTP/1.1\r\nHost: 127.0.0.1:{server.port}\r\n\r\n'.encode()
    res_hdr = f'HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(data)}\r\n\r\n'.encode()
    assert f'Encapsulated: req-hdr=0, res-hdr={len(req_hdr)}, res-body={len(req_hdr) + len(res_hdr)}'.encode() in lines
    assert body == req_hdr + res_hdr + b'%x\r\n' % len(data) + data + b'\r\n0\r\n\r\n'


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_empty_data(icap, server):
    assert not icap.scan(b'', server.url, timeout=5).infected
    assert server.request.endswith(b'Content-Length: 0\r\n\r\n0\r\n\r\n')


@pytest.mark.parametrize('server,infected,threat', [
    (CLEAN, False, None),
    (UNMODIFIED, False, None),
    (INFECTED, True, 'Type=0; Resolution=2; Threat=Eicar-Signature;'),
    (FORBIDDEN, True, 'HTTP/1.1 403 VirusFound'),
    (C_ICAP_INFECTED, True, 'Type=0; Resolution=2; Threat=Eicar-Test-Signature;'),
    (FOLDED_THREAT, True, '1 jpegPhoto Eicar-Test-Signature'),
    (UNMODIFIED_HEAD + b'4\r\ndata\r\n0\r\nX-Trailer: 1\r\n\r\n', False, None),
    (b'ICAP/1.0 204 No Content\nISTag: "test"\n\n', False, None),
], indirect=['server'])
def test_scan_result(icap, server, infected, threat):
    assert icap.scan(b'data', server.url, timeout=5) == icap.ScanResult(infected, threat)


@pytest.mark.parametrize('server', [
    SERVER_ERROR,
    BLOCKED,
    NOT_FOUND,
    b'garbage\r\n\r\n',
    b'',
    TOO_MANY_HEADERS,
    LONG_STATUS,
    b'ICAP/1.0 204 No Content\r\n' + b'X-Long: ' + b'x' * 70000 + b'\r\n\r\n',
    b'ICAP/1.0 20x OK\r\n\r\n',
    b'ICAP/1.0 204 No Content\r\n',
    b'ICAP/1.0 204 No Content\r\nISTag: "test"\r\n',
    b'ICAP/1.0 204 No Content\r\nISTag: "test"\r\n\r',
], indirect=True)
def test_scan_invalid_response(icap, server):
    with pytest.raises(icap.ICAPError):
        icap.scan(b'data', server.url, timeout=5)


def test_scan_connection_refused(icap):
    with socket.create_server(('127.0.0.1', 0)) as sock:
        port = sock.getsockname()[1]
    with pytest.raises(icap.ICAPError, match='Connection to ICAP server'):
        icap.scan(b'data', f'icap://127.0.0.1:{port}/avscan', timeout=5)


@pytest.mark.parametrize('url,expected', [
    ('icap://antivir-icap/avscan', ('antivir-icap', 1344, 'avscan', False)),
    ('icap://antivir-icap:1345/avscan/', ('antivir-icap', 1345, 'avscan', False)),
    (' icaps://[::1]:11344/srv_clamav ', ('::1', 11344, 'srv_clamav', True)),
    ('icap://antivir-icap/avscan?allow204=on&sizelimit=off', ('antivir-icap', 1344, 'avscan', False, 'allow204=on&sizelimit=off')),
])
def test_target_from_url(icap, url, expected):
    assert icap.ICAPTarget.from_url(url) == icap.ICAPTarget(*expected)


@pytest.mark.parametrize('url', [
    'http://host/avscan',
    'icap://host',
    'icap:///avscan',
    'host:1344',
    'icap://host/avscan#fragment',
    'icap://host/avscan#',
    'icap://host/av\r\nX-Injected: yes',
    'icap://host/av scan',
    'icap://host/avscän',
    'icap://host:port/avscan',
    'icap://ho\tst/avscan',
    'icap://user@host/av"scan',
])
def test_target_from_url_invalid(icap, url):
    with pytest.raises(ValueError):
        icap.ICAPTarget.from_url(url)


def test_target_uri(icap):
    target = icap.ICAPTarget('::1', 1344, 'avscan')
    assert target.netloc == '[::1]:1344'
    assert target.uri == 'icap://[::1]:1344/avscan'
    assert icap.ICAPTarget('host', 1344, 'avscan', query='a=1&b=2').uri == 'icap://host:1344/avscan?a=1&b=2'


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_sends_query(icap, server):
    icap.scan(b'data', server.url + '?allow204=on', timeout=5)
    assert server.request.startswith(f'RESPMOD icap://127.0.0.1:{server.port}/avscan?allow204=on ICAP/1.0\r\n'.encode())


@pytest.mark.parametrize('filename,path', [
    ('jpegPhoto', b'/jpegPhoto'),
    ('../../etc/passwd', b'/..%2F..%2Fetc%2Fpasswd'),
    ('a\r\nX-Injected: yes', b'/a%0D%0AX-Injected%3A%20yes'),
    ('Bild ä?#%.jpg', b'/Bild%20%C3%A4%3F%23%25.jpg'),
    ('', b'/'),
])
def test_build_request_escapes_filename(icap, filename, path):
    request = icap._build_request(icap.ICAPTarget('127.0.0.1', 1344, 'avscan'), b'data', filename)
    _icap_hdr, _sep, encapsulated = request.partition(b'\r\n\r\n')
    assert encapsulated.startswith(b'GET ' + path + b' HTTP/1.1\r\nHost: 127.0.0.1:1344\r\n\r\n')
    assert b'\r\nX-Injected' not in request


def test_build_request_ipv6_host_header(icap):
    request = icap._build_request(icap.ICAPTarget('::1', 1344, 'avscan'), b'', 'upload')
    assert request.count(b'\r\nHost: [::1]:1344\r\n') == 2


@pytest.mark.parametrize('kwargs', [
    {'host': ''},
    {'host': 'host\r\nX-Injected: yes'},
    {'host': 'host/avscan'},
    {'host': 'user@host'},
    {'host': 'häst'},
    {'port': 0},
    {'port': 65536},
    {'port': '1344'},
    {'service': ''},
    {'service': 'av\r\nX-Injected: yes'},
    {'service': 'av scan'},
    {'service': 'avscan?x=1'},
    {'query': 'a=1 ICAP/1.0'},
    {'query': 'a=1\r\nX-Injected: yes'},
    {'query': 'a=1#b'},
])
def test_target_invalid(icap, kwargs):
    values = {'host': 'host', 'port': 1344, 'service': 'avscan', **kwargs}
    with pytest.raises(ValueError):
        icap.ICAPTarget(**values)


@pytest.mark.parametrize('server,status,text', [
    (b'ICAP/1.0 404 Service not found\r\n\r\n', 404, 'rejected the request'),
    (b'ICAP/1.0 500 Server error\r\n\r\n', 500, 'could not scan'),
    (b'ICAP/1.0 206 Partial Content\r\n\r\n', 206, 'only 200 and 204'),
    (b'ICAP/1.0 301 Moved Permanently\r\nLocation: icap://evil/avscan\r\n\r\n', 301, 'only 200 and 204'),
], indirect=['server'])
def test_scan_error_status(icap, server, status, text):
    with pytest.raises(icap.ICAPError) as exc:
        icap.scan(b'data', server.url, timeout=5)
    assert exc.value.status == status
    assert text in str(exc.value)


@pytest.mark.parametrize('server', [
    b'ICAP/1.0 500 /var/lib/secret internal path\r\n\r\n',
    b'garbage /var/lib/secret\r\n\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, res-body=10\r\n\r\nHTTP/9 /var/lib/secret\r\n\r\n',
], indirect=True)
def test_scan_error_hides_server_content(icap, server):
    with pytest.raises(icap.ICAPError) as exc:
        icap.scan(b'data', server.url, timeout=5)
    assert 'secret' not in str(exc.value)


@pytest.mark.parametrize('server', [
    UNMODIFIED_HEAD,
    UNMODIFIED_HEAD + b'4\r\ndata\r\n',
    UNMODIFIED_HEAD + b'2\r\nda\r\n0\r\n\r\n',
    UNMODIFIED_HEAD + b'4\r\nDATA\r\n0\r\n\r\n',
    UNMODIFIED_HEAD + b'6\r\ndata!!\r\n0\r\n\r\n',
    UNMODIFIED_HEAD + b'4\r\ndataXX0\r\n\r\n',
    UNMODIFIED_HEAD + b'z\r\ndata\r\n0\r\n\r\n',
    UNMODIFIED_HEAD + b'4\r\ndata\r\n0\r\n',
    UNMODIFIED_HEAD + b'4\r\ndata\r\n0\r\nX-Trailer: 1\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, res-body=19\r\n\r\nHTTP/1.1 200 OK\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, null-body=19\r\n\r\nHTTP/1.1 200 OK\r\n\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, res-body=19\r\n\r\nHTTP/1.1 503 Unavailable\r\n\r\n0\r\n\r\n',
    b'ICAP/1.0 200 OK\r\n\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-body=0\r\n\r\n0\r\n\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=5, res-body=0\r\n\r\n0\r\n\r\n',
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, res-hdr=0, res-body=19\r\n\r\n',
], indirect=True)
def test_scan_incomplete_or_changed_response(icap, server):
    with pytest.raises(icap.ICAPError):
        icap.scan(b'data', server.url, timeout=5)


@pytest.mark.parametrize('server', [
    (
        b'ICAP/1.0 200 OK\r\nEncapsulated: req-hdr=0, res-hdr=18, res-body=37\r\n\r\n'
        b'GET / HTTP/1.1\r\n\r\nHTTP/1.1 200 OK\r\n\r\n0\r\n\r\n'
    ),
    b'ICAP/1.0 200 OK\r\nEncapsulated: res-hdr=0, null-body=19\r\n\r\nHTTP/1.1 200 OK\r\n\r\n',
], indirect=True)
def test_scan_unmodified_empty_data(icap, server):
    assert icap.scan(b'', server.url, timeout=5) == icap.ScanResult(False)


class SlowICAPServer(FakeICAPServer):
    """ICAP server that sends the response one byte at a time."""

    delay = 0.1

    def _serve(self) -> None:
        """Receive one request and send the response slowly."""
        conn, _addr = self.sock.accept()
        with conn:
            while not self.request.endswith(b'0\r\n\r\n'):
                self.request += conn.recv(65536)
            try:
                for byte in self.response:
                    conn.sendall(bytes([byte]))
                    time.sleep(self.delay)
            except OSError:
                pass


def test_scan_reads_response_that_arrives_in_parts(icap):
    server = SlowICAPServer(UNMODIFIED_HEAD + b'4\r\ndata\r\n0\r\n\r\n')
    server.delay = 0.01
    try:
        assert icap.scan(b'data', server.url, timeout=5) == icap.ScanResult(False)
    finally:
        server.close()


def test_scan_timeout_applies_to_complete_scan(icap):
    server = SlowICAPServer(CLEAN)
    try:
        start = time.monotonic()
        with pytest.raises(icap.ICAPError, match=r'did not answer within 0\.5 seconds'):
            icap.scan(b'data', server.url, timeout=0.5)
        assert time.monotonic() - start < 2
    finally:
        server.close()


def test_scan_negative_timeout(icap):
    with pytest.raises(ValueError):
        icap.scan(b'data', 'icap://127.0.0.1/avscan', timeout=-1)


@pytest.fixture
def blackhole_port() -> Iterator[int]:
    """Port where a TCP connection attempt hangs until its timeout, because the listen backlog is full."""
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(0)
    port = server.getsockname()[1]
    filler = [socket.create_connection(('127.0.0.1', port), timeout=1)]
    try:
        yield port
    finally:
        for sock in filler:
            sock.close()
        server.close()


def addresses(*ports: int) -> list:
    return [(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('127.0.0.1', port)) for port in ports]


@pytest.fixture
def blocked_dns(icap, monkeypatch) -> Iterator[threading.Event]:
    """Block host name lookups until the returned event is set, numeric addresses still work."""
    real_getaddrinfo = socket.getaddrinfo
    release = threading.Event()

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if flags & socket.AI_NUMERICHOST:
            return real_getaddrinfo(host, port, family, type, proto, flags)
        release.wait(10)
        return addresses(1)

    monkeypatch.setattr(icap.socket, 'getaddrinfo', getaddrinfo)
    try:
        yield release
    finally:
        release.set()
        for _ in range(100):
            if icap._lookup_slots._value == icap.MAX_LOOKUPS:
                break
            time.sleep(.05)
        assert icap._lookup_slots._value == icap.MAX_LOOKUPS


def lookup_threads() -> list:
    return [thread for thread in threading.enumerate() if thread.name == 'icap_getaddrinfo']


def test_scan_timeout_covers_slow_dns(icap, blocked_dns):
    start = time.monotonic()
    with pytest.raises(icap.ICAPError, match=r'resolve ICAP server .* in time'):
        icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=0.2)
    assert time.monotonic() - start < 0.8


def test_dns_threads_are_bounded(icap, blocked_dns):
    for _ in range(icap.MAX_LOOKUPS + 2):
        start = time.monotonic()
        with pytest.raises(icap.ICAPError, match=r'resolve ICAP server .* in time'):
            icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=0.1)
        assert time.monotonic() - start < 0.5
    assert len(lookup_threads()) == icap.MAX_LOOKUPS
    blocked_dns.set()
    for thread in lookup_threads():
        thread.join(2)
    assert not lookup_threads()


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_numeric_addresses_work_while_all_lookups_are_blocked(icap, blocked_dns, server):
    for _ in range(icap.MAX_LOOKUPS):
        with pytest.raises(icap.ICAPError, match=r'resolve ICAP server .* in time'):
            icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=0.1)
    assert icap._lookup_slots._value == 0
    assert icap.scan(b'data', server.url, timeout=5) == icap.ScanResult(False)
    with pytest.raises(icap.ICAPError, match=r'Connection to ICAP server \[::1\]:1 failed'):
        icap.scan(b'data', 'icap://[::1]:1/avscan', timeout=5)


def test_scan_socket_creation_error(icap, monkeypatch):
    def no_socket(*args, **kwargs):
        raise OSError(errno.EMFILE, 'Too many open files')

    monkeypatch.setattr(icap.socket, 'socket', no_socket)
    with pytest.raises(icap.ICAPError, match=r'Connection to ICAP server .* failed: .*Too many open files'):
        icap.scan(b'data', 'icap://127.0.0.1:1/avscan', timeout=5)


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_uses_next_address_after_socket_creation_error(icap, monkeypatch, server):
    unsupported = (9999, socket.SOCK_STREAM, 0, '', ('127.0.0.1', server.port))
    monkeypatch.setattr(icap.socket, 'getaddrinfo', lambda *args, **kwargs: [unsupported, *addresses(server.port)])
    assert icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=5) == icap.ScanResult(False)


def test_scan_dns_failure(icap, monkeypatch):
    def failing_getaddrinfo(*args, **kwargs):
        raise socket.gaierror('Name or service not known')

    monkeypatch.setattr(icap.socket, 'getaddrinfo', failing_getaddrinfo)
    with pytest.raises(icap.ICAPError, match='Could not resolve ICAP server antivir-icap: '):
        icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=5)


def test_scan_timeout_covers_all_connection_attempts(icap, monkeypatch, blackhole_port):
    monkeypatch.setattr(icap.socket, 'getaddrinfo', lambda *args, **kwargs: addresses(blackhole_port, blackhole_port, blackhole_port))
    start = time.monotonic()
    with pytest.raises(icap.ICAPError, match=r'connect to ICAP server .* in time'):
        icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=0.5)
    assert time.monotonic() - start < 1


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_uses_next_address_after_refused_connection(icap, monkeypatch, server):
    with socket.create_server(('127.0.0.1', 0)) as sock:
        refused_port = sock.getsockname()[1]
    monkeypatch.setattr(icap.socket, 'getaddrinfo', lambda *args, **kwargs: addresses(refused_port, server.port))
    assert icap.scan(b'data', 'icap://antivir-icap/avscan', timeout=5) == icap.ScanResult(False)


def test_scan_timeout_covers_tls_handshake(icap, monkeypatch):
    server = FakeICAPServer(b'')
    server.response = b''
    try:
        start = time.monotonic()
        with pytest.raises(icap.ICAPError, match=r'TLS handshake with ICAP server .* failed'):
            icap.scan(b'data', f'icaps://127.0.0.1:{server.port}/avscan', timeout=0.5)
        assert time.monotonic() - start < 1
    finally:
        server.close()


class TLSICAPServer(FakeICAPServer):
    """ICAP server behind TLS with a self-signed certificate."""

    def __init__(self, response: bytes, certificate: str, key: str) -> None:
        """
        Start the server with the given certificate.

        :param bytes response: The raw bytes to send after the request was received.
        :param str certificate: Path to the PEM certificate.
        :param str key: Path to the PEM private key.
        """
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certificate, key)
        super().__init__(response)

    def _serve(self) -> None:
        """Receive one request over TLS and send the response."""
        conn, _addr = self.sock.accept()
        try:
            with self.context.wrap_socket(conn, server_side=True) as tls:
                while not self.request.endswith(b'0\r\n\r\n'):
                    chunk = tls.recv(65536)
                    if not chunk:
                        break
                    self.request += chunk
                tls.sendall(self.response)
        except ssl.SSLError:
            conn.close()

    @property
    def url(self) -> str:
        """URL of the ICAP service."""
        return f'icaps://127.0.0.1:{self.port}/avscan'


@pytest.fixture(scope='module')
def certificate(tmp_path_factory) -> tuple[str, str]:
    """Self-signed certificate for 127.0.0.1 and its key, created with the openssl command."""
    if not shutil.which('openssl'):
        pytest.skip('openssl is not installed')
    path = tmp_path_factory.mktemp('tls')
    cert, key = str(path / 'cert.pem'), str(path / 'key.pem')
    subprocess.run([
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=127.0.0.1',
        '-addext', 'subjectAltName=IP:127.0.0.1', '-keyout', key, '-out', cert,
    ], check=True, capture_output=True)
    return cert, key


@pytest.fixture
def tls_server(certificate) -> Iterator[TLSICAPServer]:
    server = TLSICAPServer(CLEAN, *certificate)
    try:
        yield server
    finally:
        server.close()


def test_scan_tls_with_ca_file(icap, tls_server, certificate):
    assert icap.scan(b'data', tls_server.url, timeout=5, cafile=certificate[0]) == icap.ScanResult(False)
    assert tls_server.request.startswith(b'RESPMOD icap://127.0.0.1:')


def test_scan_tls_rejects_unknown_certificate(icap, tls_server):
    with pytest.raises(icap.ICAPError, match=r'TLS handshake with ICAP server .* failed: .*CERTIFICATE_VERIFY_FAILED'):
        icap.scan(b'data', tls_server.url, timeout=5)


def test_scan_tls_missing_ca_file(icap, tls_server, tmp_path):
    with pytest.raises(icap.ICAPError, match='Could not load the CA file'):
        icap.scan(b'data', tls_server.url, timeout=5, cafile=str(tmp_path / 'missing.pem'))


@pytest.mark.parametrize('server', [CLEAN], indirect=True)
def test_scan_ignores_ca_file_without_tls(icap, server, tmp_path):
    assert icap.scan(b'data', server.url, timeout=5, cafile=str(tmp_path / 'missing.pem')) == icap.ScanResult(False)
