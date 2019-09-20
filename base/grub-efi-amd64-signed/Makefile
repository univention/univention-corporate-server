#!/usr/bin/make -f
#
# Copyright 2018-2019 Univention GmbH
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

ALL := gcdx64.efi.signed grubx64.efi.signed
ARCH := x86_64-efi

# For sbsign:
#KEY := shim.rsa
#CERT := shim.pem

# For pesign:
#TOKEN := Univention GmbH
#CERT := # Univention 2014

GRUBDIR := /usr/lib/grub/$(ARCH)
MODULE_FILES := $(wildcard $(GRUBDIR)/*.mod)
MODULE_NAMES := $(basename $(notdir $(MODULE_FILES)))
MODULES_SKIP := linux cb%
MODULES_gcdx64 := $(filter-out $(MODULES_SKIP),$(MODULE_NAMES))
MODULES_grubx64 := $(shell cat grubx64.lst)

.PHONY: all
all: $(ALL)

%.efi.signed: %.efi
ifneq ($(TOKEN),)
	pesign --sign --in "$<" --force --out "$@" --nss-token "$(TOKEN)" --certficate "$(CERT)" --verbose
else ifneq ($(KEY),)
	sbsign --key "$(KEY)" --cert "$(CERT)" --output "$@" "$<"
endif

%.efi: %.cfg
	grub-mkimage -d "$(GRUBDIR)" -o "$@" -O "$(ARCH)" -c "$<" -p /efi/boot $(MODULES_$*)

.PHONY: clean
clean::
	$(RM) $(ALL:.signed=)

.PHONY: maintainerclean
maintainerclean:: clean
	$(RM) $(ALL)
