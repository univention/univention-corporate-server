#!/bin/bash

set -e -u -x

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}


export REPLACE=true
export HALT=false
export SHUTDOWN=true

KVM_USER="${KVM_USER:=$USER}"
test "$KVM_USER" = "jenkins" && KVM_USER='build'
export KVM_USER

declare -a ROLES=(master backup slave member)


mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}

# create the machines
./utils/start-test.sh scenarios/appliances/joined-kvm-templates.cfg

templatedir="/mnt/omar/vmwares/kvm/single/Others"
tmpdir="/mnt/omar/vmwares/kvm/tmp/joined-templates"

cleanup () {
	local role instance
	for role in "${ROLES[@]}"
	do
		instance="${KVM_USER}_${role}-joined-templates"
		mssh ucs-kt-remove "$instance" || true
	done
	mssh rm -rf "${tmpdir:?}"
}

trap cleanup EXIT

# convert the images
mssh install -m 2775 -g buildgroup -d "$tmpdir"
for role in "${ROLES[@]}"
do
	qcowimage="/var/lib/libvirt/images/${KVM_USER}_${role}-joined-templates.qcow2"
	instance="${KVM_USER}_${role}-joined-templates"
	mssh qemu-img convert -p -c -O qcow2 "$qcowimage" "$tmpdir/$role.qcow2"
	# remove instanc
	mssh ucs-kt-remove "$instance"
done

# get name
qcowimage="$tmpdir/master.qcow2"
ver="$(guestfish --ro -a "$TEMPLATE_BUILD/image.qcow2" -m /dev/vg_ucs/root -- sh "echo \"@%@version/version@%@-@%@version/patchlevel@%@+e@%@version/erratalevel@%@\"|ucr filter")"

for role in "${ROLES[@]}"
do
	name="${ver}_ucs-joined-$role"
	archive="${name}_amd64.tar.gz"
	hd="${name}-0.qcow2"
	xmlfile="${name}.xml"
	mssh mv "$tmpdir/$role.qcow2" "$tmpdir/$hd"
	xml="$(NAME="$name" QCOW_FILENAME="$hd" envsubst < ./utils/kvm_template.xml)"
	mssh "echo '$xml' > $tmpdir/$xmlfile"
	mssh tar -c -v -z -f "$tmpdir/$archive" -C "$tmpdir" "$hd" "$xmlfile"
	mssh ls "$templatedir/$archive" && die "template $archive already exists"
	mssh mv "$tmpdir/$archive" "$templatedir/$archive"
done

exit 0
