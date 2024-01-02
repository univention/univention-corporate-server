#!/bin/bash
# SPDX-FileCopyrightText: 2018-2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e -u -x

[ -n "${KVM_BUILD_SERVER:-}" ] &&
	exec ssh -o BatchMode=yes "build@${KVM_BUILD_SERVER:?}" "APP_ID='${APP_ID:?}' UCS_VERSION='${UCS_VERSION:?}' bash -s" <"$0"

die () {
	echo "ERROR: $*" >&2
	exit 1
}

# update the image on the kvm server and exit
src_template="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}/Univention-App-${APP_ID}-KVM.qcow2"
kvm_template_dir="/var/lib/libvirt/templates/single/Others/appliance_${APP_ID}_amd64/"
kvm_template="$kvm_template_dir/${src_template##*/}"

install -m 2775 -d "$kvm_template_dir"

# check disk space
stat=$(stat -f -c '%a*%S' /var/lib/libvirt)
[ "$((stat>>30))" -ge 20 ] ||
	die "Not enough Space on $HOSTNAME! Aborting..."

# check if update is necessary
appliance_md5=$(cat "$src_template.md5")
kvm_md5=$(cat "$kvm_template.md5" || true)
if [ "$appliance_md5" != "$kvm_md5" ]; then
	install -m 0664 "$src_template" "$kvm_template"
	install -m 0664 "$src_template.md5" "$kvm_template.md5"
else
	exit 0
fi

APP="${APP_ID:?}" envsubst <'/mnt/omar/vmwares/kvm/single/Others/appliance_template.xml' >"$kvm_template_dir/appliance_${APP_ID}_amd.xml"

# fake Qemu/KVM template
touch "/mnt/omar/vmwares/kvm/single/Others/appliance_${APP_ID}_amd64.tar.gz"

# re-allow ssh login for user `root` via key `tech`
declare -a cmd=(
	add "$kvm_template" :
	run :
	mount /dev/mapper/vg_ucs-root / :
	command 'ucr unset --force auth/sshd/user/root' :
	command 'ucr set umc/module/debug/level=4 umc/server/debug/level=4' :
	command 'ucr set interfaces/eth1/type=dhcp' :
	mkdir-p /root/.ssh/ :
	write /root/.ssh/authorized_keys 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKxi4dwmF9K7gV4JbQUmQ4ufRHcxYOYUHWoIRuj8jLmP1hMOqEmZ43rSRoe2E3xTNg+RAjwkX1GQmWQzzjRIYRpUfwLo+yEXtER1DCDTupLPAT5ulL6uPd5mK965vbE46g50LHRyTGZTbsh1A/NPD7+LNBvgm5dTo/KtMlvJHWDN0u4Fwix2uQfvCSOpF1n0tDh0b+rr01orITJcjuezIbZsArTszA+VVJpoMyvu/I3VQVDSoHB+7bKTPwPQz6OehBrFNZIp4zl18eAXafDoutTXSOUyiXcrViuKukRmvPAaO8u3+r+OAO82xUSQZgIWQgtsja8vsiQHtN+EtR8mIn tech' :
)
guestfish "${cmd[@]}"

exit 0
