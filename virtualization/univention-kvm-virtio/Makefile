#!/usr/bin/make -f
#
# Univention VirtIO rules file
#
# Copyright 2011-2019 Univention GmbH
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

SOURCE := virtio-win-0.1.141.iso
TARGET := KVM_Windows_drivers_(virtio_1.1.141).iso

empty :=
space := $(empty) $(empty)
INSTALL ?= install

.PHONY: all
all:

.PHONY: install
install: $(SOURCE)
	$(INSTALL) -m755 -d $(DESTDIR)/usr/share/univention-kvm-virtio
	$(INSTALL) -m644 "$<" "$(DESTDIR)/usr/share/univention-kvm-virtio/$(subst _,$(space),$(TARGET))"

.PHONY: get-orig-source
get-orig-source: $(SOURCE)
virtio-win-%.iso:
	wget -O "$@" "https://updates.software-univention.de/download/large-build-files/virtio/$@"
	echo "909f4437b69cba1edfa857326986eb8c4b58835169d70117a5ff57bfa4ebc48f74d6ffa05de50732fb60551166544160fa3b4ec5c59cfb98daeb789902a9b119  $@" | sha512sum -c
	#wget -O "$@" "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-$*-1/$@"
