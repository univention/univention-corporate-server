#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2008-2021 Univention GmbH
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
"""
Univention Update tools.
"""

from __future__ import absolute_import
from __future__ import print_function
try:
    import univention.debug as ud
except ImportError:
    import univention.debug2 as ud  # type: ignore

# TODO: Convert to absolute imports only AFTER the unit test has been adopted
from .commands import (
    cmd_dist_upgrade,
    cmd_dist_upgrade_sim,
    cmd_update,
)
from .errors import (
    UnmetDependencyError,
    CannotResolveComponentServerError,
    ConfigurationError,
    DownloadError,
    PreconditionError,
    RequiredComponentError,
    ProxyError,
    VerificationError,
)
from .repo_url import UcsRepoUrl
from univention.lib.ucs import UCS_Version

import errno
import sys
import re
import os
import copy
from six.moves import http_client as httplib
import socket
from univention.config_registry import ConfigRegistry
from six.moves import urllib_request as urllib2, urllib_error
import json
import subprocess
import tempfile
import shutil
import logging
import atexit
import functools
import six
import base64
try:
    from typing import Any, AnyStr, Dict, Generator, Iterable, Iterator, List, Optional, Sequence, Set, Text, Tuple, Type, TypeVar, Union  # noqa F401
    from typing_extensions import Literal  # noqa F401
    _TS = TypeVar("_TS", bound="_UCSServer")
except ImportError:
    pass

if six.PY2:
    from new import instancemethod

RE_ALLOWED_DEBIAN_PKGNAMES = re.compile('^[a-z0-9][a-z0-9.+-]+$')
RE_SPLIT_MULTI = re.compile('[ ,]+')
RE_COMPONENT = re.compile(r'^repository/online/component/([^/]+)$')
RE_CREDENTIALS = re.compile(r'^repository/credentials/(?:(?P<realm>[^/]+)/)?(?P<key>[^/]+)$')

MIN_GZIP = 100  # size of non-empty gzip file
UUID_NULL = '00000000-0000-0000-0000-000000000000'


def verify_script(script, signature):
    # type: (bytes, bytes) -> Optional[bytes]
    """
    Verify detached signature of script:

    .. code-block: sh

        gpg -a -u 6B6E7E3259A9F44F1452D1BE36602BA86B8BFD3C --passphrase-file /etc/archive-keys/ucs4.0.txt -o script.sh.gpg -b script.sh
        repo-ng-sign-release-file --debug -k 6B6E7E3259A9F44F1452D1BE36602BA86B8BFD3C -p /etc/archive-keys/ucs4.0.txt  -i script.sh -o script.sh.gpg

    .. code-block: python

        verify_script(open("script.sh", "r").read(), open("script.sh.gpg", "r").read())

    :param str script: The script text to verify.
    :param str signature: The detached signature.
    :return: None or the error output.
    :rtype: None or str
    """
    # write signature to temporary file
    sig_fd, sig_name = tempfile.mkstemp()
    os.write(sig_fd, signature)
    os.close(sig_fd)

    # verify script
    cmd = ["apt-key", "verify", sig_name, "-"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, close_fds=True)
    stdout, _stderr = proc.communicate(script)
    ret = proc.wait()
    return stdout if ret != 0 else None


class _UCSRepo(UCS_Version):
    """
    Super class to build URLs for APT repositories.
    """

    def __init__(self, release=None, **kwargs):
        # type: (Optional[UCS_Version], **Any) -> None
        if release:
            super(_UCSRepo, self).__init__(release)
        kwargs.setdefault('patchlevel_reset', 0)
        kwargs.setdefault('patchlevel_max', 99)
        for (k, v) in kwargs.items():
            if isinstance(v, str) and '%(' in v:
                self.__dict__[k] = _UCSRepo._substitution(v, self.__dict__)
            else:
                self.__dict__[k] = v

    def __repr__(self):
        # type: () -> str
        return '%s(**%r)' % (self.__class__.__name__, self.__dict__)

    def _format(self, format):
        # type: (str) -> str
        """
        Format longest path for directory/file access.
        """
        while True:
            try:
                return format % self
            except KeyError as ex:
                (k,) = ex.args
                # strip missing part
                i = format.index('%%(%s)' % k)
                format = format[:i]
                # strip partial part
                try:
                    i = format.rindex('/') + 1
                except ValueError:
                    i = 0
                format = format[:i]

    class _substitution(object):
        """
        Helper to print dynamically substituted variable.

        >>> h={'major':2}
        >>> h['version'] = _UCSRepo._substitution('%(major)d.%(minor)d', h)
        >>> h['minor'] = 3
        >>> '%(version)s' % h
        '2.3'
        """

        def __init__(self, format, values):
            # type: (str, Any) -> None
            self.format = format
            self.values = values

        def __str__(self):
            # type: () -> str
            try:
                return self.format % self.values
            except KeyError as e:
                for (k, v) in self.values.items():
                    if self == v:
                        raise KeyError(k)
                raise e

        def __repr__(self):
            # type: () -> str
            return repr(self.format)

    def deb(self, server, type="deb"):
        # type: (_UCSServer, str) -> str
        """
        Format for :file:`/etc/apt/sources.list`.

        :param str server: The URL of the repository server.
        :param str type: The repository type, e.g. `deb` for a binary and `deb-src` for source package repository.
        :returns: The APT repository stanza.
        :rtype: str
        """
        raise NotImplementedError()

    def path(self, filename=None):
        # type: (str) -> str
        """
        Format pool for directory/file access.

        :param filename: The name of a file in the repository.
        :returns: relative path.
        :rtype: str
        """
        raise NotImplementedError()

    def clean(self, server):
        # type: (_UCSServer) -> str
        """
        Format for :file:`/etc/apt/mirror.list`

        :param str server: The URL of the repository server.
        :returns: The APT repository stanza.
        :rtype: str
        """
        raise NotImplementedError()


class UCSRepoPool5(_UCSRepo):
    """
    APT repository using the debian pool structure (ucs5 and above).
    """

    def __init__(self, release=None, **kwargs):
        # type: (UCS_Version, **Any) -> None
        kwargs.setdefault('version', UCS_Version.FORMAT)
        kwargs.setdefault('patch', UCS_Version.FULLFORMAT)
        kwargs.setdefault('errata', False)
        super(UCSRepoPool5, self).__init__(release, **kwargs)

    @property
    def _suite(self):  # type: () -> str
        """
        Format suite.

        :returns: UCS suite name.
        :rtype: str

        >>> UCSRepoPool5(major=5, minor=1, patchlevel=0)._suite
        'ucs510'
        >>> UCSRepoPool5(major=5, minor=1, patchlevel=0, errata=True)._suite
        'errata510'
        """
        return "{1}{0.major}{0.minor}{0.patchlevel}".format(self, "errata" if self.errata else "ucs")

    def deb(self, server, type="deb", mirror=False):
        # type: (_UCSServer, str, bool) -> str
        """
        Format for :file:`/etc/apt/sources.list`.

        :param str server: The URL of the repository server.
        :param str type: The repository type, e.g. `deb` for a binary and `deb-src` for source package repository.
        :param bool mirror: Also mirror files for Debian installer.
        :returns: The APT repository stanza.
        :rtype: str

        >>> r=UCSRepoPool5(major=5, minor=1, patchlevel=0)
        >>> r.deb('https://updates.software-univention.de/')
        'deb https://updates.software-univention.de/ ucs510 main'
        >>> r.deb('https://updates.software-univention.de/', mirror=True)
        'deb https://updates.software-univention.de/ ucs510 main main/debian-installer'
        >>> r=UCSRepoPool5(major=5, minor=1, patchlevel=0, errata=True)
        >>> r.deb('https://updates.software-univention.de/')
        'deb https://updates.software-univention.de/ errata510 main'
        """
        components = "main main/debian-installer" if mirror and not self.errata and type == "deb" else "main"
        return "%s %s %s %s" % (type, server, self._suite, components)

    def path(self, filename=None):
        # type: (str) -> str
        """
        Format pool for directory/file access.

        :param filename: The name of a file in the repository.
        :returns: relative path.
        :rtype: str

        >>> UCSRepoPool5(major=5, minor=1, patchlevel=0).path()
        'dists/ucs510/InRelease'
        >>> UCSRepoPool5(major=5, minor=1, patchlevel=0, errata=True).path()
        'dists/errata510/InRelease'
        """
        return "dists/{}/{}".format(self._suite, filename or 'InRelease')


