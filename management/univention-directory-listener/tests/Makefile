#
# Univention Directory Listener
#  Makefile for testing the listener
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
SOURCES := $(wildcard test__*.c)
ALL ?= $(patsubst  %.c,%,$(SOURCES))

.PHONY: tests
tests: $(ALL)
	run-parts --verbose --regex='test__[^.]*$$' .

test__filter__cache_entry_ldap_filter_match: ../src/filter.o
test__utils__lower_utf8: ../src/utils.o
test__utils__same_dn: ../src/utils.o

include ../src/Makefile

CFLAGS += $(DB_CFLAGS) -I../src -fdata-sections -ffunction-sections
LDFLAGS += -Wl,--as-needed -Wl,--gc-sections
LDLIBS += -lldap -llber

.PHONY: clean
clean::
	$(RM) *.o
