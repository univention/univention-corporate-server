#!/bin/bash

set -x
set -e

env

export UCS_VERSION="${UCS_VERSION}"
export KVM_USER="${KVM_USER:=$USER}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER}"

test "$KVM_USER" = "jenkins" && KVM_USER="build"

if [ -z "${UCS_VERSION}" ]; then
	echo "ERR: missing UCS_VERSION env variable!" >2
	exit 1
fi

if [ -z "${KVM_BUILD_SERVER}" ]; then
	echo "ERR: missing KVM_BUILD_SERVER env variable!" >2
	exit 1
fi


mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}


mssh '

set -x
set -e


TEMPLATE_SRC="/mnt/omar/vmwares/kvm/ucs-appliance/UCS-'$UCS_VERSION'-KVM-Image.qcow2"
TEMPLATE_BUILD="/var/univention/buildsystem2/temp/build-kt-get-template"
TEMPLATE_TARGET="/mnt/omar/vmwares/kvm/single/UCS/"

mkdir -p "$TEMPLATE_BUILD"

rm -f $TEMPLATE_BUILD/*_generic-unsafe.xml
rm -f $TEMPLATE_BUILD/*_generic-unsafe-0.qcow2
rm -f $TEMPLATE_BUILD/*_amd64.tar.gz

cp "$TEMPLATE_SRC" "$TEMPLATE_BUILD/image.qcow2"

version="$(guestfish add $TEMPLATE_BUILD/image.qcow2 : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/version")"
patchlevel="$(guestfish add $TEMPLATE_BUILD/image.qcow2 : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/patchlevel")"
erratalevel="$(guestfish add $TEMPLATE_BUILD/image.qcow2 : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr get version/erratalevel")"

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
  <memory unit="KiB">2097152</memory>
  <currentMemory unit="KiB">2097152</currentMemory>
  <vcpu placement="static">1</vcpu>
  <resource>
    <partition>/machine</partition>
  </resource>
  <os>
    <type arch="x86_64" machine="pc">hvm</type>
    <boot dev="cdrom"/>
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
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x04" type="pci"/>
    </disk>
    <controller index="0" type="ide">
      <address bus="0x00" domain="0x0000" function="0x1" slot="0x01" type="pci"/>
    </controller>
    <controller index="0" model="piix3-uhci" type="usb">
      <address bus="0x00" domain="0x0000" function="0x2" slot="0x01" type="pci"/>
    </controller>
    <controller index="0" model="pci-root" type="pci"/>
    <interface type="bridge">
      <source bridge="eth0"/>
      <model type="virtio"/>
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x03" type="pci"/>
    </interface>
    <input bus="usb" type="tablet">
      <address bus="0" port="1" type="usb"/>
    </input>
    <input bus="ps2" type="mouse"/>
    <input bus="ps2" type="keyboard"/>
    <graphics autoport="yes" keymap="de" listen="0.0.0.0" port="-1" type="vnc">
      <listen address="0.0.0.0" type="address"/>
    </graphics>
    <video>
      <model heads="1" primary="yes" type="cirrus" vram="16384"/>
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x02" type="pci"/>
    </video>
    <memballoon model="virtio">
      <address bus="0x00" domain="0x0000" function="0x0" slot="0x05" type="pci"/>
    </memballoon>
  </devices>
</domain>
EOF

# build template and clean up
cd "$TEMPLATE_BUILD"
tar -cvzf "$archive" "$hd" "$xml"
mv "$TEMPLATE_BUILD/$archive" "$TEMPLATE_TARGET/$archive"
rm -f "$TEMPLATE_BUILD/$hd"
rm -f "$TEMPLATE_BUILD/$xml"

exit 0'

exit  0
