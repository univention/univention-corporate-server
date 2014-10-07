#!/bin/bash
set -e

URL="qemu://$(hostname -f)/system"
NAME="test$RANDOM"
IMAGE="/var/lib/libvirt/images/${NAME}.img"

domain () {
	local name="${1}"
	local image="${2:-${IMAGE}}"
	cat <<EOF
<domain type="qemu">
  <name>${name}</name>
  <memory>4096</memory>
  <os>
    <type>hvm</type>
    <boot dev="cdrom"/>
    <boot dev="hd"/>
  </os>
  <features>
        <acpi/>
        <apic/>
        <pae/>
  </features>
  <devices>
    <disk device="disk" type="file">
      <driver name="file"/>
      <source file="${image}"/>
      <target bus="ide" dev="hda"/>
    </disk>
    <disk device="cdrom" type="file">
      <driver name="file"/>
      <source file="/var/lib/libvirt/images/fdfullcd.iso"/>
      <target bus="ide" dev="hdc"/>
    </disk>
    <graphics autoport="yes" keymap="en-us" port="-1" type="vnc" listen="0.0.0.0"/>
  </devices>
</domain>
EOF
}

domain "${NAME}1" "${IMAGE}" | uvmm define "${URL}" /dev/stdin | tee data
uuid1="$(sed -ne "s/ data: //p" data)"
test -f "${IMAGE}"

domain "${NAME}2" "${IMAGE}" | uvmm define "${URL}" /dev/stdin | tee data
uuid2="$(sed -ne "s/ data: //p" data)"
test -f "${IMAGE}"

uvmm undefine "${URL}" "${uuid1}" "${IMAGE}"
test ! -f "${IMAGE}"

uvmm undefine "${URL}" "${uuid2}" "${IMAGE}"
test ! -f "${IMAGE}"


IMAGE="/tmp/${NAME}.img"
domain "${NAME}3" "${IMAGE}" | uvmm define "${URL}" /dev/stdin | tee data
uuid3="$(sed -ne "s/ data: //p" data)"
test ! -f "${IMAGE}"

uvmm undefine "${URL}" "${uuid3}" "${IMAGE}"
test ! -f "${IMAGE}"

exit 0
