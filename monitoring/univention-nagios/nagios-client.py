#
# Univention Nagios
#  listener module: update configuration of local Nagios client
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import re
import stat

import univention.debug as ud

from listener import SetUID, configRegistry, run


description = 'Create configuration for Nagios nrpe server'
filter = '(objectClass=univentionNagiosServiceClass)'

__initscript = '/etc/init.d/nagios-nrpe-server'
__confdir = '/etc/nagios/nrpe.univention.d/'
__pluginconfdir = '/etc/nagios-plugins/config/'

__pluginconfdirstat = 0.0
__pluginconfig: dict[str, str] = {}


def readPluginConfig() -> None:
    global __pluginconfdirstat

    if __pluginconfdirstat != os.stat(__pluginconfdir)[8]:
        # save modification time
        __pluginconfdirstat = os.stat(__pluginconfdir)[8]

        ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: updating plugin config')

        with SetUID(0):
            for fn in os.listdir(__pluginconfdir):
                with open(os.path.join(__pluginconfdir, fn), 'rb') as fp:
                    content = fp.read().decode('UTF-8', 'replace')
                for cmddef in re.split(r'\s*define\s+command\s*\{', content):
                    mcmdname = re.search(r'^\s+command_name\s+(.*?)\s*$', cmddef, re.MULTILINE)
                    mcmdline = re.search(r'^\s+command_line\s+(.*?)\s*$', cmddef, re.MULTILINE)
                    if mcmdname and mcmdline:
                        __pluginconfig[mcmdname.group(1)] = mcmdline.group(1)
                        ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: read configline for plugin %r ==> %r' % (mcmdname.group(1), mcmdline.group(1)))


def replaceArguments(cmdline: str, args: list[str]) -> str:
    for i in range(9):
        if i < len(args):
            cmdline = re.sub(r'\$ARG%d\$' % (i + 1), args[i], cmdline)
        else:
            cmdline = re.sub(r'\$ARG%d\$' % (i + 1), '', cmdline)
    return cmdline


def writeConfig(fqdn: str, new: dict[str, list[bytes]]) -> None:
    readPluginConfig()

    name = new['cn'][0].decode('UTF-8')
    cmdline = 'PluginNameNotFoundError'

    # if no univentionNagiosHostname is present or current host is no member then quit
    if fqdn.encode("UTF-8") not in new.get('univentionNagiosHostname', []):
        return

    nagios_check_command = new.get('univentionNagiosCheckCommand', [b''])[0].decode('UTF-8')
    cmdline = __pluginconfig.get(nagios_check_command, cmdline)
    if new.get('univentionNagiosCheckArgs', [b''])[0]:
        cmdline = replaceArguments(cmdline, new['univentionNagiosCheckArgs'][0].decode('UTF-8').split('!'))
    cmdline = re.sub(r'\$HOSTADDRESS\$', fqdn, cmdline)
    cmdline = re.sub(r'\$HOSTNAME\$', fqdn, cmdline)

    filename = os.path.join(__confdir, "%s.cfg" % name)
    with SetUID(0), open(filename, 'w') as fp:
        fp.write('# Warning: This file is auto-generated and might be overwritten.\n')
        fp.write('#          Please use univention-directory-manager instead.\n')
        fp.write('# Warnung: Diese Datei wurde automatisch generiert und wird\n')
        fp.write('#          automatisch ueberschrieben. Bitte benutzen Sie\n')
        fp.write('#          stattdessen den Univention Directory Manager.\n')
        fp.write('\n')
        fp.write('command[%s]=%s\n' % (name, cmdline))
    ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: service %s written' % name)


def removeConfig(name: str) -> None:
    filename = os.path.join(__confdir, "%s.cfg" % name)
    with SetUID(0):
        if os.path.exists(filename):
            os.unlink(filename)


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    # ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN dn=%r' % (dn,))
    # ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN old=%r' % (old,))
    # ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: IN new=%r' % (new,))

    fqdn = '%(hostname)s.%(domainname)s' % configRegistry
    fqdn_b = fqdn.encode('UTF-8')

    if old and not new:
        ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: service %r deleted' % (old['cn'][0],))
        removeConfig(old['cn'][0].decode('UTF-8'))

    if old and \
            fqdn_b in old.get('univentionNagiosHostname', []) and \
            fqdn_b not in new.get('univentionNagiosHostname', []):
        # object changed and
        # local fqdn was in old object and
        # local fqdn is not in new object
        # ==> fqdn was deleted from list
        ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: host removed from service %r' % (old['cn'][0],))
        removeConfig(old['cn'][0].decode('UTF-8'))
    elif old and \
            old.get('univentionNagiosUseNRPE', [b''])[0] == b'1' and \
            new.get('univentionNagiosUseNRPE', [b''])[0] != b'1':
        # object changed and
        # local fqdn is in new object  (otherwise previous if-statement matches)
        # NRPE was enabled in old object
        # NRPE is disabled in new object
        # ==> remove config
        ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: nrpe disabled for service %r' % (old['cn'][0],))
        removeConfig(old['cn'][0].decode('UTF-8'))
    else:
        # otherwise:
        # - this host was configure in old and new object or
        # - this host is newly added to list or
        # - this object is new
        if 'univentionNagiosUseNRPE' in new and new['univentionNagiosUseNRPE'] and (new['univentionNagiosUseNRPE'][0] == b'1'):
            ud.debug(ud.LISTENER, ud.INFO, 'NAGIOS-CLIENT: writing service %r' % (new['cn'][0],))
            writeConfig(fqdn, new)


@SetUID(0)
def initialize() -> None:
    dirname = '/etc/nagios/nrpe.univention.d'

    if not os.path.exists(dirname):
        os.mkdir(dirname)


def deleteTree(dirname: str) -> None:
    if os.path.exists(dirname):
        for f in os.listdir(dirname):
            fn = os.path.join(dirname, f)
            mode = os.stat(fn)[stat.ST_MODE]
            if stat.S_ISDIR(mode):
                deleteTree(fn)
            else:
                os.unlink(fn)
        os.rmdir(dirname)


@SetUID(0)
def clean() -> None:
    dirname = '/etc/nagios/nrpe.univention.d'
    if os.path.exists(dirname):
        deleteTree(dirname)


def postrun() -> None:
    initscript = __initscript
    if configRegistry.is_true("nagios/client/autostart"):
        ud.debug(ud.LISTENER, ud.INFO, 'NRPED: Restarting server')
        run(initscript, ['nagios-nrpe-server', 'restart'], uid=0)
