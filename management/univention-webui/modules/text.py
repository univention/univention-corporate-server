# -*- coding: utf-8 -*-
#
# Univention Webui
#  text.py
#
# Copyright (C) 2004-2009 Univention GmbH
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

from uniconf import *

class text(uniconf):
    def mytype(self):
        return "text"
    def myxmlrepr(self,xmlob,node):
        l=0
        last=len(self.args["text"])
        for line in self.args["text"]:
            l+=1
            texttag=xmlob.createTextNode(line)
            node.appendChild(texttag)
            if not l==last:
                br=xmlob.createElement("break")
                node.appendChild(br)


        return xmlob

class htmltext(uniconf):
    def mytype(self):
        return "htmltext"
    def myxmlrepr(self,xmlob,node):
        l=0
        last=len(self.args["htmltext"])
        for line in self.args["htmltext"]:
            l+=1
            texttag=xmlob.createTextNode(line)
            node.appendChild(texttag)
            if not l==last:
                br=xmlob.createElement("break")
                node.appendChild(br)


        return xmlob
