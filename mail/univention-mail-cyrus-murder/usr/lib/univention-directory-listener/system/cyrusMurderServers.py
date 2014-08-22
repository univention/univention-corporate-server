# -*- coding: utf-8 -*-
#
# Univention Cyrus Murder
#  listener module: Cyrus Murder frontend list
#
# Copyright (C) 2011-2014 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

__package__='' 	# workaround for PEP 366
import listener
import os
import univention.config_registry
import univention.debug

name='cyrusMurderServers'
description='Update Cyrus Murder Server List'
filter="(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=Cyrus Murder))"
attributes=["uid"]
var = "mail/cyrus/murder/servers"
reload = False

def initialize():

	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, '%s: Initialize' % name)

	return

def setVar(content):

	listener.setuid(0)
	try:
		univention.config_registry.handler_set([u'%s=%s' % (var, " ".join(content))])
	finally:
		listener.unsetuid

	return

def addServer(uid, ucr):

	global reload

	servers = ucr.get(var, "").split(" ")
	if not uid in servers:
		servers.append(uid)
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, '%s: - adding %s to %s' % (name, uid, var))
		setVar(servers)
		reload = True

	return
	
def removeServer(uid, ucr):

	global reload
	
	servers = ucr.get(var, "").split(" ")
	newServers = []
	serverRemoved = False

	for server in servers:
		server = server.strip()
		if server == uid:
			serverRemoved = True
		else:
			newServers.append(server)

	if serverRemoved:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, '%s: - removed %s from %s' % (name, uid, var))
		setVar(servers)
		reload = True

	return

def handler(dn, new, old):

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	# added
	if new and not old:
		if new.has_key('uid'):
			addServer(new['uid'][0], configRegistry)
	# removed
	if old and not new:
		if old.has_key('uid'):
			removeServer(old['uid'][0], configRegistry)
	# modified
	else:
		if old.has_key('uid'):
			removeServer(old['uid'][0], configRegistry)
		if new.has_key('uid'):
			addServer(new['uid'][0], configRegistry)

	return

def postrun():

	global reload
	if reload:

		initFile = "/etc/init.d/cyrus2.2"
		if os.path.exists("/etc/init.d/cyrus-imapd"):
			initFile = "/etc/init.d/cyrus-imapd"

		listener.setuid(0)
		try:
			listener.run(initFile, [os.path.basename(initFile), 'reload'], uid=0, wait=1)
		finally:
			listener.unsetuid
		reload = False

	return
