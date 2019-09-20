#!/usr/bin/make -f
#
# ucs-school-lib
#  makefile
#
# Copyright 2012-2019 Univention GmbH
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

PKG := univention-lib
VERSION := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')

PO_FILE := python/de.po
MO_FILE := python/$(PKG).mo
PYTHON_FILES := $(shell find python -name "*.py")
INST_DIR := $(DESTDIR)/usr/share/locale/de/LC_MESSAGES/

.PHONY: build
build:: l10n

.PHONY: l10n
l10n:: $(MO_FILE)

$(MO_FILE):: $(PO_FILE)
	msgfmt --check --output-file "$@" "$<"

$(PO_FILE):: $(PO_FILE).tmp
	if [ -e "$@" ]; then \
		msgmerge --update --sort-output "$@" "$<"; \
		touch "$@"; \
	else \
		cp "$<" "$@"; \
	fi

$(PO_FILE).tmp:: $(PYTHON_FILES)
	xgettext --output=$(@) \
		--language=Python \
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
