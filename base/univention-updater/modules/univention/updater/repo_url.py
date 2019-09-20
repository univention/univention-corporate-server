#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention Updater: UCR Repository Server URL
"""
# Copyright 2008-2019 Univention GmbH
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

from urlparse import urlsplit
from urllib import quote
from copy import copy


class UcsRepoUrl(object):
    """
    UCS repository server base URL.
    """

    DEFAULT = 'https://updates.software-univention.de/'

    def __init__(self, ucr, prefix, default=None):
        '''
        >>> UcsRepoUrl({'_/server': 'hostname'}, '_').path
        ''
        >>> UcsRepoUrl({'_/server': 'hostname', '_/prefix': '/p'}, '_').path
        '/p/'
        >>> UcsRepoUrl({'_/server': 'hostname', '_/prefix': 'path'}, '_').path
        '/path/'
        >>> UcsRepoUrl({}, '', UcsRepoUrl({'_/server': 'https://hostname/'}, '_')).private()
        'https://hostname/'
        >>> UcsRepoUrl({'_/server': 'hostname'}, '_', UcsRepoUrl({'_/server': 'https://hostname:80/'}, '_')).private()
        'http://hostname/'
        '''
        def ucrv(key, default=None):
            return ucr.get('%s/%s' % (prefix, key), default)

        server = ucrv('server', '')
        url = urlsplit(server)
        if url.scheme:
            self.scheme = url.scheme
            self.username = url.username
            self.password = url.password
            self.hostname = url.hostname
            port = url.port
            prefix = url.path
        else:
            if default is None:
                default = self.DEFAULT
            elif isinstance(default, UcsRepoUrl):
                default = default.private()
            default = urlsplit(default)

            self.username = ucrv('username', default.username)
            self.password = ucrv('password', default.password)
            if server:
                self.hostname = server
                port = ucrv('port', 80)
                self.scheme = 'https' if port == 443 else 'http'
                prefix = ucrv('prefix', None)
            else:
                self.hostname = default.hostname
                port = ucrv('port', default.port)
                self.scheme = default.scheme
                prefix = ucrv('prefix', default.path)
        self.port = int(port if port else 443 if self.scheme == 'https' else 80)
        if prefix:
            prefix = prefix.strip('/')
            if prefix:
                self.path = '/%s/' % (prefix,)
            else:
                self.path = '/'
        else:
            self.path = ''

    @property
    def cred(self):
        if self.username:
            # FIXME http://bugs.debian.org/500560: [@:/] don't work
            return '%s:%s@' % (quote(self.username), quote(self.password))
        return ''

    @property
    def _port(self):
        return ':%d' % (self.port) if (self.scheme, self.port) not in (
            ('http', 80),
            ('https', 443)
        ) else ''

    @property
    def _path(self):
        return quote('/%s' % (self.path.lstrip('/'),))

    def public(self):
        """
        URI without credentials.

        >>> UcsRepoUrl({'_/server': 'hostname'}, '_').public()
        'http://hostname/'
        >>> UcsRepoUrl({'_/server': 'hostname', '_/username': 'user', '_/password': 'pass'}, '_').public()
        'http://hostname/'
        >>> UcsRepoUrl({'_/server': 'https://hostname'}, '_').public()
        'https://hostname/'
        >>> UcsRepoUrl({'_/server': 'https://user:pass@hostname'}, '_').public()
        'https://hostname/'
        """
        return '{0.scheme}://{0.hostname}{0._port}{0._path}'.format(self)

    def private(self):
        """
        URI with credentials.

        >>> UcsRepoUrl({'_/server': 'hostname'}, '_').private()
        'http://hostname/'
        >>> UcsRepoUrl({'_/server': 'hostname', '_/username': 'user', '_/password': 'pass'}, '_').private()
        'http://user:pass@hostname/'
        >>> UcsRepoUrl({'_/server': 'https://hostname'}, '_').private()
        'https://hostname/'
        >>> UcsRepoUrl({'_/server': 'https://user:pass@hostname'}, '_').private()
        'https://user:pass@hostname/'
        """
        return '{0.scheme}://{0.cred}{0.hostname}{0._port}{0._path}'.format(self)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__,
            {},
            '',
            self.private(),
        )

    def __eq__(self, other):
        return self.private() == other.private()

    def __add__(self, rel):
        """
        Append relative path component.

        >>> (UcsRepoUrl({'_/server': 'http://hostname'}, '_') + '/b').public()
        'http://hostname/b'
        >>> (UcsRepoUrl({'_/server': 'http://hostname/'}, '_') + '/b').public()
        'http://hostname/b'
        >>> (UcsRepoUrl({'_/server': 'http://hostname/a'}, '_') + '/b').public()
        'http://hostname/a/b'
        >>> (UcsRepoUrl({'_/server': 'http://hostname/a/'}, '_') + '/b').public()
        'http://hostname/a/b'
        >>> (UcsRepoUrl({'_/server': 'http://hostname/a/'}, '_') + '/b/').public()
        'http://hostname/a/b/'
        """
        cfg = copy(self)
        cfg.path = '%s/%s' % (self._path.rstrip('/'), str(rel).lstrip('/'))
        return cfg


if __name__ == '__main__':
    import doctest
    from sys import exit
    exit(doctest.testmod()[0])
