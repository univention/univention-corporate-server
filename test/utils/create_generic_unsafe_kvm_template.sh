#!/bin/bash

set -x
set -e

KVM_USER="$1"
KVM_BUILD_SERVER="$2"
UCS_VERSION="$3"
DEVELOPMENT="$4"

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}

test -z "$UCS_VERSION" && die "ERR: missing UCS_VERSION arg!"
test -z "$KVM_USER" && die "ERR: missing KVM_USER arg!"
test -z "$KVM_BUILD_SERVER" && die "ERR: missing KVM_BUILD_SERVER arg!"
test -z "$DEVELOPMENT" && die "ERR: missing DEVELOPMENT arg!"

test "$KVM_USER" = "jenkins" && KVM_USER="build"


mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}

TEMPLATE_SRC="/var/lib/libvirt/images/${KVM_USER}_master-generic-kvm-template-${UCS_VERSION}.qcow2"
TEMPLATE_BUILD="/var/univention/buildsystem2/temp/build-kt-get-template"
TEMPLATE_TARGET="/mnt/omar/vmwares/kvm/single/UCS/"

mssh "mkdir -p $TEMPLATE_BUILD"
mssh "rm -f $TEMPLATE_BUILD/*_generic-unsafe.xml"
mssh "rm -f $TEMPLATE_BUILD/*_generic-unsafe-0.qcow2"
mssh "rm -f $TEMPLATE_BUILD/*_amd64.tar.gz"

mssh "qemu-img convert -p -c -O qcow2 $TEMPLATE_SRC $TEMPLATE_BUILD/image.qcow2"

if $DEVELOPMENT; then
	name="${UCS_VERSION}+$(date +%Y-%m-%d)_generic-unsafe"
else
	erratalevel=$(mssh "guestfish add $TEMPLATE_BUILD/image.qcow2 : run : mount /dev/vg_ucs/root / : command '/usr/sbin/ucr get version/erratalevel'")
	name="${UCS_VERSION}+e${erratalevel}_generic-unsafe"
fi

archive="${name}_amd64.tar.gz"
hd="${name}-0.qcow2"
xmlfile="${name}.xml"

mssh "ls $TEMPLATE_TARGET/$archive" && die "template $archive already exists"
mssh "mv $TEMPLATE_BUILD/image.qcow2 $TEMPLATE_BUILD/$hd"
xml=$(NAME=$name QCOW_FILENAME=$hd envsubst < ./utils/kvm_template.xml)
mssh "echo '$xml' > $TEMPLATE_BUILD/${xmlfile}"

mssh "cd $TEMPLATE_BUILD && tar -cvzf $archive $hd $xmlfile"
mssh "mv $TEMPLATE_BUILD/$archive $TEMPLATE_TARGET/$archive"
mssh "rm -f $TEMPLATE_BUILD/$hd"
mssh "rm -f $TEMPLATE_BUILD/$xmlfile"

exit 0
