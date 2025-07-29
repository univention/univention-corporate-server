#
# PAM Univention Mail Cyrus
#  Makefile for the pam-univentionmailcyrus debian package
#
# SPDX-FileCopyrightText: 2005-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

TITLE=pam_univentionmailcyrus
#

DYNAMIC_LIBPAM=yes
MKDIR=mkdir -p
CFLAGS=-O2 -D_GNU_SOURCE -D_REENTRANT -DLINUX_PAM  -Wall -fPIC -Dlinux -Werror
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
		$(LD_D) -o $@ $(LIBOBJD) $(LINKLIBS) -lpam -lldap -luniventionpolicy

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
