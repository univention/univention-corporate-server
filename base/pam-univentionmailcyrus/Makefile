#
# PAM Univention Mail Cyrus
#  Makefile for the pam-univentionmailcyrus debian package
#
# Copyright (C) 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

TITLE=pam_univentionmailcyrus
#

DYNAMIC_LIBPAM=yes
MKDIR=mkdir -p
CFLAGS=-O2 -D_GNU_SOURCE -D_REENTRANT -DLINUX_PAM  -Wall -fPIC -Dlinux
DYNAMIC=-DPAM_DYNAMIC
CPPFLAGS=
TARGET_ARCH=-Di386
LD_D=gcc -shared -Wl,-x
INSTALL=install
LINKLIBS=
DESTDIR=
SECUREDIR=/lib/security
SHLIBMODE=0644

LIBSRC = $(TITLE).c
LIBOBJ = $(TITLE).o
LIBOBJD = $(addprefix dynamic/,$(LIBOBJ))

dynamic/%.o : %.c
	$(CC) $(CFLAGS) $(DYNAMIC) $(CPPFLAGS) $(TARGET_ARCH) -c $< -o $@

LIBSHARED = $(TITLE).so

####################### don't edit below #######################

all: dirs $(LIBSHARED)

dirs:
	$(MKDIR) ./dynamic


$(LIBOBJD): $(LIBSRC)

$(LIBSHARED):	$(LIBOBJD)
		$(LD_D) -o $@ $(LIBOBJD) $(LINKLIBS) -lpam -lldap

install: all
	$(MKDIR) $(DESTDIR)$(SECUREDIR)
	$(INSTALL) -m $(SHLIBMODE) $(LIBSHARED) $(DESTDIR)$(SECUREDIR)

remove:
	rm -f $(DESTDIR)$(SECUREDIR)/$(TITLE).so

clean:
	rm -f $(LIBOBJD) $(LIBOBJS) core *~ ${LIBSHARED}
	rm -rf ./dynamic


extraclean: clean
	rm -f *.a *.o *.so *.bak

.c.o:
	$(CC) $(CFLAGS) -c $<
