#!/usr/bin/make -f
#
# univention-kde
#  makefile
#
# Copyright 2013-2019 Univention GmbH
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

PKG := univention-kde
VERSION := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')

PO_FILE := de.po
MO_FILE := $(PO_FILE:.po=.mo)
MO_INST_DIR := $(DESTDIR)/usr/share/locale/de/LC_MESSAGES
AUTOSTART_INST_DIR := $(DESTDIR)/usr/share/autostart

.PHONY: build install

build: $(MO_FILE)

install: $(MO_FILE)
	mkdir -p $(MO_INST_DIR)
	mkdir -p $(AUTOSTART_INST_DIR)
	install $(MO_FILE) $(MO_INST_DIR)/univention-root-login-notification.mo

$(MO_FILE): $(PO_FILE)
	msgfmt --check --output-file "$@" "$<"

$(PO_FILE): $(PO_FILE).tmp
	if [ -e "$@" ]; then \
		msgmerge --update --sort-output "$@" "$<"; \
		touch "$@"; \
	else \
		cp "$<" "$@"; \
	fi

$(PO_FILE).tmp: profiles/univention-root-login-notification
	xgettext --output=$(@) \
		--language=Shell \
		--keyword=N_:1 \
		--sort-output \
		--package-name=$(PKG) \
		--package-version=$(VERSION) \
		--msgid-bugs-address="packages@univention.de" \
		--copyright-holder="Univention GmbH" \
		$^

.PHONY: clean
clean::
	$(RM) $(MO_FILE) $(PO_FILE).tmp
