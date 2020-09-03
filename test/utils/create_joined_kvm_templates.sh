#!/bin/bash

set -x
set -e


export REPLACE=true
export SHUTDOWN=true
export KVM_USER="${KVM_USER:=$USER}"
test "$USER" = "jenkins" && export KVM_USER='build'
export HALT=false


mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}

# create the machines
./utils/start-test.sh scenarios/appliances/joined-kvm-templates.cfg


templatedir="/mnt/omar/vmwares/kvm/single/Others"
tmpdir="/mnt/omar/vmwares/kvm/tmp/joined-templates"

die () {
    echo "$exe: $*" >&2
    exit 1
}

cleanup () {
	for role in master backup slave member; do
		local instance="${KVM_USER}_${role}-joined-templates"
		mssh "ucs-kt-remove $instance" || true
	done
	mssh "rm -rf $tmpdir"
}

trap cleanup EXIT

# convert the images
mssh "mkdir /mnt/omar/vmwares/kvm/tmp/joined-templates || true"
for role in master backup slave member; do
	qcowimage=/var/lib/libvirt/images/${KVM_USER}_${role}-joined-templates.qcow2
	instance="${KVM_USER}_${role}-joined-templates"
	mssh "qemu-img convert -p -c -O qcow2 $qcowimage  $tmpdir/$role.qcow2"
	# remove instanc
	mssh "ucs-kt-remove $instance"
done

# get name
qcowimage="$tmpdir/master.qcow2"
version=$(mssh "guestfish add $qcowimage : run : mount /dev/vg_ucs/root / : command '/usr/sbin/ucr get version/version'")
patchlevel=$(mssh "guestfish add $qcowimage : run : mount /dev/vg_ucs/root / : command '/usr/sbin/ucr get version/patchlevel'")
erratalevel=$(mssh "guestfish add $qcowimage : run : mount /dev/vg_ucs/root / : command '/usr/sbin/ucr get version/erratalevel'")
v="${version}-${patchlevel}+e${erratalevel}"

for role in master backup slave member; do
	name="${v}_ucs-joined-$role"
	archive="${name}_amd64.tar.gz"
	hd="${name}-0.qcow2"
	xmlfile="${name}.xml"
	mssh "mv $tmpdir/$role.qcow2 $tmpdir/$hd"
	xml=$(NAME=$name QCOW_FILENAME=$hd envsubst < ./utils/kvm_template.xml)
	mssh "echo '$xml' > $tmpdir/$xmlfile"
	mssh "cd $tmpdir && tar -cvzf $archive $hd $xmlfile"
	mssh "ls $templatedir/$archive" && die "template $archive already exists"
	mssh "mv $tmpdir/$archive $templatedir/$archive"
done

exit 0
