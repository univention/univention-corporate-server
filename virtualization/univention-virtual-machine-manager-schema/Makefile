#!/usr/bin/make -f
#
# UCS Virtual Machine Manager schema
#
# Copyright 2012-2014 Univention GmbH
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

UVMM_SCHEMA=univention-virtual-machine-manager-schema
PO_FILES := $(shell find modules -name '*.po')
MO_FILES := $(foreach po,$(PO_FILES),modules/i18n/$(notdir $(po:.po=))/LC_MESSAGES/$(UVMM_SCHEMA).mo)

.PHONY: build
build: $(MO_FILES)

define build_mo
modules/i18n/$(1)/LC_MESSAGES/$(UVMM_SCHEMA).mo: modules/univention/admin/handlers/uvmm/$(1).po
	mkdir -p $$(dir $$@)
	msgfmt --check --output-file $$@ $$<
endef

$(foreach po,$(PO_FILES),$(eval $(call build_mo,$(notdir $(po:.po=)))))

.PHONY: clean
clean::
	$(RM) $(MO_FILES)

.PHONY: update-po
update-po: $(PO_FILES)
$(PO_FILES) : %.po : modules/univention/admin/handlers/uvmm/messages.pot
	msgmerge -o $@.new $@ $<
	mv $@.new $@
modules/univention/admin/handlers/uvmm/messages.pot: $(wildcard modules/univention/admin/handlers/uvmm/*.py)
	xgettext --output=$@ \
		--language=Python \
		--msgid-bugs-address="packages@univention.de" \
		--copyright-holder="Univention GmbH" \
		$^
