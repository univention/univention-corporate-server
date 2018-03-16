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

KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_app-appliance-${APP_ID}.qcow2"
APPS_BASE="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}"
APPS_SERVER="omar.knut.univention.de"
IMAGE_CONVERT_SERVER="docker.knut.univention.de"
TMPDIR="/tmp/build-${APP_ID}"

VMPLAYER_IMAGE="Univention-App-${APP_ID}-vmware.zip"
TMP_VMPLAYER_IMAGE="$TMPDIR/$VMPLAYER_IMAGE"

KVM_IMAGE="Univention-App-${APP_ID}-KVM.qcow2"
TMP_KVM_IMAGE="$TMPDIR/master.qcow2"

VBOX_IMAGE="Univention-App-${APP_ID}-virtualbox.ova"
TMP_VBOX_IMAGE="$TMPDIR/$VBOX_IMAGE"

ESX_IMAGE="Univention-App-${APP_ID}-ESX.ova"
TMP_ESX_IMAGE="$TMPDIR/$ESX_IMAGE"

set -x
set -e

_ssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o BatchMode=yes -n "$@"
}

_scp () {
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "$@"
}

_kvm_image () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
guestfish add ${TMP_KVM_IMAGE} : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App ${UCS_VERSION} Appliance ${APP_ID} \(KVM\)\'\";
"
	_scp ${KVM_USER}@${IMAGE_CONVERT_SERVER}:${TMP_KVM_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/$KVM_IMAGE"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum ${KVM_IMAGE} > ${KVM_IMAGE}.md5
chmod 644 ${KVM_IMAGE}*
"
}

_vmplayer_image () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
guestfish add ${TMP_KVM_IMAGE} : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App ${UCS_VERSION} Appliance ${APP_ID} \(VMware\)\'\";
test -e ${TMP_VMPLAYER_IMAGE} && rm ${TMP_VMPLAYER_IMAGE} || true;
generate_appliance -m $MEMORY -p UCS -v ${UCS_VERSION}-with-${APP_ID} -o --vmware -s $TMP_KVM_IMAGE -f Univention-App-${APP_ID}
"
	_scp ${KVM_USER}@${IMAGE_CONVERT_SERVER}:${VMPLAYER_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "rm -f ${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum ${VMPLAYER_IMAGE} > ${VMPLAYER_IMAGE}.md5
chmod 644 ${VMPLAYER_IMAGE}*
"
}

_virtualbox_image () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
guestfish add /tmp/build-APP_ID/master.qcow2 : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App ${UCS_VERSION} Appliance ${APP_ID} \(VirtualBox\)\'\"
test -e ${TMP_VBOX_IMAGE} && rm ${TMP_VBOX_IMAGE} || true
generate_appliance -m $MEMORY -p UCS -v ${UCS_VERSION}-with-${APP_ID} -o --ova-virtualbox -s $TMP_KVM_IMAGE -f Univention-App-${APP_ID}
"
	_scp ${KVM_USER}@${IMAGE_CONVERT_SERVER}:${VBOX_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${VBOX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "rm -f ${VBOX_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum ${VBOX_IMAGE} > ${VBOX_IMAGE}.md5
chmod 644  ${VBOX_IMAGE}*
"
}

_esxi () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
guestfish add /tmp/build-APP_ID/master.qcow2 : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify=\'Univention App ${UCS_VERSION} Appliance ${APP_ID} \(ESX\)\'\"
test -e ${TMP_ESX_IMAGE} && rm ${TMP_ESX_IMAGE} || true
generate_appliance -m $MEMORY -p UCS -v ${UCS_VERSION}-with-${APP_ID} -o --ova-esxi -s $TMP_KVM_IMAGE -f Univention-App-${APP_ID}
"
	_scp ${KVM_USER}@${IMAGE_CONVERT_SERVER}:${ESX_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${ESX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "rm -f ${ESX_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd $APPS_BASE;
md5sum ${ESX_IMAGE} > ${ESX_IMAGE}.md5
chmod 644  ${ESX_IMAGE}*
"
}

_get_memory () {
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "
virt-cat -a ${TMP_KVM_IMAGE} /.memory 2>/dev/null || echo 1024
"
}

create_app_images () {
	# convert image

	_ssh -l "$KVM_USER" "$KVM_BUILD_SERVER" "
test -d $TMPDIR && rm -rf $TMPDIR
mkdir -p $TMPDIR
qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE
"
	# copy to image convert server for later steps
	_scp -r ${KVM_USER}@${KVM_BUILD_SERVER}:/${TMPDIR} ${KVM_USER}@${IMAGE_CONVERT_SERVER}:/tmp
	_ssh -l "$KVM_USER" "${KVM_BUILD_SERVER}" "rm -rf ${TMPDIR}"

	# create apps dir
	_ssh -l "$KVM_USER" "$APPS_SERVER" "mkdir -p $APPS_BASE"

	# get memory specification (is saved in /tmp/.memory in image)
	export MEMORY=$(_get_memory)
	_kvm_image
	_vmplayer_image
	_virtualbox_image
	_esxi
	_ssh -l "$KVM_USER" "${IMAGE_CONVERT_SERVER}" "rm -rf ${TMPDIR}"
}
