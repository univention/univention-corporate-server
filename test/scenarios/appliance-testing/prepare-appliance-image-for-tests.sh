#!/bin/bash

set -x
set -e

export APP_ID="$APP_ID"
export KVM_SERVER="${KVM_SERVER:=$KVM_BUILD_SERVER}"
export KVM_USER="${KVM_USER:=build}"
export UCS_VERSION="$UCS_VERSION"

_ssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_SERVER" "$@"
}

# update the appliance image on the kvm server and exit
appliance_template="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps/$UCS_VERSION/$APP_ID/Univention-App-${APP_ID}-KVM.qcow2"
template_name="$(basename $appliance_template)"
kvm_template_dir="/var/lib/libvirt/templates/single/Others/appliance_${APP_ID}_amd64/"
kvm_template="$kvm_template_dir/$template_name"
kvm_xml="$kvm_template_dir/appliance_${APP_ID}_amd.xml"
xml_template="/mnt/omar/vmwares/kvm/single/Others/appliance_template.xml"
# check disk space
stat=$(_ssh stat -f -c '%a*%S' /var/lib/libvirt)
if [ "$((${stat}>>30))" -lt 20 ]; then
	echo "ERROR: Not enough Space on $KVM_SERVER! Aborting..."
	exit 1
fi

# check if update is necessary
appliance_md5=$(_ssh cat "$appliance_template.md5" || true)
kvm_md5=$(_ssh cat "$kvm_template.md5" || true)
if [ "$appliance_md5" = "$kvm_md5" ]; then
	exit 0
fi

# check if instances still running appliance-test-digitec-suitecrm
existing_instances=$(_ssh virsh  list --all| grep appliance-test-$APP_ID || true)
if [ -n "$existing_instances" ]; then
	echo "ERROR: existing instances on $KVM_SERVER ($existing_instances)! Aborting ..."
	exit 1
fi

# copy image
_ssh mkdir -p "$kvm_template_dir"
_ssh cp "$appliance_template" "$kvm_template"

# create xml
_ssh "APP='$APP_ID' envsubst <'$xml_template' >'$kvm_xml'"

# prepare image
_ssh "guestfish add $kvm_template  : run : mount /dev/mapper/vg_ucs-root / : \
	command 'ucr unset --force auth/sshd/user/root' : \
	command 'ucr set umc/module/debug/level=4 umc/server/debug/level=4' : \
	command 'ucr set interfaces/eth1/type=dhcp' : \
	mkdir-p /root/.ssh/ : \
	write /root/.ssh/authorized_keys 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKxi4dwmF9K7gV4JbQUmQ4ufRHcxYOYUHWoIRuj8jLmP1hMOqEmZ43rSRoe2E3xTNg+RAjwkX1GQmWQzzjRIYRpUfwLo+yEXtER1DCDTupLPAT5ulL6uPd5mK965vbE46g50LHRyTGZTbsh1A/NPD7+LNBvgm5dTo/KtMlvJHWDN0u4Fwix2uQfvCSOpF1n0tDh0b+rr01orITJcjuezIbZsArTszA+VVJpoMyvu/I3VQVDSoHB+7bKTPwPQz6OehBrFNZIp4zl18eAXafDoutTXSOUyiXcrViuKukRmvPAaO8u3+r+OAO82xUSQZgIWQgtsja8vsiQHtN+EtR8mIn tech'"

_ssh "chmod g+w -R $kvm_template_dir"

# fake uvmm template
_ssh touch /mnt/omar/vmwares/kvm/single/Others/appliance_${APP_ID}_amd64.tar.gz

_ssh cp "$appliance_template.md5" "$kvm_template.md5"

exit 0
