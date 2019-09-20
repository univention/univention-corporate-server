#
# PAM Univention Samba Domain
#  Makefile for the pam_univentionsambadomain module
#
# Copyright 2011-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

TITLE=pam_univentionsambadomain
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
		$(LD_D) -o $@ $(LIBOBJD) $(LINKLIBS) -lpam -luniventionconfig

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
