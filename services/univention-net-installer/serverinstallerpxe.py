#!/usr/bin/python3
#
# Univention Server Installation
#  listener module: creates PXE boot configurations
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
from textwrap import dedent
from urllib.parse import urljoin, urlparse

import univention.debug as ud

import listener


description = 'PXE configuration for the Server installer'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)(objectClass=univentionClient))'
attributes = [
    'univentionServerReinstall',
    'aRecord',
    'univentionServerInstallationProfile',
    'univentionServerInstallationOption',
]

EMPTY = (b'',)
PXEBASE = '/var/lib/univention-client-boot/pxelinux.cfg'
FQDN = '%(hostname)s.%(domainname)s' % listener.configRegistry
URLBASE = listener.configRegistry.get(
    'pxe/installer/profiles',
    'http://%s/univention-client-boot/preseed/' % (FQDN,))


def ip_to_hex(ip: str) -> str:
    o = ip.split('.')
    if len(o) != 4:
        return ''
    return ''.join('%02X' % int(_) for _ in o)


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    listener.configRegistry.load()
    pxeconfig = gen_pxe(new)
    remove_pxe(old)
    if pxeconfig:
        create_pxe(new, pxeconfig)


def gen_pxe(new: dict[str, list[bytes]]) -> str | None:
    args = [listener.configRegistry.get('pxe/installer/append')]
    if args[0] is None:
        profile = new.get('univentionServerInstallationProfile', EMPTY)[0].decode('UTF-8')
        if not profile:
            return
        url = urljoin(URLBASE, profile)

        vga = listener.configRegistry.get("pxe/installer/vga")
        args += [
            'video=vesa:ywrap,mtrr',
            'vga=%s' % (vga,),
        ] if vga else [
            # plymouth
            'nosplash',
            'debian-installer/framebuffer=false',
            'DEBIAN_FRONTEND=text',
        ]

        # <https://wiki.debianforum.de/Debian-Installation_%C3%BCber_PXE,_TFTP_und_Preseed>
        server = listener.configRegistry.get("repository/online/server", FQDN)
        if "://" in server:
            url = urlparse(server)
            scheme, hostname, path = url.scheme, url.hostname, url.path
        else:
            scheme, hostname, path = "http", server, "/"

        args += [
            # Kernel
            'quiet' if listener.configRegistry.is_true('pxe/installer/quiet', False) else '',
            'loglevel=%s' % listener.configRegistry.get('pxe/installer/loglevel', '0'),
            # Debian installer
            'auto-install/enable=true',
            'preseed/url=%s' % (url,),
            'mirror/protocol=%s' % (scheme,),
            'mirror/http/hostname=%s' % (hostname,),
            'mirror/http/directory=%s' % (path,),
            # 'DEBCONF_DEBUG=5',
        ]
    args.append(new.get('univentionServerInstallationOption', EMPTY)[0].decode('UTF-8'))
    # <http://www.syslinux.org/wiki/index.php/SYSLINUX>: The entire APPEND
    # statement must be on a single line. A feature to break up a long line
    # into multiple lines will be added eventually.
    append = ' '.join(arg for arg in args if arg)

    return dedent('''\
            # Perform a profile installation by default
            PROMPT 0
            TIMEOUT 100
            DEFAULT linux

            LABEL linux
                LINUX %(kernel)s
                INITRD %(initrd)s
                APPEND %(append)s
                IPAPPEND %(ipappend)s

            LABEL local
                LOCALBOOT 0
            ''') % {
        'kernel': listener.configRegistry.get('pxe/installer/kernel', 'linux'),
        'initrd': listener.configRegistry.get('pxe/installer/initrd', 'initrd.gz'),
        'append': append,
        'ipappend': listener.configRegistry.get('pxe/installer/ipappend', '0'),
    }


def remove_pxe(old: dict[str, list[bytes]]) -> None:
    try:
        basename = ip_to_hex(old['aRecord'][0].decode('ASCII'))
    except LookupError:
        return
    else:
        if not basename:
            ud.debug(ud.LISTENER, ud.ERROR, 'PXE: invalid old IP address %r' % (old['aRecord'][0],))
            return
        filename = os.path.join(PXEBASE, basename)
        listener.setuid(0)
        try:
            if os.path.exists(filename):
                os.unlink(filename)
        finally:
            listener.unsetuid()


def create_pxe(new: dict[str, list[bytes]], pxeconfig: str) -> None:
    try:
        basename = ip_to_hex(new['aRecord'][0].decode('ASCII'))
    except LookupError:
        return
    else:
        cn = new['cn'][0].decode('UTF-8')
        ud.debug(ud.LISTENER, ud.INFO, 'PXE: writing configuration for host %s' % cn)

        if not basename:
            ud.debug(ud.LISTENER, ud.ERROR, 'PXE: invalid new IP address %s' % new['aRecord'][0])
            return
        filename = os.path.join(PXEBASE, basename)

        if new.get('univentionServerReinstall', EMPTY)[0] == b'1':
            listener.setuid(0)
            try:
                with open(filename, 'w') as fd:
                    fd.write(pxeconfig)
            finally:
                listener.unsetuid()
