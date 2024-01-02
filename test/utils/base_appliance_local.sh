#!/bin/bash
# SPDX-FileCopyrightText: 2018-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e -u -x

APPS_SERVER='omar.knut.univention.de'
APPS_BASE='/var/univention/buildsystem2/mirror'
APPS_DIR='appcenter.test/univention-apps'

_wrap () {  # <cmd> <identity> <out>
	local TMP_IMAGE out="${3:?missing output file}"
	TMP_IMAGE="${out}.qcow2"
	[ -n "${LAZY:-}" ] && [ -s "${out:?}" ] && return
	rm -f "${out%.*}"*
	qemu-img create -f qcow2 -b "${SRC_IMAGE}" "${TMP_IMAGE}"
	"$@"
	rm -f "${TMP_IMAGE}"

	[ -s "${out:?}" ]
	md5sum "${out:?}" > "${out:?}.md5"
	sha256sum "${out:?}" > "${out:?}.sha256"
	chmod 644 "${out:?}"*
}

_kvm_image () {
	identify="${1:?} (KVM)"
	guestfish add "${TMP_IMAGE}" : run : mount /dev/mapper/vg_ucs-root / : command "/usr/sbin/ucr set updater/identify='$identify'"
	qemu-img convert -p -c -O qcow2 "${TMP_IMAGE}" "${out}"
}

_vmplayer_image () {
	identify="${1:?} (VMware)"
	guestfish add "${TMP_IMAGE}" : run : mount /dev/mapper/vg_ucs-root / : command "/usr/sbin/ucr set updater/identify='$identify'"
	generate_appliance --tempdir "${APPS_PATH}" --memory "$MEMORY" --product UCS --version "$IMAGE_VERSION" --only --vmware --source "${TMP_IMAGE}" --filename "${out}"
}

_virtualbox_image () {
	identify="${1:?} (VirtualBox)"
	# FIXME: [VirtualBox](https://tracker.debian.org/pkg/virtualbox) has been remove from Debian for [serious security reasons](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=794466)
	local CONF='/etc/X11/xorg.conf.d/use-fbdev-driver.conf'
	local HOOK='/usr/lib/univention-system-setup/appliance-hooks.d/20_remove_xorg_config'
	declare -a cmd=(
		# network true
		add "${TMP_IMAGE}" :
		run :
		mount /dev/mapper/vg_ucs-root / :
		# command "ucr set --force update/secure_apt=no repository/online=yes repository/online/server='https://updates.software-univention.de/'" :
		# command "univention-install -y virtualbox-guest-utils" :
		# command "apt-get clean" :
		# command "ucr unset --force update/secure_apt repository/online repository/online/server" :
		mkdir-p "${CONF%/*}" :
		write "${CONF}" 'Section "Device"
    Identifier "Card0"
    Driver "fbdev"
EndSection
' :
		chmod 0644 "${CONF}" :
		write "${HOOK}" "#!/bin/sh
exec rm -f '$CONF'
" :
		chmod 0755 "${HOOK}" :
		command "/usr/sbin/ucr set updater/identify='$identify'"
	)
	guestfish "${cmd[@]}"
	generate_appliance --tempdir "${APPS_PATH}" --memory "$MEMORY" --product UCS --version "$IMAGE_VERSION" --only --ova-virtualbox --source "${TMP_IMAGE}" --filename "${out}"
}

_esxi () {
	identify="${1:?} (ESX)"
	guestfish add "${TMP_IMAGE}" : run : mount /dev/mapper/vg_ucs-root / : command "/usr/sbin/ucr set updater/identify='$identify'"
	generate_appliance --tempdir "${APPS_PATH}" --memory "$MEMORY" --product UCS --version "$IMAGE_VERSION" --only --ova-esxi --source "${TMP_IMAGE}" --filename "${out}"
}

