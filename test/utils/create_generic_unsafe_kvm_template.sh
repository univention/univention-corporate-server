#!/bin/sh

set -e -x

die () {
	echo "ERR: $*" >&2
	exit 1
}
have () {
	command -v "$1" >/dev/null 2>&1
}

[ "${KVM_USER:=$USER}" = 'jenkins' ] &&
	KVM_USER='build'

have guestfish ||
	exec ssh -l "${KVM_USER:?}" "${KVM_BUILD_SERVER:?missing}" "UCS_VERSION=${UCS_VERSION:?missing} ${SHELL}" <"$0"

TEMPLATE_SRC="/mnt/omar/vmwares/kvm/ucs-appliance/UCS-${UCS_VERSION:?missing}-KVM-Image.qcow2"
TEMPLATE_TARGET="/mnt/omar/vmwares/kvm/single/UCS/"

tmp="$(mktemp -d)"
cleanup () {
	rm -rf "$tmp"
}
trap cleanup EXIT

name="$(guestfish add-ro "$TEMPLATE_SRC" : run : mount /dev/vg_ucs/root / : command "sh -c 'echo -n @%@version/version@%@-@%@version/patchlevel@%@+e@%@version/erratalevel@%@_generic-unsafe|ucr filter'")"
case "$name" in
[1-9].[0-9]-[0-9]*+e[0-9]*_generic-unsafe) ;;
*) die "Invalid name: '$name'" ;;
esac
archive="${name}_amd64.tar.gz"
hd="${name}-0.qcow2"
xml="${name}.xml"

[ -e "$TEMPLATE_TARGET/$archive" ] &&
	die "template already exists, aborting ..."

install -m 0644 "$TEMPLATE_SRC" "$tmp/$hd"
guestfish add "$tmp/$hd" : run : mount /dev/vg_ucs/root / : command "/usr/sbin/ucr set repository/online/server=updates.knut.univention.de nameserver1=192.168.0.124 nameserver2=192.168.0.97" : command "usermod -p '$(mkpasswd -H sha-512 univention)' root"

# create xml
cat <<__XML__ >"$tmp/${xml}"
<?xml version="1.0" ?><domain type="kvm">
  <name>${name}</name>
  <memory unit="GiB">2</memory>
  <vcpu placement="static">1</vcpu>
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
      <driver cache="unsafe" name="qemu" type="qcow2" discard="unmap"/>
      <source file="${hd}"/>
      <target bus="virtio" dev="vda"/>
    </disk>
    <controller index="0" type="ide"/>
    <interface type="bridge">
      <source bridge="eth0"/>
      <model type="virtio"/>
    </interface>
    <input bus="usb" type="tablet"/>
    <input bus="ps2" type="mouse"/>
    <console type="pty"/>
    <graphics autoport="yes" keymap="de" listen="0.0.0.0" port="-1" type="vnc"/>
    <video>
      <model heads="1" primary="yes" type="vga" vram="9216"/>
    </video>
    <channel type="unix">
      <source mode="bind"/>
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    <rng model="virtio">
      <backend model="random">/dev/urandom</backend>
    </rng>
    <memballoon model="virtio"/>
  </devices>
</domain>
__XML__

tar -c -v -z -f "$tmp/$archive" --remove-files -C "$tmp" "$xml" "$hd"
install -m 0444 "$tmp/$archive" "$TEMPLATE_TARGET/$archive"
