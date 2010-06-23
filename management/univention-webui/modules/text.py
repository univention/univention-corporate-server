# -*- coding: utf-8 -*-
#
# Univention Webui
#  text.py
#
# Copyright 2004-2010 Univention GmbH
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
