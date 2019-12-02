#!/bin/bash

set -x
set -e

export KVM_SERVER="$KVM_BUILD_SERVER"
export KVM_USER="$KVM_USER"

_ssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_SERVER" "$@"
}

# update the image on the kvm server and exit
ucs_template="/var/univention/buildsystem2/temp/build/appliance/UCS-KVM-Image.qcow2"
kvm_template_dir="/var/lib/libvirt/templates/single/Others/appliance_ucsappliance_amd64/"
template_name="$(basename $ucs_template)"
kvm_template="$kvm_template_dir/$template_name"
xml_template="/mnt/omar/vmwares/kvm/single/Others/ucs_appliance_template.xml"
kvm_xml="$kvm_template_dir/appliance_ucsappliance_amd.xml"

# check disk space
stat=$(_ssh stat -f -c '%a*%S' /var/lib/libvirt)
if [ "$((${stat}>>30))" -lt 20 ]; then
	echo "ERROR: Not enough Space on $KVM_SERVER! Aborting..."
	exit 1
fi

# check if instances still running
existing_instances=$(_ssh virsh  list --all| grep appliance-test-ucs || true)
if [ -n "$existing_instances" ]; then
	echo "ERROR: existing instances on $KVM_SERVER ($existing_instances)! Aborting ..."
	exit 1
fi

## check if template is used as backing file
#_ssh "
#while read image; do
#	if qemu-img info \"\$image\" | grep -i \"backing file\" | grep \"$template_name\"; then
#		echo "ERROR: $template_name is backing file for \$image"
#		exit 1
#	fi
#done < <(ls /var/lib/libvirt/images/*)"

# check if update is necessary
appliance_md5=$(_ssh cat "$ucs_template.md5" || true)
kvm_md5=$(_ssh cat "$kvm_template.md5" || true)
if [ "$appliance_md5" != "$kvm_md5" ]; then
	# copy image
	_ssh mkdir -p "$kvm_template_dir"
	_ssh "chmod g+w -R $kvm_template_dir"
	_ssh cp "$ucs_template" "$kvm_template"
	_ssh cp "$ucs_template.md5" "$kvm_template.md5"
	_ssh "chmod g+w -R $kvm_template_dir"
fi

# cp xml
_ssh mkdir -p "$kvm_template_dir"
_ssh cp "$xml_template" "$kvm_xml"

# fake uvmm template
_ssh touch /mnt/omar/vmwares/kvm/single/Others/appliance_ucsappliance_amd64.tar.gz

# prepare image
_ssh "guestfish add $kvm_template : set-network true : run : mount /dev/mapper/vg_ucs-root / : \
	command 'ucr unset --force auth/sshd/user/root' : \
	command 'ucr set umc/module/debug/level=4 umc/server/debug/level=4' : \
	mkdir-p /root/.ssh/ : \
	write /root/.ssh/authorized_keys 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKxi4dwmF9K7gV4JbQUmQ4ufRHcxYOYUHWoIRuj8jLmP1hMOqEmZ43rSRoe2E3xTNg+RAjwkX1GQmWQzzjRIYRpUfwLo+yEXtER1DCDTupLPAT5ulL6uPd5mK965vbE46g50LHRyTGZTbsh1A/NPD7+LNBvgm5dTo/KtMlvJHWDN0u4Fwix2uQfvCSOpF1n0tDh0b+rr01orITJcjuezIbZsArTszA+VVJpoMyvu/I3VQVDSoHB+7bKTPwPQz6OehBrFNZIp4zl18eAXafDoutTXSOUyiXcrViuKukRmvPAaO8u3+r+OAO82xUSQZgIWQgtsja8vsiQHtN+EtR8mIn tech' : \
"

exit 0
