# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  this baseconfig script automatically generates the SSL certificate for the AD host
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import os

ad_var = 'connector/ad/ldap/host'
ssl_path = '/etc/univention/ssl'

cert_cmd = '/usr/sbin/univention-certificate'
cert_log = '/var/log/univention/ad-connector-certificate.log'

def handler(baseConfig, changes):
	new = baseConfig.get(ad_var)
	path = os.path.join(ssl_path, new)
	if new and os.path.exists(path):
		os.system('%s new -name %s >> %s 2>&1' % (cert_cmd, new, cert_log))

