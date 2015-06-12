#
# Univention Directory Listener
#  Makefile for the listener
#
# Copyright 2004-2015 Univention GmbH
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
#
CC=gcc
DB_LDADD=-ldb3
DB_CFLAGS=-I/usr/include/db3 -DWITH_DB3
DB_OBJS=cache.o cache_entry.o cache_lowlevel.o base64.o

CFLAGS=-g -Wall -Werror -D_FILE_OFFSET_BITS=64 $(DB_CFLAGS)
LDADD=-g -luniventiondebug -licuuc
LISTENER_LDADD=$(LDADD) -luniventionpolicy -lldap -lpython2.7 $(DB_LDADD)
LISTENER_OBJS=main.o notifier.o transfile.o handlers.o cache.o cache_entry.o cache_lowlevel.o change.o network.o filter.o signals.o base64.o select_server.o
DUMP_LDADD=$(LDADD) -lldap -luniventionconfig $(DB_LDADD)
DUMP_OBJS=dump.o dump_signals.o $(DB_OBJS)
DEMO_LDADD=$(LDADD) -luniventionconfig
DEMO_OBJS=demo.o network.o
VERIFY_LDADD=$(LDADD) -lldap -luniventionconfig $(DB_LDADD)
VERIFY_OBJS=verify.o dump_signals.o $(DB_OBJS)

.PHONY: all
all: listener dump verify

listener: $(LISTENER_OBJS)
	$(CC) -o $@ $^ $(LISTENER_LDADD)

dump: $(DUMP_OBJS)
	$(CC) -o $@ $^ $(DUMP_LDADD)

demo: $(DEMO_OBJS)
	$(CC) -o $@ $^ $(DEMO_LDADD)

verify: $(VERIFY_OBJS)
	$(CC) -o $@ $^ $(VERIFY_LDADD)

.PHONY: clean
clean:
	$(RM) *.o listener dump demo verify *.db3 *.db42
