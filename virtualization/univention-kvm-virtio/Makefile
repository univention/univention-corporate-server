#!/usr/bin/make -f
#
# Univention Xen VirtIO rules file
#
# Copyright 2011-2014 Univention GmbH
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

SOURCE := virtio-win-0.1-81.iso
TARGET := KVM_Windows_drivers_(virtio_1.1.81).iso

empty :=
space := $(empty) $(empty)
INSTALL ?= install

.PHONY: patch
patch: $(TARGET)
$(TARGET): $(SOURCE)
	-$(RM) "$@"
	xorriso -no_rc \
		-indev "$<" \
		-outdev "$@" \
		-compliance omit_version:lowercase:full_ascii \
		-mv /WXP/X86/\* /XP/X86/ -- \
		-rmdir /WXP/\* -- \
		-rmdir /WXP -- \
		-mv /WLH/X86/\*   /VISTA/X86/   -- \
		-mv /WLH/AMD64/\* /VISTA/AMD64/ -- \
		-rmdir /WLH/\* -- \
		-rmdir /WLH -- \
		-commit \
		-eject all || { rc=$$? ; $(RM) "$@" ; exit $$rc ; }

.PHONY: install
install: $(TARGET)
	$(INSTALL) -m755 -d $(DESTDIR)/usr/share/univention-kvm-virtio
	$(INSTALL) -m644 "$(TARGET)" "$(DESTDIR)/usr/share/univention-kvm-virtio/$(subst _,$(space),$(TARGET))"

.PHONY: get-orig-source
get-orig-source: $(SOURCE)
virtio-win-%.iso:
	wget -O "$@" "http://alt.fedoraproject.org/pub/alt/virtio-win/latest/images/$@"

.PHONY: clean
clean:
	$(RM) "$(TARGET)"
