#!/bin/bash

set -e -u -x

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}

KVM_USER="${KVM_USER:=$USER}"
test "$KVM_USER" = "jenkins" && KVM_USER="build"
export KVM_USER

[ -n "${UCS_VERSION}" ] || die "ERR: missing UCS_VERSION env variable!"
[ -n "${KVM_BUILD_SERVER}" ] || "ERR: missing KVM_BUILD_SERVER env variable!"


mssh () {
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -n -l "$KVM_USER" "$KVM_BUILD_SERVER" "$@"
}


mssh '
set -e -u -x


TEMPLATE_SRC="/mnt/omar/vmwares/kvm/ucs-appliance/UCS-'"$UCS_VERSION"'-KVM-Image.qcow2"
TEMPLATE_BUILD="/var/univention/buildsystem2/temp/build-kt-get-template"
TEMPLATE_TARGET="/mnt/omar/vmwares/kvm/single/UCS/"

install -m 2775 -g buildgroup -d "$TEMPLATE_BUILD"

rm -f "$TEMPLATE_BUILD"/*_generic-unsafe.xml
rm -f "$TEMPLATE_BUILD"/*_generic-unsafe-0.qcow2
rm -f "$TEMPLATE_BUILD"/*_amd64.tar.gz

cp "$TEMPLATE_SRC" "$TEMPLATE_BUILD/image.qcow2"

ver="$(guestfish --ro -a "$TEMPLATE_BUILD/image.qcow2" -m /dev/vg_ucs/root -- sh "echo \"@%@version/version@%@-@%@version/patchlevel@%@+e@%@version/erratalevel@%@\"|ucr filter")"
name="${ver}_generic-unsafe"
archive="${name}_amd64.tar.gz"
hd="${name}-0.qcow2"
xml="${name}.xml"

if [ -e "$TEMPLATE_TARGET/$archive" ]; then
	echo "template already exists, aborting ..."
	rm "$TEMPLATE_BUILD/image.qcow2"
	exit 1
fi

guestfish --rw -a "$TEMPLATE_BUILD/image.qcow2" -m /dev/vg_ucs/root -- command "/usr/sbin/ucr set repository/online/server=updates.knut.univention.de nameserver1=192.168.0.3" : command "usermod -p $(mkpasswd -H sha-512 univention) root"
mv "$TEMPLATE_BUILD/image.qcow2" "$TEMPLATE_BUILD/$hd"

# create xml
cat << EOF > "$TEMPLATE_BUILD/${xml}"
<?xml version="1.0"?>
<domain type="kvm">
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
  <cpu mode="host-model"/>
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
    <interface type="bridge">
      <source bridge="eth0"/>
      <model type="virtio"/>
    </interface>
    <input bus="usb" type="tablet"/>
    <input bus="ps2" type="mouse"/>
    <input bus="ps2" type="keyboard"/>
    <console type="pty"/>
    <channel type="unix">
      <source mode="bind"/>
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    <graphics autoport="yes" keymap="de" listen="0.0.0.0" port="-1" type="vnc"/>
    <video>
      <model heads="1" primary="yes" type="virtio" vram="16384"/>
    </video>
    <watchdog model="i6300esb" action="reset"/>
    <memballoon model="virtio"/>
    <rng model="virtio">
      <backend model="random">/dev/urandom</backend>
    </rng>
  </devices>
</domain>
EOF

# build template and clean up
tar -c -v -z -f "$TEMPLATE_BUILD/$archive" -C "$TEMPLATE_BUILD" "$hd" "$xml"
mv "$TEMPLATE_BUILD/$archive" "$TEMPLATE_TARGET/$archive"
rm -f "$TEMPLATE_BUILD/$hd"
rm -f "$TEMPLATE_BUILD/$xml"

exit 0'

exit  0
