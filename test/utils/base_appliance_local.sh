#!/bin/bash
#
# Copyright 2018 Univention GmbH
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

# ENV VARS:
# APP_ID
# KVM_USER
# UCS_VERSION
# KVM_BUILD_SERVER
#
# KVM_USER needs password less ssh access to APPS_SERVER, KVM_BUILD_SERVER and IMAGE_CONVERT_SERVER
# KVM_USER needs password less ssh access from IMAGE_CONVERT_SERVER to APPS_SERVER
# KVM_USER needs password less ssh access from KVM_BUILD_SERVER to APPS_SERVER

KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_app-appliance-app-appliance-${APP_ID}.qcow2"
APPS_BASE="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}"
APPS_SERVER="omar.knut.univention.de"
IMAGE_CONVERT_SERVER="docker.knut.univention.de"
KVM_IMAGE="Univention-App-${APP_ID}-KVM.qcow2"
VMPLAYER_IMAGE="Univention-App-${APP_ID}-vmware.zip"
TMPDIR="/tmp/build-${APP_ID}"
TMP_VMPLAYER_IMAGE="$TMPDIR/$VMPLAYER_IMAGE"
TMP_KVM_IMAGE="$TMPDIR/master.qcow2"

set -x
set -e

_ssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n "$@"
}

_scp () {
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no
}

_cleanup () {
	_ssh -l "$KVM_USER" "$KVM_BUILD_SERVER" "rm -f $TMP_KVM"
	_ssh -l "$KVM_USER" "$IMAGE_CONVERT_SERVER" "rm -f $TMP_KVM"
}

