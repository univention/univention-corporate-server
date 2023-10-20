#!/usr/bin/python3
"""Simple HTTP Proxy for ucs-test."""
# Inspired by <http://effbot.org/librarybook/simplehttpserver.htm>

import base64
import http.client
import os
import shutil
import socket
from argparse import ArgumentParser, Namespace
from functools import wraps
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from select import select
from typing import Any, Callable, TypeVar, cast
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


FuncT = TypeVar("FuncT", bound=Callable[..., None])

PORT = 3128
options = Namespace()


def _auth(f: FuncT) -> FuncT:
    @wraps(f)
    def wrapper(self, *args: Any, **kwargs: Any) -> None:
        if options.authorization:
            try:
                auth = self.headers.get('Proxy-Authorization', '')
                if not auth.lower().startswith('basic '):
                    raise KeyError("Only Basic authentication: %s" % auth)
                auth = auth[len('Basic '):]
                auth = base64.b64decode(auth).decode('UTF-8')
                username, password = auth.split(':', 1)
                username, password = unquote(username), unquote(password)
                if username != options.username:
                    msg = f"Username: {username} != {options.username}"
                    if options.verbose:
                        self.log_error(msg)
                    raise KeyError(msg)

                if password != options.password:
                    msg = f"Password: {password} != {options.password}"
                    if options.verbose:
                        self.log_error(msg)
                    raise KeyError(msg)
            except KeyError as exc:
                self.send_response(http.client.PROXY_AUTHENTICATION_REQUIRED)
                self.send_header('WWW-Authenticate', f'Basic realm="{options.realm}", charset="UTF-8"')
                self.send_header('Content-type', 'text/html; charset=UTF-8')
                self.end_headers()
                self.wfile.write(f'<html><body><h1>Error: Proxy authorization needed</h1>{exc}</body></html>'.encode('UTF-8'))
                return

        return f(self, *args, **kwargs)

    return cast(FuncT, wrapper)


class Proxy(BaseHTTPRequestHandler):
    server_version = "UCSTestProxy/1.0"
    VIA = '1.0 UCSTestProxy'

    @_auth
    def do_GET(self) -> None:
        self.common(data=True)

    @_auth
    def do_HEAD(self) -> None:
        self.common(data=False)

    def common(self, data: bool = True) -> None:
        # rewrite url
        url = urlsplit(self.path)
        u = list(url)
        # The proxy gets a verbatim copy of the URL, which might contain the
        # target site credentials, which httplib doesn't handle itself.
        if url.username is not None:
            u[1] = u[1].split('@', 1)[1]
            if "Authorization" not in self.headers:
                auth = "%s:%s" % (quote(url.username), quote(url.password or ""))
                auth = base64.b64encode(auth.encode("UTF-8")).decode("ASCII")
                self.headers["Authorization"] = "Basic %s" % (auth.rstrip(),)

        # Fake DNS resolve of configured hostname to localhost
        if options.translate and url.hostname == options.translate:
            u[1] = u[1].replace(options.translate, 'localhost')

        path = urlunsplit(u)
        try:
            req = Request(url=path, headers=self.headers)  # type: ignore
            if options.verbose:
                for k, v in self.headers.items():
                    self.log_message(f"> {k}: {v}")

            fp = urlopen(req)  # noqa: S310
        except HTTPError as exc:
            fp = exc
            if options.verbose:
                self.log_error("%d %s" % (fp.code, fp.msg))

        self.send_response(fp.code)
        via = self.VIA
        for k, v in fp.headers.items():
            if k.lower() == 'via':
                via = f"{via}, {v}"
            elif k.lower() in ('server', 'date'):  # Std-Hrds by BaseHTTPReqHand
                continue
            elif k.lower() == 'transfer-encoding':
                continue
            else:
                if options.verbose:
                    self.log_message(f"< {k}: {v}")
                self.send_header(k, v)

        self.send_header('Via', via)
        self.end_headers()
        if data:
            shutil.copyfileobj(fp, self.wfile)

        fp.close()

    @_auth
    def do_CONNECT(self) -> None:
        self.close_connection = True

        host, _, port = self.path.partition(":")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TODO: IPv6
        try:
            client.connect((host, int(port)))
            self.send_response(200)
            self.send_header('Via', self.VIA)
            self.end_headers()

            rlist = [self.connection, client]
            while rlist:
                reads, _, _ = select(rlist, [], [], 0)
                for read in reads:
                    data = read.recv(1024)
                    if data:
                        write = self.connection if read is client else client
                        write.sendall(data)  # FIXME: may block
                    else:
                        rlist.remove(read)
        except socket.error as exc:
            self.log_error(f"CONNECT: {exc}")
        finally:
            client.close()


def parse_args() -> None:
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=PORT, help='TCP port number')
    group = parser.add_argument_group("Proxy Authorization")
    group.add_argument('-a', '--authorization', action='store_true', help='Require use of proxy authorization')
    group.add_argument('-u', '--username', default='username', help='User name for HTTP Proxy authorization, unquoted')
    group.add_argument('-w', '--password', default='password', help='Password for HTTP Proxy authorization, unquoted')
    group.add_argument('-r', '--realm', default='realm', help='Realm for HTTP Proxy authorization')
    parser.add_argument('-t', '--translate', metavar='HOSTNAME', help='Translate requests for this host name to localhost')
    parser.add_argument('-f', '--fork', action='store_true', default=False, help='Fork daemon process')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Output verbose informations')
    parser.parse_args(namespace=options)


def main() -> None:
    parse_args()

    if socket.has_ipv6:
        ThreadingHTTPServer.address_family = socket.AF_INET6
        httpd = ThreadingHTTPServer(('::', options.port), Proxy)
    else:
        httpd = ThreadingHTTPServer(('', options.port), Proxy)

    if options.fork:
        pid = os.fork()
        if pid == 0:
            for fd in range(3):
                os.close(fd)
                fd2 = os.open(os.devnull, os.O_WRONLY if fd else os.O_RDONLY)
                if fd2 != fd:
                    os.dup2(fd2, fd)
                    os.close(fd2)
            httpd.serve_forever()
        else:
            print("proxy_pid=%d proxy_port=%d" % (pid, httpd.server_port))
    else:
        try:
            print("proxy_pid=%d proxy_port=%d" % (os.getpid(), httpd.server_port))
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
