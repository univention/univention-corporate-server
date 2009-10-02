#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention thin client bootsplash
#  bootsplash script
#
# Copyright (C) 2004-2007 Univention GmbH
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
import shutil
import univention.config_registry

cr = univention.config_registry.ConfigRegistry()
cr.load()

vga = cr.get("pxe/vga", "791")
thinClientInitrd = "/var/lib/univention-client-boot/initrd.splash"
bootsplashConfig = "/etc/bootsplash/themes/ucs/config/bootsplash-"
translate_vga = {
	791 : "1024x768",
	773 : "1024x768",
	790 : "1024x768",
	792 : "1024x768",
	769 : "640x480",
	784 : "640x480",
	786 : "640x480",
	785 : "640x480",
	771 : "800x600",
	787 : "800x600",
	788 : "800x600",
	789 : "800x600",
	775 : "1280x1024",
	793 : "1280x1024",
	794 : "1280x1024",
	795 : "1280x1024",
}
res = translate_vga.get(int(vga), "1024x768")
bootsplashConfig = bootsplashConfig + res + ".cfg"
if os.path.isfile(thinClientInitrd):
	shutil.copyfile(thinClientInitrd, "%s.bak" % thinClientInitrd)
cmd = "splash -s -f %s > %s" % (bootsplashConfig, thinClientInitrd) 	
os.system(cmd)
