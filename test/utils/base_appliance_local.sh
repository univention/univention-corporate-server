#!/bin/bash
#
# Copyright 2018 Univention GmbH
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
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "
		set -e -x
		cd $APPS_BASE
		rm -f ${TMP_KVM_IMAGE}.kv $KVM_IMAGE
		cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.kv
		guestfish add ${TMP_KVM_IMAGE}.kv : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		cp -f ${TMP_KVM_IMAGE}.kv $KVM_IMAGE
		md5sum ${KVM_IMAGE} > ${KVM_IMAGE}.md5
		sha256sum ${KVM_IMAGE} > ${KVM_IMAGE}.sha256
		chmod 644 ${KVM_IMAGE}*
		rm -f ${TMP_KVM_IMAGE}.kv
	"
}


_vmplayer_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "
		set -e -x
		cd $APPS_BASE
		rm -f ${TMP_KVM_IMAGE}.vm ${VMPLAYER_IMAGE}
		cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.vm
		guestfish add ${TMP_KVM_IMAGE}.vm : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --vmware -s ${TMP_KVM_IMAGE}.vm -f ${VMPLAYER_IMAGE}
		md5sum ${VMPLAYER_IMAGE} > ${VMPLAYER_IMAGE}.md5
		sha256sum ${VMPLAYER_IMAGE} > ${VMPLAYER_IMAGE}.sha256
		chmod 644 ${VMPLAYER_IMAGE}*
		rm -f ${TMP_KVM_IMAGE}.vm
	"
}


_virtualbox_image () {
	local identify="$1"
	_scp utils/install-vbox-guesttools.sh ${KVM_USER}@${IMAGE_SERVER}:/tmp
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "
		set -e -x
		cd $APPS_BASE
		rm -f ${TMP_KVM_IMAGE}.vb ${VBOX_IMAGE}
		cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.vb
		guestfish add ${TMP_KVM_IMAGE}.vb : set-network true : run : mount /dev/mapper/vg_ucs-root /  : copy-in /tmp/install-vbox-guesttools.sh /root/ : command /root/install-vbox-guesttools.sh
		guestfish add ${TMP_KVM_IMAGE}.vb : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --ova-virtualbox -s ${TMP_KVM_IMAGE}.vb -f ${VBOX_IMAGE}
		md5sum ${VBOX_IMAGE} > ${VBOX_IMAGE}.md5
		sha256sum ${VBOX_IMAGE} > ${VBOX_IMAGE}.sha256
		chmod 644  ${VBOX_IMAGE}*
		rm -f ${TMP_KVM_IMAGE}.vb
	"
}


_esxi () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "
		set -e -x
		cd $APPS_BASE
		rm -f ${TMP_KVM_IMAGE}.es ${ESX_IMAGE}
		cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.es
		guestfish add ${TMP_KVM_IMAGE}.es : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m $MEMORY -p UCS -v $IMAGE_VERSION -o --ova-esxi -s ${TMP_KVM_IMAGE}.es -f ${ESX_IMAGE}
		md5sum ${ESX_IMAGE} > ${ESX_IMAGE}.md5
		sha256sum ${ESX_IMAGE} > ${ESX_IMAGE}.sha256
		chmod 644  ${ESX_IMAGE}*
		rm -f ${TMP_KVM_IMAGE}.es
	"
}


_hyperv_image () {
	local identify="$1"
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "
		set -e -x
		cd $APPS_BASE
		rm -f ${TMP_KVM_IMAGE}.hv ${HYPERV_IMAGE_BASE}.vhdx ${HYPERV_IMAGE_BASE}.zip
		cp ${TMP_KVM_IMAGE} ${TMP_KVM_IMAGE}.hv
		guestfish add ${TMP_KVM_IMAGE}.hv : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		qemu-img convert -p -o subformat=dynamic -O vhdx ${TMP_KVM_IMAGE}.hv ${HYPERV_IMAGE_BASE}.vhdx
		zip ${HYPERV_IMAGE_BASE}.zip ${HYPERV_IMAGE_BASE}.vhdx
		md5sum ${HYPERV_IMAGE_BASE}.zip > ${HYPERV_IMAGE_BASE}.zip.md5
		sha256sum ${HYPERV_IMAGE_BASE}.zip > ${HYPERV_IMAGE_BASE}.zip.sha256
		chmod 644 ${HYPERV_IMAGE_BASE}*
		rm -f ${TMP_KVM_IMAGE}.hv ${HYPERV_IMAGE_BASE}.vhdx
	"
}


_ec2_image () {
	# Identifier already set
	_ssh -l "$KVM_USER" "${IMAGE_SERVER}" "generate_appliance --only --ec2-ebs -s /tmp/master-ec2-appliance/master.qcow2 -v '${UCS_VERSION_INFO}'"
}

