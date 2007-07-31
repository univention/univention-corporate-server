#
# Univention Directory Notifier
#  Makefile
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
CC=gcc
CFLAGS=-Wall -g -D_FILE_OFFSET_BITS=64
LDADD=-luniventiondebug
NOTIFIER_OBJS=index.o sem.o cache.o callback.o network.o notify.o univention-directory-notifier.o
NOTIFIER_LDADD=$(LDADD) -lldap -lpthread
DUMP_OBJS=index.o index-dump.o
DUMP_LDADD=$(LDADD)


all: univention-directory-notifier

univention-ldap-notifier: $(NOTIFIER_OBJS)
	$(CC) $(CFLAGS) -o univention-directory-notifier $(NOTIFIER_OBJS) $(NOTIFIER_LDADD)
	
univention-ldap-notifier-index-dump: $(DUMP_OBJS)
	$(CC) $(CFLAGS) -o univention-directory-notifier-index-dump $(DUMP_OBJS) $(DUMP_LDADD)

clean:
	@rm -f *.o core univention-directory-notifier univention-directory-notifier-index-dump