class UCSRepoPool(_UCSRepo):
    """
    Flat Debian APT repository.
    """

    def __init__(self, **kw):
        # type: (**Any) -> None
        kw.setdefault('version', UCS_Version.FORMAT)
        kw.setdefault('patch', UCS_Version.FULLFORMAT)
        super(UCSRepoPool, self).__init__(**kw)

    def deb(self, server, type="deb"):
        # type: (_UCSServer, str) -> str
        """
        Format for :file:`/etc/apt/sources.list`.

        :param str server: The URL of the repository server.
        :param str type: The repository type, e.g. `deb` for a binary and `deb-src` for source package repository.
        :returns: The APT repository stanza.
        :rtype: str

        >>> r=UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained',arch='i386')
        >>> r.deb('https://updates.software-univention.de/')
        'deb https://updates.software-univention.de/2.3/maintained/ 2.3-1/i386/'
        """
        fmt = "%(version)s/%(part)s/ %(patch)s/%(arch)s/"
        return "%s %s%s" % (type, server, super(UCSRepoPool, self)._format(fmt))

    def path(self, filename=None):
        # type: (str) -> str
        """
        Format pool for directory/file access.

        :param filename: The name of a file in the repository.
        :returns: relative path.
        :rtype: str

        >>> UCSRepoPool(major=2,minor=3).path()
        '2.3/'
        >>> UCSRepoPool(major=2,minor=3,part='maintained').path()
        '2.3/maintained/'
        >>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained').path()
        '2.3/maintained/2.3-1/'
        >>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained',arch='i386').path()
        '2.3/maintained/2.3-1/i386/Packages.gz'
        """
        fmt = "%(version)s/%(part)s/%(patch)s/%(arch)s/" + (filename or 'Packages.gz')
        return super(UCSRepoPool, self)._format(fmt)

    def clean(self, server):
        # type: (_UCSServer) -> str
        """
        Format for :file:`/etc/apt/mirror.list`

        :param str server: The URL of the repository server.
        :returns: The APT repository stanza.
        :rtype: str
        """
        fmt = "%(version)s/%(part)s/%(patch)s/"  # %(arch)s/
        return "clean %s%s" % (server, super(UCSRepoPool, self)._format(fmt))


class UCSRepoPoolNoArch(_UCSRepo):
    """
    Flat Debian APT repository without explicit architecture subdirectory.
    """

    def __init__(self, **kw):
        # type: (**Any) -> None
        kw.setdefault('version', UCS_Version.FORMAT)
        kw.setdefault('patch', UCS_Version.FULLFORMAT)
        super(UCSRepoPoolNoArch, self).__init__(**kw)

    def deb(self, server, type="deb"):
        # type: (_UCSServer, str) -> str
        """
        Format for :file:`/etc/apt/sources.list`.

        :param str server: The URL of the repository server.
        :param str type: The repository type, e.g. `deb` for a binary and `deb-src` for source package repository.
        :returns: The APT repository stanza.
        :rtype: str

        >>> r=UCSRepoPoolNoArch(major=2,minor=3,patch='comp',part='maintained/component',arch='all')
        >>> r.deb('https://updates.software-univention.de/')
        'deb https://updates.software-univention.de/2.3/maintained/component/comp/ ./'
        """
        fmt = "%(version)s/%(part)s/%(patch)s/ ./"
        return "%s %s%s" % (type, server, super(UCSRepoPoolNoArch, self)._format(fmt))

    def path(self, filename=None):
        # type: (str) -> str
        """
        Format pool for directory/file access. Returns relative path.

        :param filename: The name of a file in the repository.
        :returns: relative path.
        :rtype: str

        >>> UCSRepoPoolNoArch(major=2,minor=3).path()
        '2.3/'
        >>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component').path()
        '2.3/maintained/component/'
        >>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component',patch='comp').path()
        '2.3/maintained/component/comp/Packages.gz'
        >>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component',patch='comp',arch='all').path()
        '2.3/maintained/component/comp/Packages.gz'
        """
        fmt = "%(version)s/%(part)s/%(patch)s/" + (filename or 'Packages.gz')
        return super(UCSRepoPoolNoArch, self)._format(fmt)

    def clean(self, server):
        # type: (_UCSServer) -> str
        """
        Format for :file:`/etc/apt/mirror.list`

        :param str server: The URL of the repository server.
        :returns: The APT repository stanza.
        :rtype: str
        """
        fmt = "%(version)s/%(part)s/%(patch)s/"
        return "clean %s%s" % (server, super(UCSRepoPoolNoArch, self)._format(fmt))


class _UCSServer(object):
    """
    Abstrace base class to access UCS compatible update server.
    """

    @classmethod
    def load_credentials(self, ucr):
        # type: (ConfigRegistry) -> None
        """
        Load credentials from UCR.

        :param ConfigRegistry ucr: An UCR instance.
        """
        pass

    def join(self, rel):
        # type: (str) -> str
        """
        Return joined URI without credential.

        :param str rel: relative URI.
        :return: The joined URI.
        :rtype: str
        """
        raise NotImplementedError()

    def access(self, repo, filename=None, get=False):
        # type: (Optional[_UCSRepo], str, bool) -> Tuple[int, int, bytes]
        """
        Access URI and optionally get data.

        :param _UCSRepo repo: the URI to access as an instance of :py:class:`_UCSRepo`.
        :param str filename: An optional relative path.
        :param bool get: Fetch data if True - otherwise check only.
        :return: a 3-tuple (code, size, content) or None on errors.
        :rtype: tuple(int, int, bytes)
        :raises DownloadError: if the server is unreachable.
        :raises ValueError: if the credentials use an invalid encoding.
        :raises ConfigurationError: if a permanent error in the configuration occurs, e.g. the credentials are invalid or the host is unresolvable.
        :raises ProxyError: if the HTTP proxy returned an error.
        """
        raise NotImplementedError()

    def __add__(self, rel):
        # type: (_TS, str) -> _TS
        """
        Append relative path component.

        :param str rel: Relative path.
        :return: A clone of this instance using the new base path.
        :rtype: UCSHttpServer
        """
        raise NotImplementedError()

    @property
    def prefix(self):
        # type: () -> str
        raise NotImplementedError()


