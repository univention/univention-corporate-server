#
# Univention Directory Listener
#  Makefile for the listener
#
# Copyright 2004-2019 Univention GmbH
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
CC ?= gcc

DB_LDLIBS := -llmdb
DB_OBJS := cache.o cache_dn.o cache_entry.o cache_lowlevel.o base64.o filter.o

LDAP_LDLIBS := -lldap -llber

CFLAGS += -Wall -Werror -D_FILE_OFFSET_BITS=64
LDLIBS := -luniventiondebug -luniventionconfig -licuuc
LISTENER_LDLIBS := -luniventionpolicy $(LDAP_LDLIBS) -lpython2.7 $(DB_LDLIBS)
LISTENER_OBJS := main.o notifier.o transfile.o handlers.o change.o network.o signals.o select_server.o utils.o $(DB_OBJS)
DUMP_LDLIBS := $(LDAP_LDLIBS) $(DB_LDLIBS)
DUMP_OBJS := dump.o dump_signals.o utils.o $(DB_OBJS)
DEMO_OBJS := demo.o network.o utils.o
VERIFY_LDLIBS := $(LDAP_LDLIBS) $(DB_LDLIBS)
VERIFY_OBJS := verify.o dump_signals.o utils.o $(DB_OBJS)
CONVERT_LDLIBS := $(LDAP_LDLIBS) $(DB_LDLIBS) -ldb3
CONVERT_OBJS := convert.o cache_bdb.o dump_signals.o utils.o $(DB_OBJS)

ALL ?= listener dump verify convert
.PHONY: all
all: $(ALL)

listener: $(LISTENER_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(LISTENER_LDLIBS)

dump: $(DUMP_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(DUMP_LDLIBS)

demo: $(DEMO_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(DEMO_LDLIBS)

verify: $(VERIFY_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(VERIFY_LDLIBS)

convert: $(CONVERT_OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS) $(CONVERT_LDLIBS)

cache_bdb.o: cache_bdb.c
	$(CC) $(CFLAGS) -I/usr/include/db3 -DWITH_DB3 -c $^

.PHONY: clean
clean::
	$(RM) *.o
	$(RM) $(ALL)
