#!/usr/bin/make -f
#
# Copyright 2017-2019 Univention GmbH
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

INSTALL ?= install
DIR := $(DESTDIR)/usr/share/univention-kvm-compat

.PHONY: all
all:

.PHONY: clean
clean:

.PHONY: install
install:
	# See qemu-kvm-0.14.1+dfsg/debian/rules:155
	$(INSTALL) -m755 -d $(DIR)/pc-0.14
	$(INSTALL) -m644 /usr/lib/etherboot/rtl8139.rom $(DIR)/pc-0.14/pxe-rtl8139.rom
	$(INSTALL) -m644 /usr/lib/etherboot/e1000-82540em.rom $(DIR)/pc-0.14/pxe-e1000.rom
	$(INSTALL) -m644 /usr/lib/etherboot/ne.rom $(DIR)/pc-0.14/pxe-ne2k_isa.rom
	$(INSTALL) -m644 /usr/lib/etherboot/virtio-net.rom $(DIR)/pc-0.14/pxe-virtio.rom
	$(INSTALL) -m644 /usr/lib/etherboot/rtl8029.rom $(DIR)/pc-0.14/pxe-ne2k_pci.rom
	$(INSTALL) -m644 /usr/lib/etherboot/pcnet32.rom $(DIR)/pc-0.14/pxe-pcnet.rom
	# See qemu-kvm-1.1.2+dfsg/debian/rules:150
	$(INSTALL) -m755 -d $(DIR)/pc-1.1
	$(INSTALL) -m644 /usr/lib/ipxe/e1000_82540.rom $(DIR)/pc-1.1/pxe-e1000.rom
	$(INSTALL) -m644 /usr/lib/ipxe/eepro100.rom $(DIR)/pc-1.1/pxe-eepro100.rom
	$(INSTALL) -m644 /usr/lib/ipxe/ns8390.rom $(DIR)/pc-1.1/pxe-ne2k_pci.rom
	$(INSTALL) -m644 /usr/lib/ipxe/pcnet32.rom $(DIR)/pc-1.1/pxe-pcnet.rom
	$(INSTALL) -m644 /usr/lib/ipxe/rtl8139.rom $(DIR)/pc-1.1/pxe-rtl8139.rom
	$(INSTALL) -m644 /usr/lib/ipxe/virtio-net.rom $(DIR)/pc-1.1/pxe-virtio.rom