class UCSHttpServer(_UCSServer):
    """
    Access to UCS compatible remote update server.
    """

    class HTTPHeadHandler(urllib2.BaseHandler):
        """
        Handle fallback from HEAD to GET if unimplemented.
        """

        def http_error_501(self, req, fp, code, msg, headers):  # httplib.NOT_IMPLEMENTED
            # type: (urllib2.Request, Any, int, str, Dict) -> Any
            m = req.get_method()
            if m == 'HEAD' == UCSHttpServer.http_method:
                ud.debug(ud.NETWORK, ud.INFO, "HEAD not implemented at %s, switching to GET." % req)
                UCSHttpServer.http_method = 'GET'
                return self.parent.open(req, timeout=req.timeout)
            else:
                return None

    def __init__(self, baseurl, user_agent=None, timeout=None):
        # type: (UcsRepoUrl, str, float) -> None
        """
        Setup URL handler for accessing a UCS repository server.

        :param UcsRepoUrl baseurl: the base URL.
        :param str user_agent: optional user agent string.
        :param int timeout: optional timeout for network access.
        """
        self.log.addHandler(logging.NullHandler())
        self.baseurl = baseurl
        self.user_agent = user_agent
        self.timeout = timeout

    log = logging.getLogger('updater.UCSHttp')

    http_method = 'HEAD'
    head_handler = HTTPHeadHandler()
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)
    proxy_handler = urllib2.ProxyHandler()
    # No need for ProxyBasicAuthHandler, since ProxyHandler parses netloc for @
    opener = urllib2.build_opener(head_handler, auth_handler, proxy_handler)
    failed_hosts = set()  # type: Set[str]

    @property
    def prefix(self):
        # type: () -> str
        return self.baseurl.path.lstrip('/')

    @classmethod
    def reinit(self):
        # type: () -> None
        """
        Reload proxy settings and reset failed hosts.
        """
        self.proxy_handler = urllib2.ProxyHandler()
        self.opener = urllib2.build_opener(self.head_handler, self.auth_handler, self.proxy_handler)
        self.failed_hosts.clear()

    @classmethod
    def load_credentials(self, ucr):
        # type: (ConfigRegistry) -> None
        """
        Load credentials from UCR.

        :param ConfigRegistry ucr: An UCR instance.
        """
        uuid = ucr.get('uuid/license', UUID_NULL)

        groups = {}  # type: Dict[str, Dict[str, str]]
        for key, value in ucr.items():
            match = RE_CREDENTIALS.match(key)
            if match:
                realm, key = match.groups()
                cfg = groups.setdefault(realm, {})
                cfg[key] = value

        for realm, cfg in groups.items():
            try:
                uris = cfg.pop('uris').split()
            except KeyError:
                self.log.error('Incomplete credentials for realm "%s": %r', realm, cfg)
                continue
            username = cfg.pop('username', uuid)
            password = cfg.pop('password', uuid)
            if cfg:
                self.log.warn('Extra credentials for realm "%s": %r', realm, cfg)

            self.password_manager.add_password(realm, uris, username, password)
            self.log.info('Loaded credentials for realm "%s"', realm)

    def __str__(self):
        # type: () -> str
        """
        URI with credentials.
        """
        return self.baseurl.private()

    def __repr__(self):
        # type: () -> str
        """
        Return canonical string representation.
        """
        return '%s(%r, timeout=%r)' % (
            self.__class__.__name__,
            self.baseurl,
            self.timeout,
        )

    def __add__(self, rel):
        # type: (str) -> UCSHttpServer
        """
        Append relative path component.

        :param str rel: Relative path.
        :return: A clone of this instance using the new base path.
        :rtype: UCSHttpServer
        """
        uri = copy.copy(self)
        uri.baseurl += rel
        return uri

    def join(self, rel):
        # type: (str) -> str
        """
        Return joined URI without credential.

        :param str rel: relative URI.
        :return: The joined URI.
        :rtype: str
        """
        return (self.baseurl + rel).public()

    def access(self, repo, filename=None, get=False):
        # type: (Optional[_UCSRepo], str, bool) -> Tuple[int, int, bytes]
        """
        Access URI and optionally get data.

        :param _UCSRepo repo: the URI to access as an instance of :py:class:`_UCSRepo`.
        :param str filename: An optional relative path.
        :param bool get: Fetch data if True - otherwise check only.
        :return: a 3-tuple (code, size, content)
        :rtype: tuple(int, int, bytes)
        :raises DownloadError: if the server is unreachable.
        :raises ValueError: if the credentials use an invalid encoding.
        :raises ConfigurationError: if a permanent error in the configuration occurs, e.g. the credentials are invalid or the host is unresolvable.
        :raises ProxyError: if the HTTP proxy returned an error.
        """
        rel = filename if repo is None else repo.path(filename)
        assert rel is not None
        if self.user_agent:
            UCSHttpServer.opener.addheaders = [('User-agent', self.user_agent)]
        uri = self.join(rel)
        if self.baseurl.username:
            UCSHttpServer.auth_handler.add_password(realm=None, uri=uri, user=self.baseurl.username, passwd=self.baseurl.password)
        req = urllib2.Request(uri)

        def get_host():
            # type: () -> str
            return req.host if six.PY3 else req.get_host()  # type: ignore

        if get_host() in self.failed_hosts:
            self.log.error('Already failed %s', get_host())
            raise DownloadError(uri, -1)
        if not get and UCSHttpServer.http_method != 'GET':
            # Overwrite get_method() to return "HEAD"
            def get_method(self, orig=req.get_method):
                method = orig()
                if method == 'GET':
                    return UCSHttpServer.http_method
                else:
                    return method
            req.get_method = functools.partial(get_method, req) if six.PY3 else instancemethod(get_method, req, urllib2.Request)  # type: ignore

        self.log.info('Requesting %s', req.get_full_url())
        ud.debug(ud.NETWORK, ud.ALL, "updater: %s %s" % (req.get_method(), req.get_full_url()))
        try:
            res = UCSHttpServer.opener.open(req, timeout=self.timeout)
            assert res
            try:
                # <http://tools.ietf.org/html/rfc2617#section-2>
                try:
                    auth = req.unredirected_hdrs['Authorization']
                    scheme, credentials = auth.split(' ', 1)
                    if scheme.lower() != 'basic':
                        raise ValueError('Only "Basic" authorization is supported')
                    try:
                        basic = base64.b64decode(credentials).decode('ISO8859-1')
                    except Exception:
                        raise ValueError('Invalid base64')
                    self.baseurl.username, self.baseurl.password = basic.split(':', 1)
                except KeyError:
                    pass
                except ValueError as ex:
                    self.log.info("Failed to decode %s: %s", auth, ex)
                code = res.getcode()
                assert code
                size = int(res.info().get('content-length', 0))
                content = res.read()
                self.log.info("Got %s %s: %d %d", req.get_method(), req.get_full_url(), code, size)
                return (code, size, content)
            finally:
                res.close()
        # direct   | proxy                                        | Error cause
        #          | valid     closed   filter   DNS     auth     |
        # HTTP:200 | HTTP:200  URL:111  URL:110  GAI:-2  HTTP:407 | OK
        # HTTP:404 | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Path unknown
        # ---------+----------------------------------------------+----------------------
        # URL:111  | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Port closed
        # URL:110  | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Port filtered
        # GAI:-2   | HTTP:502/4URL:111  URL:110  GAI:-2  HTTP:407 | Host name unknown
        # HTTP:401 | HTTP:401  URL:111  URL:110  GAI:-2  HTTP:407 | Authorization required
        except urllib_error.HTTPError as res:
            self.log.debug("Failed %s %s: %s", req.get_method(), req.get_full_url(), res, exc_info=True)
            if res.code == httplib.UNAUTHORIZED:  # 401
                raise ConfigurationError(uri, 'credentials not accepted')
            if res.code == httplib.PROXY_AUTHENTICATION_REQUIRED:  # 407
                raise ProxyError(uri, 'credentials not accepted')
            if res.code in (httplib.BAD_GATEWAY, httplib.GATEWAY_TIMEOUT):  # 502 504
                self.failed_hosts.add(get_host())
                raise ConfigurationError(uri, 'host is unresolvable')
            raise DownloadError(uri, res.code)
        except urllib_error.URLError as e:
            self.log.debug("Failed %s %s: %s", req.get_method(), req.get_full_url(), e, exc_info=True)
            if isinstance(e.reason, six.string_types):
                reason = e.reason
            elif isinstance(e.reason, socket.timeout):
                raise ConfigurationError(uri, 'timeout in network connection')
            else:
                try:
                    reason = e.reason.args[1]  # default value for error message
                except IndexError:
                    reason = str(e)  # unknown
                if isinstance(e.reason, socket.gaierror):
                    if e.reason.args[0] == socket.EAI_NONAME:  # -2
                        reason = 'host is unresolvable'
                else:
                    if e.reason.args[0] == errno.ETIMEDOUT:  # 110
                        reason = 'port is blocked'
                    elif e.reason.args[0] == errno.ECONNREFUSED:  # 111
                        reason = 'port is closed'

            selector = req.selector if six.PY3 else req.get_selector()  # type: ignore
            if selector.startswith('/'):  # direct
                self.failed_hosts.add(get_host())
                raise ConfigurationError(uri, reason)
            else:  # proxy
                raise ProxyError(uri, reason)
        except socket.timeout as ex:
            self.log.debug("Failed %s %s: %s", req.get_method(), req.get_full_url(), ex, exc_info=True)
            raise ConfigurationError(uri, 'timeout in network connection')


class UCSLocalServer(_UCSServer):
    """
    Access to UCS compatible local update server.
    """

    def __init__(self, prefix):
        # type: (str) -> None
        """
        Setup URL handler for accessing a UCS repository server.

        :param str prefix: The local path of the repository.
        """
        self.log = logging.getLogger('updater.UCSFile')
        self.log.addHandler(logging.NullHandler())
        prefix = str(prefix).strip('/')
        self._prefix = '%s/' % prefix if prefix else ''

    @property
    def prefix(self):
        # type: () -> str
        return self._prefix

    def __str__(self):
        # type: () -> str
        """
        Absolute file-URI.
        """
        return 'file:///%s' % self.prefix

    def __repr__(self):
        # type: () -> str
        """
        Return canonical string representation.
        """
        return 'UCSLocalServer(prefix=%r)' % (self.prefix,)

    def __add__(self, rel):
        # type: (str) -> UCSLocalServer
        """
        Append relative path component.

        :param str rel: Relative path.
        :return: A clone of this instance using the new base path.
        :rtype: UCSLocalServer
        """
        uri = copy.copy(self)
        uri._prefix += str(rel).lstrip('/')
        return uri

    def join(self, rel):
        # type: (str) -> str
        """
        Return joined URI without credential.

        :param str rel: relative URI.
        :return: The joined URI.
        :rtype: str
        """
        uri = self.__str__()
        uri += str(rel).lstrip('/')
        return uri

    def access(self, repo, filename=None, get=False):
        # type: (Optional[_UCSRepo], str, bool) -> Tuple[int, int, bytes]
        """
        Access URI and optionally get data.

        :param _UCSRepo repo: the URI to access as an instance of :py:class:`_UCSRepo`.
        :param str filename: An optional relative path.
        :param bool get: Fetch data if True - otherwise check only.
        :return: a 3-tuple (code, size, content)
        :rtype: tuple(int, int, bytes)
        :raises DownloadError: if the server is unreachable.
        :raises ValueError: if the credentials use an invalid encoding.
        :raises ConfigurationError: if a permanent error in the configuration occurs, e.g. the credentials are invalid or the host is unresolvable.
        :raises ProxyError: if the HTTP proxy returned an error.
        """
        rel = filename if repo is None else repo.path(filename)
        assert rel is not None
        uri = self.join(rel)
        ud.debug(ud.NETWORK, ud.ALL, "updater: %s" % (uri,))
        # urllib2.urlopen() doesn't work for directories
        assert uri.startswith('file://')
        path = uri[len('file://'):]
        if os.path.exists(path):
            if os.path.isdir(path):
                self.log.info("Got %s", path)
                return (httplib.OK, 0, b'')  # 200
            elif os.path.isfile(path):
                with open(path, 'rb') as f:
                    data = f.read()
                self.log.info("Got %s: %d", path, len(data))
                return (httplib.OK, len(data), data)  # 200
        self.log.error("Failed %s", path)
        raise DownloadError(uri, -1)