_kvm_image () {
	# copy KVM image
	_ssh -l "$KVM_USER" "$APPS_SERVER" "mkdir -p $APPS_BASE"
	_scp ${KVM_USER}@${KVM_BUILD_SERVER}:${TMP_KVM_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/$KVM_IMAGE"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum $KVM_IMAGE > $KVM_IMAGE.md5;
chmod 644 $KVM_IMAGE*;
"
}

_vmplayer_image () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
guestfish add ${TMP_KVM_IMAGE} : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App ${UCS_VERSION} Appliance APP_ID \(VMware\)\'\";
test -e ${TMP_VMPLAYER_IMAGE} && rm ${TMP_VMPLAYER_IMAGE} || true;
generate_appliance -m '$(< /tmp/ucsmaster-${APP_ID}.memory)' -p UCS -v ${UCS_VERSION}-with-${APP_ID} -o --vmware -s $TMP_KVM_IMAGE -f Univention-App-${APP_ID}
"
	_scp ${KVM_USER}@${IMAGE_CONVERT_SERVER}:${VMPLAYER_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "rm -f ${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum ${VMPLAYER_IMAGE} > ${VMPLAYER_IMAGE}.md5
chmod 644 ${VMPLAYER_IMAGE}*
"
}

create_app_images () {
	# convert image
	_ssh -l "$KVM_USER" "$KVM_BUILD_SERVER" "
mkdir -p $TMP_KVM
qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE
"
	# copy to image convert server for later steps
	_scp ${KVM_USER}@${KVM_BUILD_SERVER}:/${TMP_KVM} ${KVM_USER}@${IMAGE_CONVERT_SERVER}:/tmp

	_kvm_image
	_vmplayer_image
	_cleanup
}


# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@KVM_BUILD_SERVER mkdir -p /tmp/build-APP_ID/
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@KVM_BUILD_SERVER qemu-img convert -p -c -O qcow2 /var/lib/libvirt/images/build_ucsmaster-APP_ID.qcow2 /tmp/build-APP_ID/master.qcow2
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@KVM_BUILD_SERVER ucs-kt-remove build_ucsmaster-APP_ID
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r build@KVM_BUILD_SERVER:/tmp/build-APP_ID /tmp/
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r /tmp/build-APP_ID build@docker.knut.univention.de:/tmp/
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de mkdir -p /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /tmp/build-APP_ID/master.qcow2 build@omar.knut.univention.de:/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/Univention-App-APP_ID-KVM.qcow2
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de "(cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/; md5sum Univention-App-APP_ID-KVM.qcow2 >Univention-App-APP_ID-KVM.qcow2.md5; chmod 644 Univention-App-APP_ID-KVM.qcow2*)"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@KVM_BUILD_SERVER rm -f /tmp/build-APP_ID/master.qcow2
# LOCAL rm -f /tmp/build-APP_ID/master.qcow2
#command5:



## vmware player
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de guestfish add /tmp/build-APP_ID/master.qcow2 : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App 4.2 Appliance APP_ID \(VMware\)\'\"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de "test -e /tmp/build-APP_ID/Univention-App-APP_ID-vmware.zip && rm /tmp/build-APP_ID/Univention-App-APP_ID-vmware.zip || true"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de generate_appliance -m '$(< /tmp/ucsmaster-APP_ID.memory)' -p UCS -v 4.2-with-APP_ID -o --vmware -s /tmp/build-APP_ID/master.qcow2 -f "Univention-App-APP_ID"
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de:Univention-App-APP_ID-vmware.zip /tmp/build-APP_ID/
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /tmp/build-APP_ID/Univention-App-APP_ID-vmware.zip build@omar.knut.univention.de:/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/Univention-App-APP_ID-vmware.zip
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de "(cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/; md5sum Univention-App-APP_ID-vmware.zip >Univention-App-APP_ID-vmware.zip.md5; chmod 644 Univention-App-APP_ID-vmware.zip*)"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de rm -f Univention-App-APP_ID-vmware.zip
# LOCAL rm /tmp/build-APP_ID/Univention-App-APP_ID-vmware.zip
#command6:

## virtualbox
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de guestfish add /tmp/build-APP_ID/master.qcow2 : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App 4.2 Appliance APP_ID \(VirtualBox\)\'\"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de "test -e Univention-App-APP_ID-virtualbox.ova && rm Univention-App-APP_ID-virtualbox.ova || true"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de generate_appliance -m '$(< /tmp/ucsmaster-APP_ID.memory)' -p UCS -v 4.2-with-APP_ID -o --ova-virtualbox -s /tmp/build-APP_ID/master.qcow2 -f "Univention-App-APP_ID"
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de:Univention-App-APP_ID-virtualbox.ova /tmp/build-APP_ID/
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /tmp/build-APP_ID/Univention-App-APP_ID-virtualbox.ova build@omar.knut.univention.de:/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/Univention-App-APP_ID-virtualbox.ova
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de "(cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/; md5sum Univention-App-APP_ID-virtualbox.ova >Univention-App-APP_ID-virtualbox.ova.md5; chmod 644 Univention-App-APP_ID-virtualbox.ova*)"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de rm -f Univention-App-APP_ID-virtualbox.ova
# LOCAL rm -f /tmp/build-APP_ID/Univention-App-APP_ID-virtualbox.ova
#command7:
## vmware esxi
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de guestfish add /tmp/build-APP_ID/master.qcow2 : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App 4.2 Appliance APP_ID \(ESX\)\'\"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de "test -e Univention-App-APP_ID-ESX.ova && rm Univention-App-APP_ID-ESX.ova || true"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de generate_appliance -m '$(< /tmp/ucsmaster-APP_ID.memory)' -p UCS -v 4.2-with-APP_ID -o --ova-esxi -s /tmp/build-APP_ID/master.qcow2 -f "Univention-App-APP_ID"
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de:Univention-App-APP_ID-ESX.ova /tmp/build-APP_ID/
# LOCAL scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no /tmp/build-APP_ID/Univention-App-APP_ID-ESX.ova build@omar.knut.univention.de:/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/Univention-App-APP_ID-ESX.ova
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de "(cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/4.2/APP_ID/; md5sum Univention-App-APP_ID-ESX.ova >Univention-App-APP_ID-ESX.ova.md5; chmod 644 Univention-App-APP_ID-ESX.ova*)"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de rm -f Univention-App-APP_ID-ESX.ova
# LOCAL rm -f /tmp/build-APP_ID/Univention-App-APP_ID-ESX.ova
#command8:
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@docker.knut.univention.de rm -r /tmp/build-APP_ID/
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de "(cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/current/; test -L APP_ID && rm APP_ID; ln -s ../4.2/APP_ID/ APP_ID)"
# LOCAL ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no build@omar.knut.univention.de sudo update_mirror.sh appcenter.test/univention-apps/4.2/APP_ID appcenter.test/univention-apps/current/APP_ID
#files:
# utils/*sh /root/
# ~/ec2/scripts/activate-errata-test-scope.sh /root/
