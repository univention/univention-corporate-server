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

set -x
set -e

_ssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o BatchMode=yes -n "$@"
}


_scp () {
	scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "$@"
}


_kvm_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.kv"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.kv"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.kv : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\""
	_scp ${KVM_USER}@${IMAGE_SERVER}:${TMP_KVM_IMAGE}.kv ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/$KVM_IMAGE"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "cd $APPS_BASE && md5sum ${KVM_IMAGE} > ${KVM_IMAGE}.md5 && chmod 644 ${KVM_IMAGE}*"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.kv"
}


_vmplayer_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.vm"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.vm"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.vm : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\""
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --vmware -s ${TMP_KVM_IMAGE}.vm -f ${VMPLAYER_IMAGE%-*}"
	_scp ${KVM_USER}@${IMAGE_SERVER}:${VMPLAYER_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "cd $APPS_BASE && md5sum ${VMPLAYER_IMAGE} > ${VMPLAYER_IMAGE}.md5 && chmod 644 ${VMPLAYER_IMAGE}*"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${VMPLAYER_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.vm"
}


_virtualbox_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.vb"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${VBOX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.vb"
	_scp utils/install-vbox-guesttools.sh ${KVM_USER}@${IMAGE_SERVER}:
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.vb : set-network true : run : mount /dev/mapper/vg_ucs-root /  : copy-in install-vbox-guesttools.sh /root/ : command /root/install-vbox-guesttools.sh"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.vb : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\""
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --ova-virtualbox -s ${TMP_KVM_IMAGE}.vb -f ${VBOX_IMAGE%-*}"
	_scp ${KVM_USER}@${IMAGE_SERVER}:${VBOX_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${VBOX_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "cd $APPS_BASE && md5sum ${VBOX_IMAGE} > ${VBOX_IMAGE}.md5 && chmod 644  ${VBOX_IMAGE}*"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${VBOX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.vb"
}


_esxi () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.es"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${ESX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.es"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.es : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\""
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --ova-esxi -s ${TMP_KVM_IMAGE}.es -f ${ESX_IMAGE%-*}"
	_scp ${KVM_USER}@${IMAGE_SERVER}:${ESX_IMAGE} ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${ESX_IMAGE}"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "cd $APPS_BASE && md5sum ${ESX_IMAGE} > ${ESX_IMAGE}.md5 && chmod 644  ${ESX_IMAGE}*"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${ESX_IMAGE}"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.es"
}


_hyperv_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.hv"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${HYPERV_IMAGE_BASE}.vhdx ${HYPERV_IMAGE_BASE}.zip"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.hv"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "guestfish add ${TMP_KVM_IMAGE}.hv : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\""
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "qemu-img convert -p -o subformat=dynamic -O vhdx ${TMP_KVM_IMAGE}.hv ${HYPERV_IMAGE_BASE}.vhdx"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "zip ${HYPERV_IMAGE_BASE}.zip ${HYPERV_IMAGE_BASE}.vhdx"
	_scp ${KVM_USER}@${IMAGE_SERVER}:${HYPERV_IMAGE_BASE}.zip ${KVM_USER}@${APPS_SERVER}:"$APPS_BASE/${HYPERV_IMAGE_BASE}.zip"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "cd $APPS_BASE && md5sum ${HYPERV_IMAGE_BASE}.zip > ${HYPERV_IMAGE_BASE}.zip.md5 && chmod 644 ${HYPERV_IMAGE_BASE}*"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${HYPERV_IMAGE_BASE}.vhdx ${HYPERV_IMAGE_BASE}.zip"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -f ${TMP_KVM_IMAGE}.hv"
}


_ec2_image () {
	# Identifier already set
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "generate_appliance --only --ec2-ebs -s $TMP_KVM_IMAGE"
}

_set_global_vars () {
	APP_ID=$1
	KVM_USER=$2
	KVM_SERVER=$3
	UCS_VERSION=$4

	KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_app-appliance-${APP_ID}.qcow2"
	APPS_BASE="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}"
	APPS_SERVER="omar.knut.univention.de"
	IMAGE_SERVER="docker.knut.univention.de"
	TMP_DIR="/tmp/build-${APP_ID}"
	TMP_KVM_IMAGE="$TMP_DIR/master.qcow2"
	IMAGE_VERSION="${UCS_VERSION}-with-${APP_ID}"
	VMPLAYER_IMAGE="Univention-App-${APP_ID}-vmware.zip"
	KVM_IMAGE="Univention-App-${APP_ID}-KVM.qcow2"
	VBOX_IMAGE="Univention-App-${APP_ID}-virtualbox.ova"
	ESX_IMAGE="Univention-App-${APP_ID}-ESX.ova"
	HYPERV_IMAGE_BASE="Univention-App-${APP_ID}-Hyper-V"

	export APP_ID KVM_USER KVM_SERVER UCS_VERSION KT_CREATE_IMAGE APPS_BASE APPS_SERVER IMAGE_SERVER
	export TMP_DIR VMPLAYER_IMAGE KVM_IMAGE TMP_KVM_IMAGE VBOX_IMAGE ESX_IMAGE IMAGE_VERSION
}

create_app_images () {
	_set_global_vars "$@"

	# convert image
	_ssh -l "$KVM_USER" "$KVM_SERVER" "test -d $TMP_DIR && rm -rf $TMP_DIR || true"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "mkdir -p $TMP_DIR"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE"

	# copy to image convert server for later steps and remove tmp image from kvm server
	_scp -r ${KVM_USER}@${KVM_SERVER}:/${TMP_DIR} ${KVM_USER}@${IMAGE_SERVER}:/tmp
	_ssh -l "$KVM_USER" "${KVM_SERVER}" "rm -rf ${TMP_DIR}"

	# create apps dir
	_ssh -l "$KVM_USER" "$APPS_SERVER" "mkdir -p $APPS_BASE"

	# get memory specification (is saved in /tmp/.memory in image)
	export MEMORY=$(_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "virt-cat -a ${TMP_KVM_IMAGE} /.memory 2>/dev/null || echo 1024")

	_kvm_image "Univention App ${UCS_VERSION} Appliance ${APP_ID} (KVM)"
	_vmplayer_image "Univention App ${UCS_VERSION} Appliance ${APP_ID} (VMware)"
	_esxi "Univention App ${UCS_VERSION} Appliance ${APP_ID} (ESX)"
	_virtualbox_image "Univention App ${UCS_VERSION} Appliance ${APP_ID} (VirtualBox)"

	# cleanup
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -rf ${TMP_DIR}"

	# update current link and sync test mirror
	_ssh -l "$KVM_USER" "$APPS_SERVER" "
cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/current/
test -L ${APP_ID} && rm ${APP_ID}
ln -s ../${UCS_VERSION}/${APP_ID} ${APP_ID}
"
	_ssh -l "$KVM_USER" "$APPS_SERVER" "sudo update_mirror.sh -v appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID} appcenter.test/univention-apps/current/${APP_ID}"

}

create_ucs_images () {

	UPDATER_ID="$1"
	KVM_USER="$2"
	KVM_SERVER="$3"
	UCS_VERSION="$4"

	KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_master-ucs-appliance.qcow2"
	APPS_SERVER="omar.knut.univention.de"
	IMAGE_SERVER="docker.knut.univention.de"
	TMP_DIR="/tmp/build-ucs-appliance"
	TMP_KVM_IMAGE="$TMP_DIR/master.qcow2"
	APPS_BASE="/var/univention/buildsystem2/temp/build/appliance/"
	MEMORY=1536
	IMAGE_VERSION="${UCS_VERSION}"
	VMPLAYER_IMAGE="UCS-Demo-Image-vmware.zip"
	KVM_IMAGE="UCS-Demo-Image-KVM.qcow2"
	VBOX_IMAGE="UCS-Demo-Image-virtualbox.ova"
	ESX_IMAGE="UCS-Demo-Image-ESX.ova"
	HYPERV_IMAGE_BASE="UCS-Demo-Image-Hyper-V"

    export APP_ID KVM_USER KVM_SERVER UCS_VERSION KT_CREATE_IMAGE APPS_BASE APPS_SERVER IMAGE_SERVER
    export TMP_DIR VMPLAYER_IMAGE KVM_IMAGE TMP_KVM_IMAGE VBOX_IMAGE ESX_IMAGE MEMORY IMAGE_VERSION

	# convert image
	_ssh -l "$KVM_USER" "$KVM_SERVER" "test -d $TMP_DIR && rm -rf $TMP_DIR || true"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "mkdir -p $TMP_DIR"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE"

	# copy to image convert server for later steps and remove tmp image from kvm server
	_ssh -l "$KVM_USER" "$IMAGE_SERVER" "test -d $TMP_DIR && rm -rf $TMP_DIR || true"
	_ssh -l "$KVM_USER" "$IMAGE_SERVER" "mkdir -p $TMP_DIR"
	_scp -r ${KVM_USER}@${KVM_SERVER}:/${TMP_KVM_IMAGE} ${KVM_USER}@${IMAGE_SERVER}:${TMP_DIR}
	_ssh -l "$KVM_USER" "${KVM_SERVER}" "rm -rf ${TMP_DIR}"

	# create apps dir
	_ssh -l "$KVM_USER" "$APPS_SERVER" "mkdir -p $APPS_BASE"

	_kvm_image "$UPDATER_ID (KVM)"
	_vmplayer_image "$UPDATER_ID (VMware)"
	_esxi "$UPDATER_ID (ESX)"
	_virtualbox_image "$UPDATER_ID (VirtualBox)"
	_hyperv_image "$UPDATER_ID (HyperV)"

	# cleanup
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -rf ${TMP_DIR}"

}

create_ec2_image () {
	_set_global_vars "$@"
	KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_${APP_ID}.qcow2"

	# convert image
	_ssh -l "$KVM_USER" "$KVM_SERVER" "test -d $TMP_DIR && rm -rf $TMP_DIR || true"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "mkdir -p $TMP_DIR"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE"

	# copy to image convert server for later steps and remove tmp image from kvm server
	_scp -r ${KVM_USER}@${KVM_SERVER}:/${TMP_DIR} ${KVM_USER}@${IMAGE_SERVER}:/tmp
	_ssh -l "$KVM_USER" "${KVM_SERVER}" "rm -rf ${TMP_DIR}"

	_ec2_image

	# cleanup
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "rm -rf ${TMP_DIR}"
}