_hyperv_image () {
	identify="${1:?} (HyperV)"
	guestfish add "${TMP_IMAGE}" : run : mount /dev/mapper/vg_ucs-root / : command "/usr/sbin/ucr set updater/identify='$identify'"
	qemu-img convert -p -O vhdx -o subformat=dynamic "${TMP_IMAGE}" "${out%.zip}.vhdx"
	zip --move --junk-paths "${out}" "${out%.zip}.vhdx"
}

_ec2_image () {
	# Identifier already set
	generate_appliance --tempdir "${APPS_PATH}" --version "${UCS_VERSION_INFO}" --only --ec2-ebs --source "${SRC_IMAGE}"
}

# Used by scenarios/app-appliance.cfg
create_app_images () {
	SRC_IMAGE="${1:?}"
	IMG_ID="${2:?}${3:+-${3}}"
	_setup_dir "${APPS_BASE}/${APPS_DIR}/${UCS_VERSION}/${IMG_ID}"
	IMAGE_VERSION="${UCS_VERSION}-with-${IMG_ID}"
	MEMORY="$(virt-cat -a "${SRC_IMAGE}" /.memory 2>/dev/null || echo 2048)"

	local identifier
	identifier="Univention App ${UCS_VERSION} Appliance $(virt-cat -a "${SRC_IMAGE}" /.identifier 2>/dev/null || echo "$IMG_ID")"

	_wrap _kvm_image        "${identifier}" "Univention-App-${IMG_ID}-KVM.qcow2"
	_wrap _vmplayer_image   "${identifier}" "Univention-App-${IMG_ID}-vmware.zip"
	_wrap _esxi             "${identifier}" "Univention-App-${IMG_ID}-ESX.ova"
	_wrap _virtualbox_image "${identifier}" "Univention-App-${IMG_ID}-virtualbox.ova"

	# update current link and sync test mirror
	ln -snf "../${UCS_VERSION}/${IMG_ID}" "${APPS_BASE}/${APPS_DIR}/current/${IMG_ID}"
	sudo update_mirror.sh -v "${APPS_DIR}/${UCS_VERSION}/${IMG_ID}" "${APPS_DIR}/current/${IMG_ID}"
}

# Used by scenarios/appliances/ucs-appliance.cfg
create_ucs_images () {
	SRC_IMAGE="${1:?}"
	IMG_ID="${2:?}"
	_setup_dir "/var/univention/buildsystem2/temp/build/appliance"
	IMAGE_VERSION="${UCS_VERSION}"
	MEMORY=2048

	_wrap _kvm_image        "${IMG_ID}" "UCS-KVM-Image.qcow2"
	_wrap _vmplayer_image   "${IMG_ID}" "UCS-VMware-Image.zip"
	_wrap _esxi             "${IMG_ID}" "UCS-VMware-ESX-Image.ova"
	_wrap _virtualbox_image "${IMG_ID}" "UCS-Virtualbox-Image.ova"
	_wrap _hyperv_image     "${IMG_ID}" "UCS-Hyper-V-Image.zip"

	echo "## Images available at ${APPS_PATH}"
}

_setup_dir() {
	APPS_PATH="${1:?}"
	install -g buildgroup -m 2775 -d "${APPS_PATH}"
	cd "${APPS_PATH}"
}

# Used by scenarios/appliances/ec2-appliance.cfg
create_ec2_image () {
	SRC_IMAGE="${1:?}"
	IMG_ID="${2:?}"
	UCS_VERSION_INFO="${3?}"
	_setup_dir "/var/univention/buildsystem2/temp/build/appliance"

	_ec2_image
}

case "${HOSTNAME:=$(hostname)}" in
"${APPS_SERVER}"|"${APPS_SERVER%%.*}")
	${1:+"$@"}
	;;
*)
	exec ssh -o BatchMode=yes "$APPS_SERVER" "LAZY='${LAZY:-}' UCS_VERSION='${UCS_VERSION:?}' bash -s ${*@Q}" <"$0"
	;;
esac
