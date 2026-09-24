#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import socket
import threading
from collections.abc import Iterator

import pytest


CLEAN = b'ICAP/1.0 204 No Content\r\nISTag: "test"\r\n\r\n'
INFECTED = (
    b'ICAP/1.0 200 OK\r\n'
    b'ISTag: "test"\r\n'
    b'X-Infection-Found: Type=0; Resolution=2; Threat=Eicar-Signature;\r\n'
    b'Encapsulated: res-hdr=0, res-body=45\r\n'
    b'\r\n'
    b'HTTP/1.0 403 Forbidden\r\nServer: C-ICAP\r\n\r\n'
)
FORBIDDEN = (
    b'ICAP/1.0 200 OK\r\n'
    b'Encapsulated: res-hdr=0, res-body=26\r\n'
    b'\r\n'
    b'HTTP/1.1 403 VirusFound\r\n\r\n'
)
UNMODIFIED = (
    b'ICAP/1.0 200 OK\r\n'
    b'Encapsulated: res-hdr=0, res-body=19\r\n'
    b'\r\n'
    b'HTTP/1.1 200 OK\r\n\r\n'
)
BLOCKED = b'ICAP/1.0 500 Server Error\r\nX-Error-Code: file_type_blocked\r\n\r\n'
SERVER_ERROR = b'ICAP/1.0 500 Server Error\r\n\r\n'
NOT_FOUND = b'ICAP/1.0 404 Service Not Found\r\n\r\n'


class FakeICAPServer:
    """ICAP server that stores one request and sends a fixed response."""

    def __init__(self, response: bytes) -> None:
        """
        Start the server on a free local port.

        Args:
            response: The raw bytes to send after the request was received.
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
    req_hdr = b'GET /my_photo.jpg HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n'
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
    (BLOCKED, True, 'file_type_blocked'),
], indirect=['server'])
def test_scan_result(icap, server, infected, threat):
    assert icap.scan(b'data', server.url, timeout=5) == icap.ScanResult(infected, threat)


@pytest.mark.parametrize('server', [SERVER_ERROR, NOT_FOUND, b'garbage\r\n\r\n', b''], indirect=True)
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
])
def test_target_from_url(icap, url, expected):
    assert icap.ICAPTarget.from_url(url) == icap.ICAPTarget(*expected)


@pytest.mark.parametrize('url', ['http://host/avscan', 'icap://host', 'icap:///avscan', 'host:1344'])
def test_target_from_url_invalid(icap, url):
    with pytest.raises(ValueError):
        icap.ICAPTarget.from_url(url)


def test_target_uri(icap):
    assert icap.ICAPTarget('::1', 1344, 'avscan').uri == 'icap://[::1]:1344/avscan'
