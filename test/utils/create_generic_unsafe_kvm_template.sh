#!/bin/bash

set -e -u -x

env

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}

[ -n "${UCS_VERSION:-}" ] ||
	die "Missing variable '$UCS_VERSION'"
[ -n "${KVM_BUILD_SERVER:-}" ] ||
	die "Missing variable '$KVM_BUILD_SERVER'"

[ "${KVM_USER:=$USER}" = "jenkins" ] &&
	KVM_USER="build"

mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}


mssh '
set -e -u -x

TEMPLATE_SRC="/mnt/omar/vmwares/kvm/ucs-appliance/UCS-'$UCS_VERSION'-KVM-Image.qcow2"
TEMPLATE_BUILD="/var/univention/buildsystem2/temp/build-kt-get-template"
TEMPLATE_TARGET="/mnt/omar/vmwares/kvm/single/UCS/"

mkdir -p "$TEMPLATE_BUILD"

rm -f "$TEMPLATE_BUILD/"*_generic-unsafe.xml
rm -f "$TEMPLATE_BUILD/"*_generic-unsafe-0.qcow2
rm -f "$TEMPLATE_BUILD/"*_amd64.tar.gz

cp "$TEMPLATE_SRC" "$TEMPLATE_BUILD/image.qcow2"

version="$(guestfish add "$TEMPLATE_BUILD/image.qcow2" : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/version")"
patchlevel="$(guestfish add "$TEMPLATE_BUILD/image.qcow2" : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/patchlevel")"
erratalevel="$(guestfish add "$TEMPLATE_BUILD/image.qcow2" : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/erratalevel")"

name="${version}-${patchlevel}+e${erratalevel}_generic-unsafe"
archive="${name}_amd64.tar.gz"
hd="${name}-0.qcow2"
xml="${name}.xml"

if [ -e "$TEMPLATE_TARGET/$archive" ]; then
	echo "template already exists, aborting ..."
	rm "$TEMPLATE_BUILD/image.qcow2"
	exit 1
fi

guestfish add "$TEMPLATE_BUILD/image.qcow2" : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr set repository/online/server=updates.knut.univention.de nameserver1=192.168.0.3"
mv "$TEMPLATE_BUILD/image.qcow2" "$TEMPLATE_BUILD/$hd"

# create xml
cat << EOF > "$TEMPLATE_BUILD/${xml}"
<?xml version="1.0" ?><domain type="kvm">
  <name>${name}</name>
  <memory unit="GiB">2</memory>
  <vcpu placement="static">1</vcpu>
  <os>
    <type arch="x86_64" machine="pc">hvm</type>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode="host-model">
    <model fallback="allow"/>
  </cpu>
  <clock offset="utc"/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/kvm</emulator>
    <disk device="disk" type="file">
      <driver cache="unsafe" name="qemu" type="qcow2"/>
      <source file="${hd}"/>
      <target bus="virtio" dev="vda"/>
    </disk>
    <controller index="0" type="ide"/>
    <controller index="0" model="piix3-uhci" type="usb"/>
    <controller index="0" model="pci-root" type="pci"/>
    <console type="pty"/>
    <channel type="unix">
      <source mode="bind"/>
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    <interface type="bridge">
      <source bridge="eth0"/>
      <model type="virtio"/>
    </interface>
    <input bus="usb" type="tablet"/>
    <input bus="ps2" type="mouse"/>
    <input bus="ps2" type="keyboard"/>
    <graphics autoport="yes" keymap="de" listen="0.0.0.0" port="-1" type="vnc">
      <listen address="0.0.0.0" type="address"/>
    </graphics>
    <video>
      <model heads="1" primary="yes" type="vga" vram="16384"/>
    </video>
    <rng model="virtio">
      <backend model="random">/dev/urandom</backend>
    </rng>
    <memballoon model="virtio"/>
  </devices>
</domain>
EOF

# build template and clean up
exec tar -c -v -z -f "$TEMPLATE_TARGET/$archive" -C "$TEMPLATE_BUILD" --remove-files "$hd" "$xml"
'

exit  0
