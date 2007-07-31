#
# Univention Directory Listener
#  Makefile for the listener
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
DB_LDADD=-ldb3
DB_CFLAGS=-I/usr/include/db3 -DWITH_DB3
DB_OBJS=cache.o cache_entry.o cache_lowlevel.o base64.o

CFLAGS=-g -Wall -D_FILE_OFFSET_BITS=64 $(DB_CFLAGS)
LDADD=-g -luniventiondebug
LISTENER_LDADD=$(LDADD) -luniventionpolicy -lldap -lpython2.4 $(DB_LDADD)
LISTENER_OBJS=main.o notifier.o transfile.o handlers.o cache.o cache_entry.o cache_lowlevel.o change.o network.o filter.o signals.o base64.o select_server.o
DUMP_LDADD=$(LDADD) -lldap $(DB_LDADD)
DUMP_OBJS=dump.o dump_signals.o $(DB_OBJS)
DEMO_LDADD=$(LDADD)
DEMO_OBJS=demo.o network.o
VERIFY_LDADD=$(LDADD) -lldap $(DB_LDADD)
VERIFY_OBJS=verify.o dump_signals.o $(DB_OBJS)


all: listener dump verify

listener: $(LISTENER_OBJS)
	$(CC) -o listener $(LISTENER_OBJS) $(LISTENER_LDADD)

dump: $(DUMP_OBJS)
	$(CC) -o dump $(DUMP_OBJS) $(DUMP_LDADD)

demo: $(DEMO_OBJS)
	$(CC) -o demo $(DEMO_OBJS) $(DEMO_LDADD)

verify: $(VERIFY_OBJS)
	$(CC) -o verify $(VERIFY_OBJS) $(VERIFY_LDADD)

clean:
	rm -f *.o listener dump demo verify *.db3 *.db42