class UniventionUpdater(object):
    """
    Handle UCS package repositories.
    """

    COMPONENT_AVAILABLE = 'available'
    COMPONENT_NOT_FOUND = 'not_found'
    COMPONENT_DISABLED = 'disabled'
    COMPONENT_UNKNOWN = 'unknown'
    COMPONENT_PERMISSION_DENIED = 'permission_denied'
    FN_UPDATER_APTSOURCES_COMPONENT = '/etc/apt/sources.list.d/20_ucs-online-component.list'

    def __init__(self, check_access=True):
        # type: (bool) -> None
        """
        Create new updater with settings from UCR.

        :param bool check_access: Check if repository server is reachable on init.
        :raises ConfigurationError: if configured server is not available immediately.
        """
        self.log = logging.getLogger('updater.Updater')
        self.log.addHandler(logging.NullHandler())
        self.check_access = check_access
        self.connection = None
        self.architectures = [os.popen('dpkg --print-architecture 2>/dev/null').readline()[:-1]]

        self.configRegistry = ConfigRegistry()
        self.ucr_reinit()

    def config_repository(self):
        # type: () -> None
        """
        Retrieve configuration to access repository. Overridden by :py:class:`univention.updater.UniventionMirror`.
        """
        self.online_repository = self.configRegistry.is_true('repository/online', True)
        self.repourl = UcsRepoUrl(self.configRegistry, 'repository/online')
        self.sources = self.configRegistry.is_true('repository/online/sources', False)
        self.timeout = float(self.configRegistry.get('repository/online/timeout', 30))
        UCSHttpServer.http_method = self.configRegistry.get('repository/online/httpmethod', 'HEAD').upper()

    def ucr_reinit(self):
        # type: () -> None
        """
        Re-initialize settings.
        """
        self.configRegistry.load()

        self.is_repository_server = self.configRegistry.is_true('local/repository', False)

        reinitUCSHttpServer = False
        if 'proxy/http' in self.configRegistry and self.configRegistry['proxy/http']:
            os.environ['http_proxy'] = self.configRegistry['proxy/http']
            os.environ['https_proxy'] = self.configRegistry['proxy/http']
            reinitUCSHttpServer = True
        if 'proxy/https' in self.configRegistry and self.configRegistry['proxy/https']:
            os.environ['https_proxy'] = self.configRegistry['proxy/https']
            reinitUCSHttpServer = True
        if 'proxy/no_proxy' in self.configRegistry and self.configRegistry['proxy/no_proxy']:
            os.environ['no_proxy'] = self.configRegistry['proxy/no_proxy']
            reinitUCSHttpServer = True
        if reinitUCSHttpServer:
            UCSHttpServer.reinit()

        # check for maintained and unmaintained
        self.parts = ['maintained']
        if self.configRegistry.is_true('repository/online/unmaintained', False):
            self.parts.append('unmaintained')

        # UCS version
        self.current_version = UCS_Version("%(version/version)s-%(version/patchlevel)s" % self.configRegistry)
        self.erratalevel = int(self.configRegistry.get('version/erratalevel', 0))

        # override automatically detected architecture by UCR variable repository/online/architectures (comma or space separated)
        archlist = self.configRegistry.get('repository/online/architectures', '')
        if archlist:
            self.architectures = RE_SPLIT_MULTI.split(archlist)

        # UniventionMirror needs to provide its own settings
        self.config_repository()

        if not self.online_repository:
            self.log.info('Disabled')
            self.server = UCSLocalServer('')  # type: _UCSServer
            return

        # generate user agent string
        user_agent = self._get_user_agent_string()
        UCSHttpServer.load_credentials(self.configRegistry)

        self.server = UCSHttpServer(
            baseurl=self.repourl,
            user_agent=user_agent,
            timeout=self.timeout,
        )
        self._get_releases()

    def _get_releases(self):
        # type: () -> None
        """
        Detect server prefix and download `releases.json` file.
        """
        try:
            if not self.repourl.path:
                try:
                    _code, _size, data = self.server.access(None, '/univention-repository/releases.json', get=True)
                    self.server += '/univention-repository/'
                    self.log.info('Using detected prefix /univention-repository/')
                    self.releases = json.loads(data)
                except DownloadError as e:
                    self.log.info('No prefix /univention-repository/ detected, using /')
                    ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
            # Validate server settings
            try:
                _code, _size, data = self.server.access(None, 'releases.json', get=True)
                self.log.info('Using configured prefix %s', self.repourl.path)
                self.releases = json.loads(data)
            except DownloadError as e:
                self.log.error('Failed configured prefix %s', self.repourl.path, exc_info=True)
                uri, code = e.args
                raise ConfigurationError(uri, 'non-existing prefix "%s": %s' % (self.repourl.path, uri))
        except ConfigurationError as e:
            if self.check_access:
                self.log.fatal('Failed server detection: %s', e, exc_info=True)
                raise
            self.releases = {"error": str(e)}
        except (ValueError, LookupError) as exc:
            ud.debug(ud.NETWORK, ud.ERROR, 'Querying maintenance information failed: %s' % (exc,))
            self.releases = {"error": str(exc)}

    def get_releases(self, start=None, end=None):
        # type: (Optional[UCS_Version], Optional[UCS_Version]) -> Iterator[Tuple[UCS_Version, Dict[str, Any]]]
        """
        Return UCS releases in range.

        :param start: Minimum requried version.
        :param end: Maximum allowed version.
        :returns: Iterator of 2-tuples (UCS_Version, data).
        """
        for major_release in self.releases.get('releases', []):
            for minor_release in major_release['minors']:
                for patchlevel_release in minor_release['patchlevels']:
                    ver = UCS_Version((
                        major_release['major'],
                        minor_release['minor'],
                        patchlevel_release['patchlevel']
                    ))
                    if start and ver < start:
                        continue
                    if end and ver > end:
                        continue
                    yield (ver, dict(patchlevel_release, major=major_release['major'], minor=minor_release['minor']))

    def get_next_version(self, version, components=[], errorsto='stderr'):
        # type: (UCS_Version, Iterable[str], Literal["stderr", "exception", "none"]) -> Optional[UCS_Version]
        """
        Check if a new patchlevel, minor or major release is available for the given version.
        Components must be available for the same major.minor version.

        :param UCS_Version version: A UCS release version.
        :param components: A list of component names, which must be available for the next release.
        :type components: list[str]
        :param str errorsto: Select method of reporting errors; on of 'stderr', 'exception', 'none'.
        :returns: The next UCS release or None.
        :rtype: UCS_Version or None
        :raises RequiredComponentError: if a required component is missing
        """
        try:
            ver = min(ver for ver, _data in self.get_releases() if ver > version)
        except ValueError:
            return None

        self.log.info('Found version %s', ver)

        failed = set()
        for component in components:
            self.log.info('Checking for component %s', component)
            try:
                self.get_component_repositories(component, [ver], clean=False, debug=(errorsto == 'stderr')
            except UpdaterException:
                self.log.error('Missing component %s', component)
                failed.add(component)

        if failed:
            ex = RequiredComponentError(str(ver), failed)
            if errorsto == 'exception':
                raise ex
            elif errorsto == 'stderr':
                print(ex, file=sys.stderr)
            return None

        self.log.info('Going for version %s', ver)
        return ver

    def get_all_available_release_updates(self, ucs_version=None):
        # type: (Optional[UCS_Version]) -> Tuple[List[UCS_Version], Optional[Set[str]]]
        """
        Returns a list of all available release updates - the function takes required components into account
        and stops if a required component is missing

        :param ucs_version: starts travelling through available version from version.
        :type ucs_version: UCS_Version or None
        :returns: a list of 2-tuple `(versions, blocking_component)`, where `versions` is a list of UCS release and `blocking_component` is the first missing component blocking the update.
        :rtype: tuple(list[str], str or None)
        """
        ucs_version = ucs_version or self.current_version
        components = self.get_current_components()

        result = []  # type: List[UCS_Version]
        while ucs_version:
            try:
                ucs_version = self.get_next_version(ucs_version, components, errorsto='exception')
            except RequiredComponentError as ex:
                self.log.warning('Update blocked by components %s', ', '.join(ex.components))
                # ex.components blocks update to next version ==> return current list and blocking component
                return result, ex.components

            if not ucs_version:
                break
            result.append(ucs_version)
        self.log.info('Found release updates %r', result)
        return result, None

    def release_update_available(self, ucs_version=None, errorsto='stderr'):
        # type: (Optional[UCS_Version], Literal["stderr", "exception", "none"]) -> Optional[UCS_Version]
        """
        Check if an update is available for the `ucs_version`.

        :param str ucs_version: The UCS release to check.
        :param str errorsto: Select method of reporting errors; on of 'stderr', 'exception', 'none'.
        :returns: The next UCS release or None.
        :rtype: str or None
        """
        ucs_version = ucs_version or self.current_version

        components = self.get_current_components()

        return self.get_next_version(UCS_Version(ucs_version), components, errorsto)

    def release_update_temporary_sources_list(self, version, components=None):
        # type: (UCS_Version, Iterable[str]) -> List[str]
        """
        Return list of Debian repository statements for the release update including all enabled components.

        :param version: The UCS release.
        :param components: A list of required component names or None.
        :type components: list or None
        :returns: A list of Debian APT `sources.list` lines.
        :rtype: list[str]
        """
        if components is None:
            components = self.get_components()

        current_components = self.get_current_components()

        result = [UCSRepoPool5(version).deb(self.server)]
        for component in components:
            repos = []  # type: List[str]
            try:
                repos = self.get_component_repositories(component, [version], False)
            except (ConfigurationError, ProxyError):
                # if component is marked as required (UCR variable "version" contains "current")
                # then raise error, otherwise ignore it
                if component in current_components:
                    raise
            if not repos and component in current_components:
                server = self._get_component_server(component)
                uri = server.join('%s/component/%s/' % (version, component))
                raise ConfigurationError(uri, 'component not found')
            result += repos
        return result

    def get_components(self, only_localmirror_enabled=False):
        # type: (bool) -> Set[str]
        """
        Retrieve all enabled components from registry as set().
        By default, only "enabled" components will be returned (repository/online/component/%s=$TRUE).

        :param bool only_localmirror_enabled:
            Only the components enabled for local mirroring.
            If only_`localmirror`_enabled is `True`, then all components with `repository/online/component/%s/localmirror=$TRUE` will be returned.
            If `repository/online/component/%s/localmirror` is not set, then the value of `repository/online/component/%s` is used for backward compatibility.
        :returns: The set of enabled components.
        :rtype: set(str)
        """
        components = set()
        for key, value in self.configRegistry.items():
            match = RE_COMPONENT.match(key)
            if not match:
                continue
            component, = match.groups()
            enabled = self.configRegistry.is_true(value=value)
            if only_localmirror_enabled:
                enabled = self.configRegistry.is_true(key + '/localmirror', enabled)
            if enabled:
                components.add(component)
        return components

    def get_current_components(self):
        # type: () -> Set[str]
        """
        Return set() of all components marked as current.

        :returns: Set of component names marked as current.
        :rtype: set(str)
        """
        all_components = self.get_components()
        components = set()
        for component in all_components:
            key = 'repository/online/component/%s/version' % component
            value = self.configRegistry.get(key, '')
            versions = RE_SPLIT_MULTI.split(value)
            if 'current' in versions:
                components.add(component)
        return components

    def get_all_components(self):
        # type: () -> Set[str]
        """
        Retrieve all configured components from registry as set().

        :returns: Set of component names.
        :rtype: set(str)
        """
        components = set()
        for key in self.configRegistry.keys():
            if key.startswith('repository/online/component/'):
                component_part = key[len('repository/online/component/'):]
                if component_part.find('/') == -1:
                    components.add(component_part)
        return components

    def get_current_component_status(self, name):
        # type: (str) -> str
        """
        Returns the current status of specified component based on `/etc/apt/sources.list.d/20_ucs-online-component.list`

        :param str name: The name of the component.
        :returns: One of the strings:

            :py:const:`COMPONENT_DISABLED`
                component has been disabled via UCR
            :py:const:`COMPONENT_AVAILABLE`
                component is enabled and at least one valid repo string has been found in .list file
            :py:const:`COMPONENT_NOT_FOUND`
                component is enabled but no valid repo string has been found in .list file
            :py:const:`COMPONENT_PERMISSION_DENIED`
                component is enabled but authentication failed
            :py:const:`COMPONENT_UNKNOWN`
                component's status is unknown

        :rtype: str
        """
        if name not in self.get_components():
            return self.COMPONENT_DISABLED

        try:
            comp_file = open(self.FN_UPDATER_APTSOURCES_COMPONENT, 'r')
        except IOError:
            return self.COMPONENT_UNKNOWN
        rePath = re.compile('(un)?maintained/component/ ?%s/' % name)
        reDenied = re.compile('credentials not accepted: %s$' % name)
        try:
            # default: file contains no valid repo entry
            result = self.COMPONENT_NOT_FOUND
            for line in comp_file:
                if line.startswith('deb ') and rePath.search(line):
                    # at least one repo has been found
                    result = self.COMPONENT_AVAILABLE
                elif reDenied.search(line):
                    # stop immediately if at least one repo has authentication problems
                    return self.COMPONENT_PERMISSION_DENIED
            # return result
            return result
        finally:
            comp_file.close()

    def get_component_defaultpackage(self, componentname):
        # type: (str) -> Set[str]
        """
        Returns a set of (meta) package names to be installed for this component.

        :param str componentname: The name of the component.
        :returns: a set of package names.
        :rtype: set(str)
        """
        lst = set()  # type: Set[str]
        for var in ('defaultpackages', 'defaultpackage'):
            if componentname and self.configRegistry.get('repository/online/component/%s/%s' % (componentname, var)):
                val = self.configRegistry.get('repository/online/component/%s/%s' % (componentname, var), '')
                # split at " " and "," and remove empty items
                lst |= set(RE_SPLIT_MULTI.split(val))
        lst.discard('')
        return lst

    def is_component_defaultpackage_installed(self, componentname, ignore_invalid_package_names=True):
        # type: (str, bool) -> Optional[bool]
        """
        Returns installation status of component's default packages

        :param str componentname: The name of the component.
        :param bool ignore_invalid_package_names: Ignore invalid package names.
        :returns: On of the values:

            None
                no default packages are defined
            True
                all default packages are installed
            False
                at least one package is not installed

        :rtype: None or bool
        :raises ValueError: if UCR variable contains invalid package names if ignore_invalid_package_names=False
        """
        pkglist = self.get_component_defaultpackage(componentname)
        if not pkglist:
            return None

        # check package names
        for pkg in pkglist:
            match = RE_ALLOWED_DEBIAN_PKGNAMES.search(pkg)
            if not match:
                if ignore_invalid_package_names:
                    continue
                raise ValueError('invalid package name (%s)' % pkg)

        cmd = ['/usr/bin/dpkg-query', '-W', '-f', '${Status}\\n']
        cmd.extend(pkglist)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = (data.decode("UTF-8", errors="replace") for data in p.communicate())
        # count number of "Status: install ok installed" lines
        installed_correctly = len([x for x in stdout.splitlines() if x.endswith(' ok installed')])
        # if pkg count and number of counted lines match, all packages are installed
        return len(pkglist) == installed_correctly

    def component_update_get_packages(self):
        # type: () -> Tuple[List[Tuple[Text, Text]], List[Tuple[Text, Text, Text]], List[Tuple[Text, Text]]]
        """
        Return tuple with list of (new, upgradeable, removed) packages.

        :return: A 3-tuple (new, upgraded, removed).
        :rtype: tuple(list[str], list[str], list[str])
        """
        env = dict(os.environ, LC_ALL="C.UTF-8")

        proc = subprocess.Popen(("univention-config-registry", "commit", "/etc/apt/sources.list.d/20_ucs-online-component.list"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = (data.decode("UTF-8", errors="replace") for data in proc.communicate())
        if stderr:
            ud.debug(ud.NETWORK, ud.PROCESS, 'stderr=%s' % stderr)
        if stdout:
            ud.debug(ud.NETWORK, ud.INFO, 'stdout=%s' % stdout)
        # FIXME: error handling

        proc = subprocess.Popen(cmd_update, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = (data.decode("UTF-8", errors="replace") for data in proc.communicate())
        if stderr:
            ud.debug(ud.NETWORK, ud.PROCESS, 'stderr=%s' % stderr)
        if stdout:
            ud.debug(ud.NETWORK, ud.INFO, 'stdout=%s' % stdout)
        # FIXME: error handling

        proc = subprocess.Popen(cmd_dist_upgrade_sim, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = (data.decode("UTF-8", errors="replace") for data in proc.communicate())
        if stderr:
            ud.debug(ud.NETWORK, ud.PROCESS, 'stderr=%s' % stderr)
        if stdout:
            ud.debug(ud.NETWORK, ud.INFO, 'stdout=%s' % stdout)

        if proc.returncode == 100:
            raise UnmetDependencyError(stderr)

        new_packages = []  # type: List[Tuple[Text, Text]]
        upgraded_packages = []  # type: List[Tuple[Text, Text, Text]]
        removed_packages = []  # type: List[Tuple[Text, Text]]
        for line in stdout.splitlines():
            line_split = line.split(' ')
            if line.startswith('Inst '):
                # upgrade:
                #    Inst univention-updater [3.1.1-5] (3.1.1-6.408.200810311159 192.168.0.10)
                # inst:
                #    Inst mc (1:4.6.1-6.12.200710211124 oxae-update.open-xchange.com)
                if len(line_split) > 3:
                    if line_split[2].startswith('[') and line_split[2].endswith(']'):
                        ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of upgraded packages' % line_split[1])
                        upgraded_packages.append((line_split[1], line_split[2].replace('[', '').replace(']', ''), line_split[3].replace('(', '')))
                    else:
                        ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of new packages' % line_split[1])
                        new_packages.append((line_split[1], line_split[2].replace('(', '')))
                else:
                    ud.debug(ud.NETWORK, ud.WARN, 'unable to parse the update line: %s' % line)
                    continue
            elif line.startswith('Remv '):
                if len(line_split) > 3:
                    ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of removed packages' % line_split[1])
                    removed_packages.append((line_split[1], line_split[2].replace('(', '')))
                elif len(line_split) > 2:
                    ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of removed packages' % line_split[1])
                    removed_packages.append((line_split[1], 'unknown'))
                else:
                    ud.debug(ud.NETWORK, ud.WARN, 'unable to parse the update line: %s' % line)
                    continue

        return (new_packages, upgraded_packages, removed_packages)

    def run_dist_upgrade(self):
        # type: () -> int
        """
        Run `apt-get dist-upgrade` command.

        :returns: a 3-tuple (return_code, stdout, stderr)
        :rtype: tuple(int, str, str)
        """
        env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
        with open("/var/log/univention/updater.log", "a") as log:
            return subprocess.call(cmd_dist_upgrade, shell=True, env=env, stdout=log, stderr=log)

    def _iterate_release(self, ver, start, end):
        # type: (_UCSRepo, UCS_Version, UCS_Version) -> Generator[_UCSRepo, bool, None]
        """
        Iterate through all versions of repositories between start and end.

        :param UCSRepo ver: An instance of :py:class:`UCS_Version` used for iteration.
        :param UCS_Version start: The UCS release to start from.
        :param UCS_Version end: The UCS release where to stop.
        """
        MAX_MINOR = 99
        for ver.major in range(start.major, end.major + 1):
            for ver.minor in range(start.minor if ver.major == start.major else 0, (end.minor if ver.major == end.major else MAX_MINOR) + 1):
                if isinstance(ver.patch, six.string_types):  # patchlevel not used
                    failed = (yield ver)
                else:
                    for ver.patchlevel in range(start.patchlevel if ver.mm == start.mm else ver.patchlevel_reset, (end.patchlevel if ver.mm == end.mm else ver.patchlevel_max) + 1):
                        failed = (yield ver)
                        if failed and ver.mm < end.mm:
                            break
                if failed and ver.major < end.major:
                    break

    def _iterate_versions(self, ver, start, end, parts, archs, server):
        # type: (_UCSRepo, UCS_Version, UCS_Version, Iterable[str], Iterable[str], _UCSServer) -> Iterator
        """
        Iterate through all versions of repositories between start and end.

        :param UCSRepo ver: An instance of :py:class:`UCS_Version` used for iteration.
        :param UCS_Version start: The UCS release to start from.
        :param UCS_Version end: The UCS release where to stop.
        :param parts: List of `maintained` and/or `unmaintained`.
        :param archs: List of architectures.
        :param UCSHttpServer server: The UCS repository server to use.
        :returns: A iterator through all UCS releases between `start` and `end` returning `ver`.
        :raises ProxyError: if the repository server is blocked by the proxy.
        """
        self.log.info('Searching %s:%r [%s..%s) in %s and %s', server, ver, start, end, parts, archs)
        (ver.major, ver.minor, ver.patchlevel) = (start.major, start.minor, start.patchlevel)

        # Workaround version of start << first available repository version,
        # e.g. repository starts at 2.3-0, but called with start=2.0-0
        it = self._iterate_release(ver, start, end)
        try:
            ver = next(it)
            while True:
                self.log.info('Checking version %s', ver)
                success = False
                for ver.part in parts:  # part
                    try:
                        self.log.info('Checking version %s', ver.path())
                        assert server.access(ver)  # patchlevel
                        for ver.arch in archs:  # architecture
                            try:
                                code, size, content = server.access(ver)
                                self.log.info('Found content: code=%d size=%d', code, size)
                                if size >= MIN_GZIP:
                                    success = True
                                    yield ver
                                elif size == 0 and isinstance(server, UCSHttpServer) and server.proxy_handler.proxies:
                                    uri = server.join(ver.path())
                                    raise ProxyError(uri, "download blocked by proxy?")
                            except DownloadError as e:
                                ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
                            finally:
                                del ver.arch
                    except DownloadError as e:
                        ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
                    finally:
                        del ver.part
                ver = it.send(not success)
        except StopIteration:
            pass

    def _iterate_version_repositories(self, start, end, parts, archs):
        # type: (UCS_Version, UCS_Version, List[str], List[str]) -> Iterator[Tuple[_UCSServer, _UCSRepo]]
        """
        Iterate over all UCS releases and return (server, version).

        :param UCS_Version start: The UCS release to start from.
        :param UCS_Version end: The UCS release where to stop.
        :param parts: List of `maintained` and/or `unmaintained`.
        :type parts: list[str]
        :param archs: List of architectures without `all`.
        :type archs: list[str]
        :returns: A iterator returning 2-tuples (server, ver).
        """
        self.log.info('Searching releases [%s..%s)', start, end)
        releases = sorted(ver for ver, _data in self.get_releases(start, end))
        for release in releases:
            yield self.server, UCSRepoPool5(release=release, prefix=self.server)

    def _iterate_component_repositories(self, components, start, end, archs, for_mirror_list=False):
        # type: (Iterable[str], UCS_Version, UCS_Version, List[str], bool) -> Iterator[Tuple[_UCSServer, _UCSRepo]]
        """
        Iterate over all components and return (server, version).

        :para components: List of component names.
        :type components: list[str]
        :param UCS_Version start: The UCS release to start from.
        :param UCS_Version end: The UCS release where to stop.
        :param archs: List of architectures without `all`.
        :type archs: list[str]
        :param bool for_mirror_list: Use the settings for mirroring.
        :returns: A iterator returning 2-tuples (server, ver).
        """
        self.log.info('Searching components %r [%s..%s)', components, start, end)
        # Components are ... different:
        for component in components:
            # server, port, prefix
            server = self._get_component_server(component, for_mirror_list=for_mirror_list)
            # parts
            parts_unique = set(self.parts)
            if self.configRegistry.is_true('repository/online/component/%s/unmaintained' % (component)):
                parts_unique.add("unmaintained")
            parts = ['%s/component' % (part,) for part in parts_unique]
            # versions
            versions = {start} if start == end else self._get_component_versions(component, start, end)

            self.log.info('Component %s from %s versions %r', component, server, versions)
            for version in versions:
                try:
                    repos = [(UCSRepoPool, archs), (UCSRepoPoolNoArch, [])]  # type: List[Tuple[Type[_UCSRepo], List[str]]]
                    for (UCSRepoPoolVariant, subarchs) in repos:
                        struct = UCSRepoPoolVariant(prefix=server, patch=component)
                        for ver in self._iterate_versions(struct, version, version, parts, ['all'] + subarchs, server):
                            yield server, ver
                except (ConfigurationError, ProxyError):
                    # if component is marked as required (UCR variable "version" contains "current")
                    # then raise error, otherwise ignore it
                    if component in self.get_current_components():
                        raise

    def _get_component_baseurl(self, component, for_mirror_list=False):
        # type: (str, bool) -> UcsRepoUrl
        """
        Calculate the base URL for a component.

        :param str component: Name of the component.
        :param bool for_mirror_list: Use external or local repository.

        CS (component server)
            value of `repository/online/component/%s/server`
        MS (mirror server)
            value of `repository/mirror/server`
        RS (repository server)
            value of `repository/online/server`
        \-
            value is unset or no entry
        /blank/
            value is irrelevant

        +-------------+----------+------------+---------+------------+------------+-------------+
        | UCR configuration                             |Result                   |             |
        +-------------+----------+------------+---------+------------+------------+             |
        | isRepoServer|enabled   |localmirror |server   |sources.list mirror.list |             |
        +=============+==========+============+=========+============+============+=============+
        | False       |False     |False       |\-       |\-          |\-          |no           |
        +             +----------+------------+---------+------------+------------+local        |
        |             |True      |            |\-       |RS          |\-          |repository   |
        +             +----------+------------+---------+------------+------------+mirror       |
        |             |True      |            |CS       |CS          |\-          |             |
        +-------------+----------+------------+---------+------------+------------+-------------+
        | True        |False     |False       |         |\-          |\-          |local        |
        +             +----------+------------+---------+------------+------------+repository   |
        |             |False     |True        |\-       |\-          |MS          |mirror       |
        +             +----------+------------+---------+------------+------------+             |
        |             |False     |True        |CS       |\-          |CS          |             |
        +             +----------+------------+---------+------------+------------+             |
        |             |True      |False       |\-       |MS          |\-          |             |
        +             +----------+------------+---------+------------+------------+             |
        |             |True      |False       |CS       |CS          |\-          |             |
        +             +----------+------------+---------+------------+------------+             |
        |             |True      |True        |\-       |RS          |MS          |             |
        +             +----------+------------+---------+------------+------------+             |
        |             |True      |True        |CS       |RS          |CS          |             |
        +             +----------+------------+---------+------------+------------+-------------+
        |             |False     |\-          |\-       |\-          |\-          |backward     |
        +             +----------+            +---------+------------+------------+compabibility|
        |             |True      |            |\-       |RS          |MS          |[1]_         |
        +             +----------+            +---------+------------+------------+             |
        |             |True      |            |CS       |RS          |CS          |             |
        +-------------+----------+------------+---------+------------+------------+-------------+

        .. [1] if `repository/online/component/%s/localmirror` is unset, then the value of `repository/online/component/%s` will be used to achieve backward compatibility.
        """

        c_prefix = 'repository/online/component/%s' % component
        if self.is_repository_server:
            m_url = UcsRepoUrl(self.configRegistry, 'repository/mirror')
            c_enabled = self.configRegistry.is_true('repository/online/component/%s' % component, False)
            c_localmirror = self.configRegistry.is_true('repository/online/component/%s/localmirror' % component, c_enabled)

            if for_mirror_list:  # mirror.list
                if c_localmirror:
                    return UcsRepoUrl(self.configRegistry, c_prefix, m_url)
            else:  # sources.list
                if c_enabled:
                    if c_localmirror:
                        return self.repourl
                    else:
                        return UcsRepoUrl(self.configRegistry, c_prefix, m_url)
        else:
            return UcsRepoUrl(self.configRegistry, c_prefix, self.repourl)

        raise CannotResolveComponentServerError(component, for_mirror_list)

    def _get_component_server(self, component, for_mirror_list=False):
        # type: (str, bool) -> UCSHttpServer
        """
        Return :py:class:`UCSHttpServer` for component as configures via UCR.

        :param str component: Name of the component.
        :param bool for_mirror_list: component entries for `mirror.list` will be returned, otherwise component entries for local `sources.list`.
        :returns: The repository server for the component.
        :rtype: UCSHttpServer
        :raises ConfigurationError: if the configured server is not usable.
        """
        c_url = copy.copy(self._get_component_baseurl(component, for_mirror_list))
        c_url.path = ''
        prefix = self.configRegistry.get('repository/online/component/%s/prefix' % component, '')

        user_agent = self._get_user_agent_string()

        server = UCSHttpServer(
            baseurl=c_url,
            user_agent=user_agent,
            timeout=self.timeout,
        )
        try:
            # if prefix.lower() == 'none' ==> use no prefix
            if prefix and prefix.lower() == 'none':
                try:
                    assert server.access(None, '')
                except DownloadError as e:
                    uri, code = e.args
                    raise ConfigurationError(uri, 'absent prefix forced - component %s not found: %s' % (component, uri))
            else:
                for testserver in [
                    server + '/univention-repository/',
                    server + self.repourl.path if self.repourl.path else None,
                    server,
                ]:
                    if not testserver:
                        continue
                    if prefix:  # append prefix if defined
                        testserver = testserver + '%s/' % (prefix.strip('/'),)
                    try:
                        assert testserver.access(None, '')
                        return testserver
                    except DownloadError as e:
                        ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
                        uri, code = e.args
                raise ConfigurationError(uri, 'non-existing component prefix: %s' % (uri,))

        except ConfigurationError:
            if self.check_access:
                raise
        return server

    def _get_component_versions(self, component, start, end):
        # type: (str, Optional[UCS_Version], Optional[UCS_Version]) -> Set[UCS_Version]
        """
        Return configured versions for component.

        :param str component: Name of the component.
        :param UCS_Version start: smallest version that shall be returned.
        :param UCS_Version end: largest version that shall be returned.
        :returns: A set of UCR release versions for which the component is enabled.
        :rtype: set(UCS_Version)

        For each component the UCR variable `repository/online/component/%s/version`
        is evaluated, which can be a space/comma separated combination of the following values:

            `current` or /empty/
                required component; must exist for requested version.
            /major.minor/
                use exactly this version.
        """
        ver = self.configRegistry.get('repository/online/component/%s/version' % component, '')
        versions = set()  # type: Set[UCS_Version]
        for version in RE_SPLIT_MULTI.split(ver):
            version = self.current_version if version in ('current', '') else UCS_Version(version if '-' in version else '%s-0' % version)

            if start and version < start:
                continue
            if end and version > end:
                continue
            versions.add(version)

        return versions

    def get_component_repositories(self, component, versions, clean=False, debug=True, for_mirror_list=False):
        # type: (str, Iterable[UCS_Version], bool, bool, bool) -> List[str]
        """
        Return list of Debian repository statements for requested component.

        :param str component: The name of the component.
        :param versions: A list of UCS releases.
        :type versions: list[str] or list[UCS_Version].
        :param bool clean: Add additional `clean` statements for `apt-mirror`.
        :param bool debug: UNUSED.
        :param bool for_mirror_list: component entries for `mirror.list` will be returned, otherwise component entries for local `sources.list`.
        :returns: A list of strings with APT statements.
        :rtype: list(str)
        """
        result = []  # type: List[str]

        versions_mmp = {UCS_Version((v.major, v.minor, 0)) for v in versions}
        for version in versions_mmp:
            for server, ver in self._iterate_component_repositories([component], version, version, self.architectures, for_mirror_list=for_mirror_list):
                result.append(ver.deb(server))
                if ver.arch == self.architectures[-1]:  # after architectures but before next patch(level)
                    if clean:
                        result.append(ver.clean(server))
                    if self.sources:
                        ver.arch = "source"
                        try:
                            code, size, content = server.access(ver, "Sources.gz")
                            if size >= MIN_GZIP:
                                result.append(ver.deb(server, "deb-src"))
                        except DownloadError as e:
                            ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

        return result

    def print_component_repositories(self, clean=False, start=None, end=None, for_mirror_list=False):
        # type: (bool, Optional[UCS_Version], Optional[UCS_Version], bool) -> str
        """
        Return a string of Debian repository statements for all enabled components.

        :param bool clean: Add additional `clean` statements for `apt-mirror` if enabled by UCRV `repository/online/component/%s/clean`.
        :param UCS_Version start: optional smallest UCS release to return.
        :param UCS_Version end: optional largest UCS release to return.
        :param bool for_mirror_list: component entries for `mirror.list` will be returned, otherwise component entries for local `sources.list`.
        :returns: A string with APT statement lines.
        :rtype: str
        """
        if not self.online_repository:
            return ''

        if clean:
            clean = self.configRegistry.is_true('online/repository/clean', False)

        result = []  # type: List[str]
        for component in self.get_components(only_localmirror_enabled=for_mirror_list):
                versions = self._get_component_versions(component, start, end)
                repos = self.get_component_repositories(component, versions, clean, for_mirror_list=for_mirror_list)
                result += repos
        return '\n'.join(result)

    def _get_user_agent_string(self):
        # type: () -> str
        """
        Return the HTTP user agent string encoding the enabled components.

        :returns: A HTTP user agent string.
        :rtype: str
        """
        # USER_AGENT='updater/identify - version/version-version/patchlevel errata version/erratalevel - uuid/system - uuid/license'
        # USER_AGENT='UCS updater - 3.1-0 errata28 - 77e6406d-7a3e-40b3-a398-81cf119c9ef7 - 4c52d2da-d04d-4b05-a593-1974ee851fc8'
        # USER_AGENT='UCS updater - 3.1-0 errata28 - 77e6406d-7a3e-40b3-a398-81cf119c9ef7 - 00000000-0000-0000-0000-000000000000'
        return '%s - %s-%s errata%s - %s - %s - %s - %s' % (
            self.configRegistry.get('updater/identify', 'UCS'),
            self.configRegistry.get('version/version'), self.configRegistry.get('version/patchlevel'),
            self.configRegistry.get('version/erratalevel'),
            self.configRegistry.get('uuid/system', UUID_NULL),
            self.configRegistry.get('uuid/license', UUID_NULL),
            ','.join(self.configRegistry.get('repository/app_center/installed', '').split('-')),
            self.configRegistry.get('updater/statistics', ''),
        )

    @staticmethod
    def call_sh_files(scripts, logname, *args):
        # type: (Iterable[Tuple[_UCSServer, _UCSRepo, Optional[str], str, bytes]], str, *str) -> Iterator[Tuple[str, str]]
        """
        Get pre- and postup.sh files and call them in the right order::

            u = UniventionUpdater()
            ver = u.current_version
            rel = u._iterate_version_repositories(ver, ver, u.parts, u.architectures)
            com = u._iterate_component_repositories(['ucd'], ver, ver, u.architectures)
            repos = itertools.chain(rel, com)
            scripts = u.get_sh_files(repos)
            next_ver = u.get_next_version(u.current_version)
            for phase, order in u.call_sh_files(scripts, '/var/log/univention/updater.log', next_ver):
              if (phase, order) == ('update', 'main'):
                pass

        :param scripts: A generator returning the script to call, e.g. :py:meth:`get_sh_files`
        :param str logname: The file name of the log file.
        :param args: Additional arguments to pass through to the scripts.
        :returns: A generator returning 2-tuples (phase, part)
        """
        # create temporary directory for scripts
        tempdir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, tempdir, ignore_errors=True)

        def call(*cmd):
            # type: (*str) -> int
            """
            Execute script.

            :param cmd: The command to execute in a sub-process.
            :type cmd: list(str)
            :returns: The exit code of the child process.
            :rtype: int
            """
            commandline = ' '.join(["'%s'" % a.replace("'", "'\\''") for a in cmd])
            ud.debug(ud.PROCESS, ud.INFO, "Calling %s" % commandline)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tee = subprocess.Popen(('tee', '-a', logname), stdin=p.stdout)
            # Order is important! See bug #16454
            tee.wait()
            p.wait()
            return p.returncode

        # download scripts
        yield "update", "pre"
        main = {'preup': [], 'postup': []}  # type: Dict[str, List[Tuple[str, str]]]
        comp = {'preup': [], 'postup': []}  # type: Dict[str, List[Tuple[str, str]]]
        # save scripts to temporary files
        for server, struct, phase, path, data in scripts:
            if phase is None:
                continue
            assert data is not None
            uri = server.join(path)
            fd, name = tempfile.mkstemp(suffix='.sh', prefix=phase, dir=tempdir)
            try:
                size = os.write(fd, data)
                os.chmod(name, 0o744)
                if size == len(data):
                    ud.debug(ud.NETWORK, ud.INFO, "%s saved to %s" % (uri, name))
                    if hasattr(struct, 'part') and struct.part.endswith('/component'):
                        comp[phase].append((name, str(struct.patch)))
                    else:
                        main[phase].append((name, str(struct.patch)))
                    continue
            finally:
                os.close(fd)
            ud.debug(ud.NETWORK, ud.ERROR, "Error saving %s to %s" % (uri, name))

        # call component/preup.sh pre $args
        yield "preup", "pre"
        for (script, patch) in comp['preup']:
            if call(script, 'pre', *args) != 0:
                raise PreconditionError('preup', 'pre', patch, script)

        # call $next_version/preup.sh
        yield "preup", "main"
        for (script, patch) in main['preup']:
            if call(script, *args) != 0:
                raise PreconditionError('preup', 'main', patch, script)

        # call component/preup.sh post $args
        yield "preup", "post"
        for (script, patch) in comp['preup']:
            if call(script, 'post', *args) != 0:
                raise PreconditionError('preup', 'post', patch, script)

        # call $update/commands/distupgrade or $update/commands/upgrade
        yield "update", "main"

        # call component/postup.sh pos $args
        yield "postup", "pre"
        for (script, patch) in comp['postup']:
            if call(script, 'pre', *args) != 0:
                raise PreconditionError('postup', 'pre', patch, script)

        # call $next_version/postup.sh
        yield "postup", "main"
        for (script, patch) in main['postup']:
            if call(script, *args) != 0:
                raise PreconditionError('postup', 'main', patch, script)

        # call component/postup.sh post $args
        yield "postup", "post"
        for (script, patch) in comp['postup']:
            if call(script, 'post', *args) != 0:
                raise PreconditionError('postup', 'post', patch, script)

        # clean up
        yield "update", "post"

    @staticmethod
    def get_sh_files(repositories, verify=False):
        # type: (Iterable[Tuple[_UCSServer, _UCSRepo]], bool) -> Iterator[Tuple[_UCSServer, _UCSRepo, Optional[str], str, bytes]]
        """
        Return all preup- and postup-scripts of repositories.

        :param repositories: iteratable (server, struct)s
        :param bool verify: Verify the PGP signature of the downloaded scripts.
        :returns: iteratable (server, struct, phase, path, script)
        :raises VerificationError: if the PGP signature is invalid.

        See :py:meth:`call_sh_files` for an example.
        """
        for server, struct in repositories:
            uses_proxy = hasattr(server, "proxy_handler") and server.proxy_handler.proxies  # type: ignore
            for phase in ('preup', 'postup'):
                name = '%s.sh' % phase
                path = struct.path(name)
                ud.debug(ud.ADMIN, ud.ALL, "Accessing %s" % path)
                try:
                    _code, _size, script = server.access(struct, name, get=True)
                    # Bug #37031: dansguarding is lying and returns 200 even for blocked content
                    if not script.startswith(b'#!') and uses_proxy:
                        uri = server.join(path)
                        raise ProxyError(uri, "download blocked by proxy?")
                    if verify and struct >= UCS_Version((3, 2, 0)):
                        name_gpg = name + '.gpg'
                        path_gpg = struct.path(name_gpg)
                        try:
                            _code, _size, signature = server.access(struct, name_gpg, get=True)
                            if not signature.startswith(b"-----BEGIN PGP SIGNATURE-----") and uses_proxy:
                                uri = server.join(path_gpg)
                                raise ProxyError(uri, "download blocked by proxy?")
                        except DownloadError:
                            raise VerificationError(path_gpg, "Signature download failed")
                        error = verify_script(script, signature)
                        if error is not None:
                            raise VerificationError(path, "Invalid signature: %r" % error)
                        yield server, struct, None, path_gpg, signature
                    yield server, struct, phase, path, script
                except DownloadError as e:
                    ud.debug(ud.NETWORK, ud.ALL, "%s" % e)


class LocalUpdater(UniventionUpdater):
    """
    Direct file access to local repository.
    """

    def __init__(self):
        # type: () -> None
        UniventionUpdater.__init__(self)
        self.log = logging.getLogger('updater.LocalUpdater')
        self.log.addHandler(logging.NullHandler())
        repository_path = self.configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository')
        self.server = UCSLocalServer("%s/mirror/" % repository_path)  # type: _UCSServer


if __name__ == '__main__':
    import doctest
    exit(doctest.testmod()[0])
