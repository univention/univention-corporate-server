#
# Univention Directory Reports
#  Makefile fo package generation
#
# Copyright (C) 2007 Univention GmbH
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

DESTDIR=/tmp/foo
MODS=$(shell find modules -name '*.py' | sed 's/\.py/\.pyo/g')
MOFILES=$(shell find modules -name '*.po' | sed 's/\.po/\.mo/g')

%.pyo:	%.py
	@./univention-pycompile ${OPTION} $< $@

%.mo:	%.po
	msgfmt -o $@ $<

all:	$(MODS) $(MOFILES)

clean:
	find modules \( -name '*.pyo' -o -name '*.pyo.pp' -o -name '*.pot' -o -name '*.pox' \) -exec rm \{\} \;
	rm -f $(MOFILES)
	rm -rf build

install: all
	@for i in $(MODS); do\
		o=$(DESTDIR)/usr/lib/python2.4/site-packages/$${i#modules/};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done
	@for i in $(MOFILES); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^modules/,,;s,/,-,g'`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
