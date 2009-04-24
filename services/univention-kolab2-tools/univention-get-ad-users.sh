#!/bin/sh
# -*- coding: utf-8 -*-
#
# Univention Kolab2 Tools
#
# Copyright (C) 2008 Univention GmbH
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

BASE=DC=btag,DC=de
USER=cn=testadmin,ou=Administratoren,$BASE
AD_SERVER=172.24.103.42

ldapsearch -x -D $USER -W -h $AD_SERVER -b $BASE '(&(objectClass=organizationalPerson)(sAMAccountName=*)(!(sAMAccountName=*$))(!(mail=SystemMailbox{*)))' sAMAccountName mail -LLL | ldapsearch-wrapper | grep -v "dn: " |  sed -e :a -e '/^mail/N;s/mail: \([^\n]*\)\nsAMAccountName: \(.*\)/\2:\1/; ta' | grep -v '^$'
