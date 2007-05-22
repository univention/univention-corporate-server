# 
# Univention Admin
#  Makefile for the admin debian package
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
#

DESTDIR=/tmp/foo
UNICONF=$(shell find uniconf -name '*.py' | sed 's/\.py/\.pyo/g')

%.pyo:	%.py
	@./py_compile $< $@

%.mo:	%.po
	msgfmt -o $@ $<

all:	$(UNICONF)

clean:
	@find uniconf -name '*.pyo' -exec rm \{\} \;

install: all
	install -d $(DESTDIR)/usr/share/univention-admin
	@for i in $(UNICONF); do\
		o=$(DESTDIR)/usr/share/univention-admin/uniconf/$${i#uniconf/};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done
	install -m 0755 uniconf/uniconf-client $(DESTDIR)/usr/share/univention-admin
