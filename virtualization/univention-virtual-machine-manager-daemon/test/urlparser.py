#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  tests for the extension to urlparse for node URIs
#
# Copyright 2011-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

def __test():
	URIS = filter(None, map(lambda u: u.lstrip(), """\
	lxc:///
	openvz:///system
	openvz+unix:///system
	openvz://example.com/system
	openvz+tcp://example.com/system
	openvz+ssh://root@example.com/system
	qemu:///session
	qemu+unix:///session
	qemu:///system
	qemu+unix:///system
	qemu://example.com/system
	qemu+tcp://example.com/system
	qemu+ssh://root@example.com/system
	qemu+ssh://root@example.com/system?netcat=/bin/nc.openbsd&command=/usr/bin/ssh
	test:///default
	test:///path/to/driver/config.xml
	test+unix:///default
	test://example.com/default
	test+tcp://example.com/default
	test+ssh://root@example.com/default
	uml:///session
	uml+unix:///session
	uml:///system
	uml+unix:///system
	uml://example.com/system
	uml+tcp://example.com/system
	uml+ssh://root@example.com/system
	vbox:///session
	vbox+unix:///session
	vbox+tcp://user@example.com/session
	vbox+ssh://user@example.com/session
	vpx://example-vcenter.com/dc1/srv1
	esx://example-esx.com
	gsx://example-gsx.com
	esx://example-esx.com/?transport=http
	esx://example-esx.com/?no_verify=1
	vmwareplayer:///session
	vmwarews:///session
	vmwarews+tcp://user@example.com/session
	vmwarews+ssh://user@example.com/session
	xen:///
	xen+unix:///
	xen://example.com/
	xen+tcp://example.com/
	xen+ssh://root@example.com/
	""".splitlines()))
	for uri in URIS:
		data = urlparse.urlsplit(uri)
		u = urlparse.urlunsplit(data)
		try:
			assert uri == u
			print data
		except:
			print uri, data, u

if __name__ == '__main__':
	__test()
	import readline, rlcompleter
	readline.parse_and_bind("tab: complete")