_set_global_vars () {
	APP_ID=$1
	KVM_USER=$2
	KVM_SERVER=$3
	UCS_VERSION=$4
	UCS_VERSION_INFO="$5"

	KT_CREATE_IMAGE="/var/lib/libvirt/images/${KVM_USER}_app-appliance-${APP_ID}.qcow2"
	APPS_BASE="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}"
	APPS_SERVER="omar.knut.univention.de"
	IMAGE_SERVER="docker.knut.univention.de"
	TMP_DIR="/var/univention/buildsystem2/temp/build-app-appliance/${APP_ID}"
	TMP_KVM_IMAGE="$TMP_DIR/master.qcow2"
	IMAGE_VERSION="${UCS_VERSION}-with-${APP_ID}"
	VMPLAYER_IMAGE="Univention-App-${APP_ID}-vmware.zip"
	KVM_IMAGE="Univention-App-${APP_ID}-KVM.qcow2"
	VBOX_IMAGE="Univention-App-${APP_ID}-virtualbox.ova"
	ESX_IMAGE="Univention-App-${APP_ID}-ESX.ova"
	HYPERV_IMAGE_BASE="Univention-App-${APP_ID}-Hyper-V"

	export APP_ID KVM_USER KVM_SERVER UCS_VERSION UCS_VERSION_INFO KT_CREATE_IMAGE APPS_BASE APPS_SERVER IMAGE_SERVER
	export TMP_DIR VMPLAYER_IMAGE KVM_IMAGE TMP_KVM_IMAGE VBOX_IMAGE ESX_IMAGE IMAGE_VERSION
}

create_app_images () {
	_set_global_vars "$@"

	# convert image
	_ssh -l "$KVM_USER" "$KVM_SERVER" "
		set -e -x
		test -d $TMP_DIR && rm -rf $TMP_DIR || true
		mkdir -p $TMP_DIR
		mkdir -p $APPS_BASE
		qemu-img convert -p -c -O qcow2 $KT_CREATE_IMAGE $TMP_KVM_IMAGE
	"

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
		set -e -x
		cd /var/univention/buildsystem2/mirror/appcenter.test/univention-apps/current/
		test -L ${APP_ID} && rm ${APP_ID}
		ln -s ../${UCS_VERSION}/${APP_ID} ${APP_ID}
		sudo update_mirror.sh -v appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID} appcenter.test/univention-apps/current/${APP_ID}
	"

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
	MEMORY=2048
	IMAGE_VERSION="${UCS_VERSION}"
	VMPLAYER_IMAGE="UCS-VMware-Image.zip"
	KVM_IMAGE="UCS-KVM-Image.qcow2"
	VBOX_IMAGE="UCS-Virtualbox-Image.ova"
	ESX_IMAGE="UCS-VMware-ESX-Image.ova"
	HYPERV_IMAGE_BASE="UCS-Hyper-V-Image"

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

create_internal_template () {
	SERVERROLE=$1
	KVM_USER=$2
	KVM_SERVER=$3
	UCS_VERSION=$4
	UCS_VERSION_INFO="$5"
	QCOW_PATH="/var/lib/libvirt/images/${KVM_USER}_${SERVERROLE}.qcow2"
	TMP_DIR="/var/univention/buildsystem2/temp/build-branch-test-template"
	KVM_SERVER_LOCAL_TMP_IMAGE="${SERVERROLE}-${UCS_VERSION}.qcow2"
	KVM_TEMPLATE_NAME="${UCS_VERSION}+${UCS_VERSION_INFO}_${SERVERROLE}-joined_amd64.tar.gz"
	KVM_TEMPLATE_TGZ_PATH="${TMP_DIR}/${KVM_TEMPLATE_NAME}"
	NAME="${UCS_VERSION}+${UCS_VERSION_INFO}_${SERVERROLE}-joined"

	_ssh -l "$KVM_USER" "$KVM_SERVER" "test -d $TMP_DIR && rm -rf $TMP_DIR || true"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "mkdir -p $TMP_DIR"
	_ssh -l "$KVM_USER" "$KVM_SERVER" "qemu-img convert -p -c -O qcow2 $QCOW_PATH $TMP_DIR/$KVM_SERVER_LOCAL_TMP_IMAGE"
	#test _ssh -l "$KVM_USER" "$KVM_SERVER" "cp $QCOW_PATH $TMP_DIR/$KVM_SERVER_LOCAL_TMP_IMAGE"

	_scp utils/kvm_template.xml ${KVM_USER}@${KVM_SERVER}:"$TMP_DIR"
	ssh -l "$KVM_USER" "$KVM_SERVER" "QCOW_FILENAME=$KVM_SERVER_LOCAL_TMP_IMAGE NAME=$NAME envsubst <'$TMP_DIR/kvm_template.xml' >'$TMP_DIR/${SERVERROLE}-${UCS_VERSION}.xml'"
	ssh -l "$KVM_USER" "$KVM_SERVER" "rm $TMP_DIR/kvm_template.xml"

	_ssh -l "$KVM_USER" "$KVM_SERVER" "cd ${TMP_DIR} && tar czvf ${KVM_TEMPLATE_TGZ_PATH} *"

	# copy to template directory, cleanup kvm server
	_ssh -l "$KVM_USER" "$KVM_SERVER" "cp ${KVM_TEMPLATE_TGZ_PATH} /mnt/omar/vmwares/kvm/single/Others/"
	_ssh -l "$KVM_USER" "${KVM_SERVER}" "rm -rf ${TMP_DIR}"

}
